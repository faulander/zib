import type { RequestHandler } from './$types';
import { getAllLogsForExport } from '$lib/server/logger';

export const GET: RequestHandler = async () => {
  const logs = getAllLogsForExport();

  // Format as readable text log
  const logText = logs
    .map((log) => {
      const timestamp = new Date(log.created_at).toISOString();
      const details = log.details ? ` | ${log.details}` : '';
      return `[${timestamp}] [${log.level.toUpperCase()}] [${log.category}] ${log.message}${details}`;
    })
    .join('\n');

  const filename = `zib-logs-${new Date().toISOString().split('T')[0]}.txt`;

  return new Response(logText, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Content-Disposition': `attachment; filename="${filename}"`
    }
  });
};
