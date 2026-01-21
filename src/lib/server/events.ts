import { EventEmitter } from 'events';

// Shared event emitter for server-side events
export const serverEvents = new EventEmitter();

// Event types
export const EVENTS = {
  FEEDS_REFRESHED: 'feeds-refreshed',
  ARTICLES_UPDATED: 'articles-updated'
} as const;
