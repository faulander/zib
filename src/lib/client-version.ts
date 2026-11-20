/**
 * Marks requests from the current client bundle. The server rejects bulk/implicit
 * "mark read" writes without it, which stops stale tabs running an old (buggy)
 * auto-mark observer from marking articles read.
 */
export const CLIENT_HEADER = 'X-ZiB-Client';
export const CLIENT_VERSION = '2';

/** Spread into fetch headers on every request that sets articles read. */
export const READ_WRITE_HEADERS = {
  'Content-Type': 'application/json',
  [CLIENT_HEADER]: CLIENT_VERSION
};
