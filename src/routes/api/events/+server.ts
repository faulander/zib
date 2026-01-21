import type { RequestHandler } from './$types';
import { serverEvents, EVENTS } from '$lib/server/events';

// Store connected clients
const clients = new Set<ReadableStreamDefaultController>();

function notifyClients(event: string, data?: unknown) {
  const message = `event: ${event}\ndata: ${JSON.stringify(data ?? {})}\n\n`;
  for (const controller of clients) {
    try {
      controller.enqueue(new TextEncoder().encode(message));
    } catch {
      // Client disconnected, remove from set
      clients.delete(controller);
    }
  }
}

// Listen to server events and forward to clients
serverEvents.on(EVENTS.FEEDS_REFRESHED, (data) => {
  notifyClients('feeds-refreshed', data);
});

serverEvents.on(EVENTS.ARTICLES_UPDATED, (data) => {
  notifyClients('articles-updated', data);
});

export const GET: RequestHandler = async () => {
  const stream = new ReadableStream({
    start(controller) {
      clients.add(controller);

      // Send initial connection message
      controller.enqueue(new TextEncoder().encode('event: connected\ndata: {}\n\n'));
    },
    cancel() {
      // Will be cleaned up on next notifyClients call
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive'
    }
  });
};
