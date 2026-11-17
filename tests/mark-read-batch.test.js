import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const dir = mkdtempSync(join(tmpdir(), 'zib-mark-read-test-'));
process.env.DATABASE_PATH = join(dir, 'rss.db');
const { getDb } = await import('../src/lib/server/db.ts');
const { markArticleIdsRead } = await import('../src/lib/server/articles.ts');

test('batch read updates only requested unread articles', () => {
  const db = getDb();
  try {
    db.prepare('INSERT INTO feeds (title, feed_url) VALUES (?, ?)').run('Test', 'https://example.invalid/rss');
    const insert = db.prepare('INSERT INTO articles (feed_id, guid, title) VALUES (1, ?, ?)');
    for (const id of [1, 2, 3]) insert.run(String(id), `Article ${id}`);

    assert.equal(markArticleIdsRead([1, 3]), 2);
    assert.deepEqual(db.query('SELECT id FROM articles WHERE is_read = 0 ORDER BY id').all(), [{ id: 2 }]);
    assert.equal(markArticleIdsRead([1, 3]), 0);
    assert.deepEqual(db.query('SELECT id FROM articles WHERE is_read = 0 ORDER BY id').all(), [{ id: 2 }]);
  } finally {
    db.close();
    rmSync(dir, { recursive: true, force: true });
  }
});
