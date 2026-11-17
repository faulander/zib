import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { createServer } from 'node:http';
import { join } from 'node:path';

// The DB module reads DATABASE_PATH on import; this file runs in its own test process.
const dir = mkdtempSync(join(tmpdir(), 'zib-embedding-test-'));
process.env.DATABASE_PATH = join(dir, 'rss.db');
const { getDb } = await import('../src/lib/server/db.ts');
const { processNewEmbeddings } = await import('../src/lib/server/embedding-job.ts');

test('failed embeddings do not reprocess the same pending articles indefinitely', { timeout: 3000 }, async () => {
  const db = getDb();
  db.prepare('INSERT INTO feeds (title, feed_url) VALUES (?, ?)').run('Test', 'https://example.invalid/rss');
  db.prepare('INSERT INTO articles (feed_id, guid, title) VALUES (1, ?, ?)').run('two', 'Another article');
  db.prepare('INSERT INTO articles (feed_id, guid, title) VALUES (1, ?, ?)').run('three', 'Third article');
  db.prepare('INSERT INTO articles (feed_id, guid, title) VALUES (1, ?, ?)').run('one', 'Test article');

  let requests = 0;
  const provider = createServer((_request, response) => {
    requests++;
    response.writeHead(404).end('model not found');
  });
  const { promise, resolve } = Promise.withResolvers();
  provider.listen({ port: 0, host: '127.0.0.1' }, () => resolve(undefined));
  await promise;
  const address = provider.address();
  if (!address || typeof address === 'string') throw new Error('Test server has no port');

  try {
    const setting = db.prepare('INSERT INTO settings (key, value) VALUES (?, ?)');
    setting.run('embeddingProvider', 'ollama');
    setting.run('embeddingModel', 'missing-model');
    setting.run('embeddingApiUrl', `http://127.0.0.1:${address.port}`);

    assert.deepEqual(await processNewEmbeddings(), { processed: 0, failed: 1 });
    assert.equal(requests, 1);
  } finally {
    provider.close();
    db.close();
    rmSync(dir, { recursive: true, force: true });
  }
});
