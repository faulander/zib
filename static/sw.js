const CACHE_NAME = 'zib-v2';
const STATIC_ASSETS = [
	'/',
	'/manifest.json'
];

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
	);
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		(async () => {
			const keys = await caches.keys();
			const stale = keys.filter((key) => key !== CACHE_NAME);
			await Promise.all(stale.map((key) => caches.delete(key)));
			await self.clients.claim();

			// A previous worker/cache existed, so open tabs may run an outdated bundle
			// (cached or already loaded). Reload them once onto the fresh build.
			if (stale.length === 0) return;
			const windows = await self.clients.matchAll({ type: 'window' });
			await Promise.all(windows.map((client) => client.navigate(client.url).catch(() => {})));
		})()
	);
});

self.addEventListener('fetch', (event) => {
	const { request } = event;
	const url = new URL(request.url);

	// Skip non-GET requests
	if (request.method !== 'GET') return;

	// Network-first for API calls and SSE
	if (url.pathname.startsWith('/api/')) return;

	// Network-first for pages: SSR output (e.g. the color theme) must be fresh.
	// Fall back to the cached copy when offline.
	if (request.mode === 'navigate') {
		event.respondWith(
			fetch(request)
				.then((response) => {
					if (response.ok) {
						const clone = response.clone();
						caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
					}
					return response;
				})
				.catch(() => caches.match(request).then((cached) => cached || Response.error()))
		);
		return;
	}

	// Cache-first for static assets, with network update
	event.respondWith(
		caches.match(request).then((cached) => {
			const fetched = fetch(request).then((response) => {
				if (response.ok) {
					const clone = response.clone();
					caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
				}
				return response;
			});
			return cached || fetched;
		})
	);
});
