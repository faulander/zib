import { getDb } from './db';

export interface FilterRow {
  id: number;
  name: string;
  rule: string;
  is_enabled: number;
  created_at: string;
}

export interface Filter {
  id: number;
  name: string;
  rule: string;
  is_enabled: boolean;
  created_at: string;
}

export interface CreateFilter {
  name: string;
  rule: string;
  is_enabled?: boolean;
}

export interface UpdateFilter {
  name?: string;
  rule?: string;
  is_enabled?: boolean;
}

function rowToFilter(row: FilterRow): Filter {
  return {
    ...row,
    is_enabled: row.is_enabled === 1
  };
}

export function getAllFilters(): Filter[] {
  const db = getDb();
  const rows = db.prepare('SELECT * FROM filters ORDER BY name').all() as FilterRow[];
  return rows.map(rowToFilter);
}

export function getEnabledFilters(): Filter[] {
  const db = getDb();
  const rows = db
    .prepare('SELECT * FROM filters WHERE is_enabled = 1 ORDER BY name')
    .all() as FilterRow[];
  return rows.map(rowToFilter);
}

export function getFilterById(id: number): Filter | null {
  const db = getDb();
  const row = db.prepare('SELECT * FROM filters WHERE id = ?').get(id) as FilterRow | undefined;
  return row ? rowToFilter(row) : null;
}

export function createFilter(data: CreateFilter): Filter {
  const db = getDb();
  const result = db
    .prepare('INSERT INTO filters (name, rule, is_enabled) VALUES (?, ?, ?)')
    .run(data.name, data.rule, data.is_enabled !== false ? 1 : 0);

  return getFilterById(result.lastInsertRowid as number)!;
}

export function updateFilter(id: number, data: UpdateFilter): Filter | null {
  const db = getDb();
  const existing = getFilterById(id);

  if (!existing) {
    return null;
  }

  const updates: string[] = [];
  const values: (string | number)[] = [];

  if (data.name !== undefined) {
    updates.push('name = ?');
    values.push(data.name);
  }

  if (data.rule !== undefined) {
    updates.push('rule = ?');
    values.push(data.rule);
  }

  if (data.is_enabled !== undefined) {
    updates.push('is_enabled = ?');
    values.push(data.is_enabled ? 1 : 0);
  }

  if (updates.length > 0) {
    values.push(id);
    db.prepare(`UPDATE filters SET ${updates.join(', ')} WHERE id = ?`).run(...values);
  }

  return getFilterById(id);
}

export function deleteFilter(id: number): boolean {
  const db = getDb();
  const result = db.prepare('DELETE FROM filters WHERE id = ?').run(id);
  return result.changes > 0;
}

/**
 * Parse a filter rule and check if text matches it.
 *
 * Rule syntax:
 * - Terms in quotes: "Rapid Wien"
 * - Regex patterns: /\d+:\d+/ (always case-insensitive)
 * - OR: "Term A" OR "Term B" (match any)
 * - AND: "Term A" AND "Term B" (match all)
 * - Parentheses for grouping: ("A" OR "B") AND "C"
 *
 * Case-insensitive matching.
 */
export function matchesRule(text: string, rule: string): boolean {
  if (!text || !rule) return false;

  const lowerText = text.toLowerCase();

  try {
    // Parse the rule into tokens
    const tokens = tokenizeRule(rule);
    // Evaluate the expression
    return evaluateExpression(tokens, lowerText);
  } catch {
    // If parsing fails, do simple contains check for the whole rule
    return lowerText.includes(rule.toLowerCase());
  }
}

type Token =
  | { type: 'term'; value: string }
  | { type: 'regex'; pattern: RegExp }
  | { type: 'and' }
  | { type: 'or' }
  | { type: 'lparen' }
  | { type: 'rparen' };

function tokenizeRule(rule: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;

  while (i < rule.length) {
    // Skip whitespace
    if (/\s/.test(rule[i])) {
      i++;
      continue;
    }

    // Quoted term
    if (rule[i] === '"') {
      const start = i + 1;
      i++;
      while (i < rule.length && rule[i] !== '"') {
        i++;
      }
      tokens.push({ type: 'term', value: rule.slice(start, i).toLowerCase() });
      i++; // skip closing quote
      continue;
    }

    // Parentheses
    if (rule[i] === '(') {
      tokens.push({ type: 'lparen' });
      i++;
      continue;
    }
    if (rule[i] === ')') {
      tokens.push({ type: 'rparen' });
      i++;
      continue;
    }

    // Regex term: /pattern/flags
    if (rule[i] === '/') {
      const start = i + 1;
      i++;
      while (i < rule.length && rule[i] !== '/') {
        if (rule[i] === '\\') i++; // skip escaped chars
        i++;
      }
      const pattern = rule.slice(start, i);
      i++; // skip closing /
      let flags = '';
      while (i < rule.length && /[gimsuy]/.test(rule[i])) {
        flags += rule[i];
        i++;
      }
      if (!flags.includes('i')) flags += 'i';
      try {
        tokens.push({ type: 'regex', pattern: new RegExp(pattern, flags) });
      } catch {
        // Invalid regex — treat as literal term
        tokens.push({ type: 'term', value: pattern.toLowerCase() });
      }
      continue;
    }

    // AND/OR keywords
    const rest = rule.slice(i).toUpperCase();
    if (rest.startsWith('AND') && (i + 3 >= rule.length || /[\s("]/.test(rule[i + 3]))) {
      tokens.push({ type: 'and' });
      i += 3;
      continue;
    }
    if (rest.startsWith('OR') && (i + 2 >= rule.length || /[\s("]/.test(rule[i + 2]))) {
      tokens.push({ type: 'or' });
      i += 2;
      continue;
    }

    // Unquoted term (read until whitespace or special char)
    const start = i;
    while (i < rule.length && !/[\s()"']/.test(rule[i])) {
      i++;
    }
    if (i > start) {
      const word = rule.slice(start, i);
      if (word.toUpperCase() !== 'AND' && word.toUpperCase() !== 'OR') {
        tokens.push({ type: 'term', value: word.toLowerCase() });
      }
    }
  }

  return tokens;
}

function evaluateExpression(tokens: Token[], text: string): boolean {
  let pos = 0;

  function parseOr(): boolean {
    let result = parseAnd();

    while (pos < tokens.length && tokens[pos].type === 'or') {
      pos++; // consume OR
      const right = parseAnd();
      result = result || right;
    }

    return result;
  }

  function parseAnd(): boolean {
    let result = parsePrimary();

    while (pos < tokens.length && tokens[pos].type === 'and') {
      pos++; // consume AND
      const right = parsePrimary();
      result = result && right;
    }

    return result;
  }

  function parsePrimary(): boolean {
    if (pos >= tokens.length) return false;

    const token = tokens[pos];

    if (token.type === 'lparen') {
      pos++; // consume (
      const result = parseOr();
      if (pos < tokens.length && tokens[pos].type === 'rparen') {
        pos++; // consume )
      }
      return result;
    }

    if (token.type === 'term') {
      pos++;
      return text.includes(token.value);
    }

    if (token.type === 'regex') {
      pos++;
      return token.pattern.test(text);
    }

    return false;
  }

  return parseOr();
}

/**
 * Check if an article matches any of the enabled filters.
 */
export function articleMatchesFilters(
  article: { title: string; rss_content?: string | null; full_content?: string | null },
  filters: Filter[]
): boolean {
  if (filters.length === 0) return false;

  const searchText = [article.title, article.rss_content || '', article.full_content || ''].join(
    ' '
  );

  for (const filter of filters) {
    if (filter.is_enabled && matchesRule(searchText, filter.rule)) {
      return true;
    }
  }

  return false;
}

/**
 * Count how many articles match a given rule.
 */
export function countMatchingArticles(rule: string): number {
  const db = getDb();
  const articles = db.prepare('SELECT title, rss_content, full_content FROM articles').all() as {
    title: string;
    rss_content: string | null;
    full_content: string | null;
  }[];

  let count = 0;
  for (const article of articles) {
    const searchText = [article.title, article.rss_content || '', article.full_content || ''].join(
      ' '
    );
    if (matchesRule(searchText, rule)) {
      count++;
    }
  }

  return count;
}

/**
 * Get the most recent articles matching a given rule.
 */
export function getRecentMatchingArticles(
  rule: string,
  limit: number = 10
): { id: number; title: string; feed_title: string; published_at: string | null }[] {
  const db = getDb();
  const articles = db
    .prepare(
      `
    SELECT a.id, a.title, a.rss_content, a.full_content, a.published_at,
           f.title as feed_title
    FROM articles a
    JOIN feeds f ON f.id = a.feed_id
    ORDER BY a.published_at DESC, a.id DESC
  `
    )
    .all() as {
    id: number;
    title: string;
    rss_content: string | null;
    full_content: string | null;
    published_at: string | null;
    feed_title: string;
  }[];

  const matches: { id: number; title: string; feed_title: string; published_at: string | null }[] =
    [];

  for (const article of articles) {
    if (matches.length >= limit) break;

    const searchText = [article.title, article.rss_content || '', article.full_content || ''].join(
      ' '
    );

    if (matchesRule(searchText, rule)) {
      matches.push({
        id: article.id,
        title: article.title,
        feed_title: article.feed_title,
        published_at: article.published_at
      });
    }
  }

  return matches;
}
