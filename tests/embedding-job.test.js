import { test, expect } from 'bun:test';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// The DB module reads DATABASE_PATH on import; this file runs in its own test process.
const dir = mkdtempSync(join(tmpdir(), 'zib-embedding-test-'));
process.env.DATABASE_PATH = join(dir, 'rss.db');
const { getDb } = await import('../src/lib/server/db.ts');
const { processNewEmbeddings } = await import('../src/lib/server/embedding-job.ts');

test('failed embeddings do not reprocess the same pending articles indefinitely', async () => {
  const db = getDb();
  db.prepare('INSERT INTO feeds (title, feed_url) VALUES (?, ?)').run('Test', 'https://example.invalid/rss');
  db.prepare('INSERT INTO articles (feed_id, guid, title) VALUES (1, ?, ?)').run('one', 'Test article');

  let requests = 0;
  const provider = Bun.serve({
    port: 0,
    fetch() {
      requests++;
      return new Response('model not found', { status: 404 });
    }
  });

  try {
    const setting = db.prepare('INSERT INTO settings (key, value) VALUES (?, ?)');
    setting.run('embeddingProvider', 'ollama');
    setting.run('embeddingModel', 'missing-model');
    setting.run('embeddingApiUrl', `http://127.0.0.1:${provider.port}`);

    expect(await processNewEmbeddings()).toEqual({ processed: 0, failed: 1 });
    expect(requests).toBe(1);
  } finally {
    provider.stop();
    db.close();
    rmSync(dir, { recursive: true, force: true });
  }
}, 3000);
