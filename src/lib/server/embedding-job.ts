import { getDb } from './db';
import { getSetting, isEmbeddingConfigured } from './settings';
import { generateEmbedding, embeddingToBlob } from './embedding-provider';
import { logger } from './logger';

interface ArticleToEmbed {
  id: number;
  title: string;
  rss_content: string | null;
}

let isEmbedding = false;

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

    // On first run (no embeddings yet), only embed unread articles
    // to avoid processing thousands of old read articles.
    // Subsequent runs embed everything new (articles arriving after setup).
    const hasExistingEmbeddings = (db.prepare(
      'SELECT COUNT(*) as count FROM article_embeddings'
    ).get() as { count: number }).count > 0;

    const articles = db.prepare(`
      SELECT a.id, a.title, a.rss_content
      FROM articles a
      WHERE a.id NOT IN (SELECT article_id FROM article_embeddings)
      ${!hasExistingEmbeddings ? 'AND a.is_read = 0' : ''}
      ORDER BY a.created_at DESC
    `).all() as ArticleToEmbed[];

    if (articles.length === 0) {
      isEmbedding = false;
      return { processed: 0, failed: 0 };
    }

    logger.info('embedding', `Processing ${articles.length} articles for embedding`);

    for (const article of articles) {
      try {
        const text = prepareEmbeddingText(article.title, article.rss_content);
        const result = await generateEmbedding(text);

        if (result) {
          const blob = embeddingToBlob(result.embedding);
          db.prepare(`
            INSERT OR REPLACE INTO article_embeddings (article_id, embedding, model, dimensions)
            VALUES (?, ?, ?, ?)
          `).run(article.id, blob, result.model, result.dimensions);

          processed++;
        } else {
          failed++;
        }

        // Rate limiting for OpenAI
        if (isRateLimited && delayMs > 0) {
          await new Promise((resolve) => setTimeout(resolve, delayMs));
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        logger.error('embedding', `Failed to embed article ${article.id}: ${msg}`);
        failed++;
      }
    }

    if (processed > 0) {
      logger.info('embedding', `Embedding complete: ${processed} processed, ${failed} failed`);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    logger.error('embedding', `Embedding job failed: ${msg}`);
  } finally {
    isEmbedding = false;
  }

  return { processed, failed };
}

/**
 * Prepare text for embedding: title + first 200 chars of content
 */
function prepareEmbeddingText(title: string, content: string | null): string {
  let text = title;

  if (content) {
    // Strip HTML tags for cleaner embedding input
    const stripped = content.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    if (stripped.length > 0) {
      text += ' ' + stripped.substring(0, 200);
    }
  }

  return text;
}

/**
 * Get the count of articles with and without embeddings.
 */
export function getEmbeddingStats(): { total: number; embedded: number; model: string | null } {
  const db = getDb();
  const embedded = (db.prepare('SELECT COUNT(*) as count FROM article_embeddings').get() as { count: number }).count;
  const modelRow = db.prepare('SELECT model FROM article_embeddings LIMIT 1').get() as { model: string } | undefined;

  // First run only embeds unread articles. Show unread count as target
  // until all unread have been embedded, then switch to total articles.
  const unreadCount = (db.prepare('SELECT COUNT(*) as count FROM articles WHERE is_read = 0').get() as { count: number }).count;
  const allCount = (db.prepare('SELECT COUNT(*) as count FROM articles').get() as { count: number }).count;
  const total = embedded >= unreadCount ? allCount : unreadCount;

  return {
    total,
    embedded,
    model: modelRow?.model ?? null
  };
}

/**
 * Purge all embeddings (used when changing embedding model).
 */
export function purgeAllEmbeddings(): number {
  const db = getDb();
  const result = db.prepare('DELETE FROM article_embeddings').run();
  logger.info('embedding', `Purged ${result.changes} embeddings`);
  return result.changes;
}
