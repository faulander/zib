import { appStore } from '$lib/stores/app.svelte';

// Track articles that have been marked as read in this session
const markedIds = new Set<number>();

// Batch API calls to avoid overwhelming the server
let pendingMarkRead: number[] = [];
let flushTimeout: ReturnType<typeof setTimeout> | null = null;

async function flushPendingMarkRead() {
	if (pendingMarkRead.length === 0) return;

	const idsToMark = [...pendingMarkRead];
	pendingMarkRead = [];

	// Mark each article as read
	for (const id of idsToMark) {
		try {
			await fetch(`/api/articles/${id}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ is_read: true })
			});
			appStore.updateArticleInList(id, { is_read: true });
		} catch (err) {
			console.error('Failed to mark article as read:', err);
		}
	}

	// Refresh counts once after batch
	if (idsToMark.length > 0) {
		window.dispatchEvent(new CustomEvent('reload-counts'));
	}
}

function scheduleFlush() {
	if (flushTimeout) return;
	flushTimeout = setTimeout(() => {
		flushTimeout = null;
		flushPendingMarkRead();
	}, 500); // 500ms debounce
}

export function queueMarkAsRead(articleId: number) {
	if (markedIds.has(articleId)) return;
	markedIds.add(articleId);
	pendingMarkRead.push(articleId);
	scheduleFlush();
}

export function resetMarkedIds() {
	markedIds.clear();
}

export function createAutoMarkReadObserver(
	scrollContainer: HTMLElement
): IntersectionObserver {
	return new IntersectionObserver(
		(entries) => {
			if (!appStore.autoMarkAsRead) return;

			for (const entry of entries) {
				// Article is leaving viewport
				if (!entry.isIntersecting) {
					const articleEl = entry.target as HTMLElement;
					const articleId = parseInt(articleEl.dataset.articleId || '0', 10);
					const isRead = articleEl.dataset.isRead === 'true';

					// Only mark if scrolling UP (article left from TOP)
					// boundingClientRect.top < 0 means element is above viewport
					if (articleId && !isRead && entry.boundingClientRect.top < 0) {
						queueMarkAsRead(articleId);
					}
				}
			}
		},
		{
			root: scrollContainer,
			rootMargin: '0px',
			threshold: 0
		}
	);
}
