import { getDb } from './db';
import { getSetting, isEmbeddingConfigured } from './settings';
import { generateEmbedding, embeddingToBlob } from './embedding-provider';
import { logger } from './logger';

interface ArticleToEmbed {
  id: number;
  title: string;
}

let isEmbedding = false;

const batchSize = 50;
const yieldToRequests = () => {
  const { promise, resolve } = Promise.withResolvers<void>();
  setTimeout(resolve, 0);
  return promise;
};

interface EmbeddingStats {
  total: number;
  embedded: number;
  pending: number;
  model: string | null;
}

let cachedStats: EmbeddingStats | null = null;
let cachedAt = 0;
let statsInFlight: Promise<EmbeddingStats> | null = null;

/**
 * Check if an embedding job is currently running.
 */
export function isEmbeddingInProgress(): boolean {
  return isEmbedding;
}

/**
 * Process new articles that don't have embeddings yet.
 * Called after feed refresh or on a schedule.
 */
export async function processNewEmbeddings(): Promise<{ processed: number; failed: number }> {
  if (isEmbedding) {
    logger.info('embedding', 'Embedding job already in progress, skipping');
    return { processed: 0, failed: 0 };
  }

  if (!isEmbeddingConfigured()) {
    return { processed: 0, failed: 0 };
  }

  isEmbedding = true;
  let processed = 0;
  let failed = 0;

  try {
    const db = getDb();
    const provider = getSetting('embeddingProvider');
    const rateLimit = getSetting('embeddingRateLimit');
    const isRateLimited = provider === 'openai' || provider === 'openai-compatible';
    const delayMs = isRateLimited ? Math.ceil(60000 / rateLimit) : 0;

    // IDs increase with insertion time. Articles predating the first
    // embedding are only backfilled when unread; newer articles are all
    // eligible, even if they have since been read.
    const firstEmbedding = db.prepare(
      'SELECT MIN(article_id) as id FROM article_embeddings'
    ).get() as { id: number | null };
    const firstEmbeddedId = firstEmbedding.id;
    const recent = db.prepare(`
      SELECT id, title FROM articles
      WHERE id >= ? AND id <= ? AND id < ?
      ORDER BY id DESC LIMIT ?
    `);
    const unread = db.prepare(`
      SELECT id, title FROM articles INDEXED BY idx_articles_is_read
      WHERE is_read = 0 AND id < ? AND id < ?
      ORDER BY id DESC LIMIT ?
    `);
    const embedded = db.prepare(`
      SELECT article_id FROM article_embeddings
      WHERE article_id IN (SELECT value FROM json_each(?))
    `);
    const insert = db.prepare(`
      INSERT OR REPLACE INTO article_embeddings (article_id, embedding, model, dimensions)
      VALUES (?, ?, ?, ?)
    `);

    // Page over *candidate* IDs, not all missing embeddings: an unbounded
    // anti-join can monopolize Bun's request thread on large libraries.
    // Each slice scans at most 50 article rows and yields even when all are
    // already embedded. Catch articles inserted during the pass afterward.
    const latestArticle = db.prepare('SELECT MAX(id) as id FROM articles');
    const initialLatest = latestArticle.get() as { id: number | null };
    let newestId = initialLatest.id ?? 0;
    while (true) {
      for (const phase of ['recent', 'unread'] as const) {
        if (phase === 'recent' && firstEmbeddedId === null) continue;
        let cursor = newestId + 1;
        while (true) {
          const candidates = phase === 'recent'
            ? recent.all(firstEmbeddedId, newestId, cursor, batchSize) as ArticleToEmbed[]
            : unread.all(firstEmbeddedId ?? newestId + 1, cursor, batchSize) as ArticleToEmbed[];
          if (candidates.length === 0) break;
          cursor = candidates[candidates.length - 1].id;
          const embeddedIds = new Set(
            (embedded.all(JSON.stringify(candidates.map((article) => article.id))) as { article_id: number }[])
              .map((row) => row.article_id)
          );

          for (const article of candidates) {
            if (embeddedIds.has(article.id)) continue;
            try {
              const result = await generateEmbedding(article.title);
              if (!result) {
                failed++;
                break;
              }

              const blob = embeddingToBlob(result.embedding);
              insert.run(article.id, blob, result.model, result.dimensions);
              processed++;

              if (isRateLimited && delayMs > 0) {
                const { promise, resolve } = Promise.withResolvers<void>();
                setTimeout(resolve, delayMs);
                await promise;
              }
            } catch (err) {
              const msg = err instanceof Error ? err.message : String(err);
              logger.error('embedding', `Failed to embed article ${article.id}: ${msg}`);
              failed++;
              break;
            }
          }

          if (failed > 0) break; // Retry a broken provider on the next job, not in a tight loop.
          await yieldToRequests();
        }
        if (failed > 0) break;
      }
      if (failed > 0) break;
      const latestRow = latestArticle.get() as { id: number | null };
      const latest = latestRow.id ?? 0;
      if (latest <= newestId) break;
      newestId = latest;
    }

    if (processed > 0 || failed > 0) {
      logger.info('embedding', `Embedding complete: ${processed} processed, ${failed} failed`);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    logger.error('embedding', `Embedding job failed: ${msg}`);
  } finally {
    isEmbedding = false;
    cachedStats = null;
  }

  return { processed, failed };
}

/**
 * Get the count of articles with and without embeddings.
 * `pending` = articles that still need embedding in the current job scope.
 */
async function scanEmbeddingStats(): Promise<EmbeddingStats> {
  const db = getDb();
  const firstEmbedding = db.prepare(
    'SELECT MIN(article_id) as id FROM article_embeddings'
  ).get() as { id: number | null };
  const modelRow = db.prepare('SELECT model FROM article_embeddings LIMIT 1').get() as { model: string } | undefined;
  const articles = db.prepare(
    'SELECT id, is_read FROM articles WHERE id > ? ORDER BY id LIMIT ?'
  );
  const existing = db.prepare(`
    SELECT article_id FROM article_embeddings
    WHERE article_id IN (SELECT value FROM json_each(?))
  `);

  let total = 0;
  let embedded = 0;
  let pending = 0;
  let cursor = 0;
  while (true) {
    const rows = articles.all(cursor, 500) as { id: number; is_read: number }[];
    if (rows.length === 0) break;
    cursor = rows[rows.length - 1].id;
    const existingIds = new Set(
      (existing.all(JSON.stringify(rows.map((row) => row.id))) as { article_id: number }[])
        .map((row) => row.article_id)
    );
    total += rows.length;
    embedded += existingIds.size;
    for (const row of rows) {
      const eligible = row.is_read === 0 ||
        (firstEmbedding.id !== null && row.id >= firstEmbedding.id);
      if (eligible && !existingIds.has(row.id)) pending++;
    }
    // The settings page polls this endpoint; never block reader requests with
    // full-table COUNTs or a full-library pending anti-join.
    await yieldToRequests();
  }
  return { total, embedded, pending, model: modelRow?.model ?? null };
}

export async function getEmbeddingStats(): Promise<EmbeddingStats> {
  if (statsInFlight) return statsInFlight;
  if (!isEmbedding && cachedStats && Date.now() - cachedAt < 5000) return cachedStats;

  statsInFlight = scanEmbeddingStats();
  try {
    const stats = await statsInFlight;
    cachedStats = stats;
    cachedAt = Date.now();
    return stats;
  } finally {
    statsInFlight = null;
  }
}

/**
 * Purge all embeddings (used when changing embedding model).
 */
export function purgeAllEmbeddings(): number {
  const db = getDb();
  const result = db.prepare('DELETE FROM article_embeddings').run();
  cachedStats = null;
  logger.info('embedding', `Purged ${result.changes} embeddings`);
  return result.changes;
}
