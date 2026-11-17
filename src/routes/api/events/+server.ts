import type { RequestHandler } from './$types';
import { serverEvents, EVENTS } from '$lib/server/events';

const encoder = new TextEncoder();
const heartbeatMessage = encoder.encode(': heartbeat\n\n');
const connectedMessage = encoder.encode('event: connected\ndata: {}\n\n');
const HEARTBEAT_INTERVAL = 25 * 1000;
type Client = { controller: ReadableStreamDefaultController<Uint8Array>; disconnect: () => void };
const clients = new Set<Client>();

function notifyClients(event: string, data?: unknown) {
  const message = encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data ?? {})}\n\n`);
  for (const client of clients) {
    try {
      client.controller.enqueue(message);
    } catch {
      client.disconnect();
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

export const GET: RequestHandler = ({ request }) => {
  let client: Client;
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const heartbeat = setInterval(() => {
        try {
          controller.enqueue(heartbeatMessage);
        } catch {
          client.disconnect();
        }
      }, HEARTBEAT_INTERVAL);

      const disconnect = () => {
        clients.delete(client);
        clearInterval(heartbeat);
        request.signal.removeEventListener('abort', disconnect);
        try {
          controller.close();
        } catch {
          // The browser may already have canceled the stream.
        }
      };
      client = { controller, disconnect };
      clients.add(client);
      request.signal.addEventListener('abort', disconnect, { once: true });
      if (request.signal.aborted) disconnect();
      else controller.enqueue(connectedMessage);
    },
    cancel() {
      client.disconnect();
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no'
    }
  });
};
