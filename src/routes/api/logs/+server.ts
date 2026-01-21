import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getLogs, getLogCount, clearLogs, type LogLevel, type LogCategory } from '$lib/server/logger';

export const GET: RequestHandler = async ({ url }) => {
  const level = url.searchParams.get('level') as LogLevel | null;
  const category = url.searchParams.get('category') as LogCategory | null;
  const limit = parseInt(url.searchParams.get('limit') || '100');
  const offset = parseInt(url.searchParams.get('offset') || '0');

  const logs = getLogs({
    level: level || undefined,
    category: category || undefined,
    limit,
    offset
  });

  const total = getLogCount({
    level: level || undefined,
    category: category || undefined
  });

  return json({
    logs,
    total,
    limit,
    offset
  });
};

export const DELETE: RequestHandler = async () => {
  clearLogs();
  return json({ success: true });
};
