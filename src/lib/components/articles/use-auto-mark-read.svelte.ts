import { appStore } from '$lib/stores/app.svelte';

// Track articles that have been marked as read in this session
const markedIds = new Set<number>();

// Track articles that have been seen (were visible in viewport)
const seenIds = new Set<number>();

// Track which elements are currently being observed to avoid duplicate observations
const observedElements = new WeakSet<Element>();

// Batch API calls to avoid overwhelming the server
let pendingMarkRead: number[] = [];
let flushTimeout: ReturnType<typeof setTimeout> | null = null;

// Flag to ignore initial intersection events after observing
let ignoreEventsUntil = 0;

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
  seenIds.clear();
  // WeakSet doesn't need clearing - elements will be garbage collected
}

export function observeArticles(observer: IntersectionObserver, scrollContainer: HTMLElement) {
  const articleElements = scrollContainer.querySelectorAll('[data-article-id]');
  let newObservations = 0;

  articleElements.forEach((el) => {
    const htmlEl = el as HTMLElement;
    const articleId = parseInt(htmlEl.dataset.articleId || '0', 10);
    if (!articleId) return;

    // Skip hidden elements (e.g., desktop layout when on mobile, or vice versa)
    // Check if element has actual dimensions
    if (htmlEl.offsetWidth === 0 && htmlEl.offsetHeight === 0) return;

    // Skip elements already being observed
    if (observedElements.has(el)) return;

    observedElements.add(el);
    observer.observe(el);
    newObservations++;
  });

  // If we added new observations, ignore events briefly to skip initial callbacks
  if (newObservations > 0) {
    ignoreEventsUntil = Date.now() + 100;
  }
}

export function createAutoMarkReadObserver(scrollContainer: HTMLElement): IntersectionObserver {
  return new IntersectionObserver(
    (entries) => {
      if (!appStore.autoMarkAsRead) return;

      // Skip initial intersection events right after observing
      if (Date.now() < ignoreEventsUntil) {
        // But still mark visible articles as "seen"
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const articleId = parseInt((entry.target as HTMLElement).dataset.articleId || '0', 10);
            if (articleId) seenIds.add(articleId);
          }
        }
        return;
      }

      for (const entry of entries) {
        const articleEl = entry.target as HTMLElement;
        const articleId = parseInt(articleEl.dataset.articleId || '0', 10);
        if (!articleId) continue;

        if (entry.isIntersecting) {
          // Article entered viewport - mark it as seen
          seenIds.add(articleId);
        } else {
          // Article left viewport - only mark as read if it was seen before
          const isRead = articleEl.dataset.isRead === 'true';
          const wasSeen = seenIds.has(articleId);
          const rootBounds = entry.rootBounds;

          // Check that we have valid bounds and article left from TOP
          if (!rootBounds || rootBounds.height === 0) continue;

          const leftFromTop = entry.boundingClientRect.bottom <= rootBounds.top;

          // Only mark if:
          // 1. Article was previously visible (seen)
          // 2. Article is not already read
          // 3. Article left from TOP (scrolled up past it)
          if (wasSeen && !isRead && leftFromTop) {
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
