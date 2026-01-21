import type { Handle, HandleServerError } from '@sveltejs/kit';
import { startScheduler, initialRefresh } from '$lib/server/scheduler';

// Start the scheduler when the server starts
let schedulerStarted = false;

export const handle: Handle = async ({ event, resolve }) => {
  // Start scheduler on first request (ensures DB is initialized)
  if (!schedulerStarted) {
    schedulerStarted = true;
    startScheduler();
    // Run initial refresh after a short delay
    setTimeout(() => initialRefresh(), 5000);
  }
  // Request timing
  const start = performance.now();

  // Example: Get user session from cookie
  // const sessionId = event.cookies.get('session');
  // if (sessionId) {
  //   const user = await getUser(sessionId);
  //   event.locals.user = user;
  // }

  const response = await resolve(event);

  // Log request (disable in production if too verbose)
  const duration = (performance.now() - start).toFixed(2);
  console.log(`${event.request.method} ${event.url.pathname} - ${response.status} (${duration}ms)`);

  return response;
};

export const handleError: HandleServerError = async ({ error, event, status, message }) => {
  // Log error details (integrate with error tracking service in production)
  console.error('Server error:', {
    status,
    message,
    path: event.url.pathname,
    error
  });

  // Return user-friendly error
  return {
    message: status === 404 ? 'Page not found' : 'An unexpected error occurred'
  };
};
