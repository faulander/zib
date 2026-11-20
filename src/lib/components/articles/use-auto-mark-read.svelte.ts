import { appStore } from '$lib/stores/app.svelte';
import { READ_WRITE_HEADERS } from '$lib/client-version';

// Track articles that have been marked as read in this session
const markedIds = new Set<number>();

// Track articles that have been seen (were visible in viewport)
const seenIds = new Set<number>();

// Observations belong to an observer. A replacement observer must re-observe
// surviving row elements after a filter change or auto-mark toggle.
const observedElements = new WeakMap<IntersectionObserver, WeakSet<Element>>();

// Batch API calls to avoid overwhelming the server
let pendingMarkRead: number[] = [];
let flushTimeout: ReturnType<typeof setTimeout> | null = null;
const MAX_BATCH_SIZE = 1000;

async function flushPendingMarkRead() {
  if (pendingMarkRead.length === 0) return;

  const idsToMark = pendingMarkRead.splice(0, MAX_BATCH_SIZE);
  if (pendingMarkRead.length > 0) scheduleFlush();

  try {
    const response = await fetch('/api/mark-read', {
      method: 'POST',
      headers: READ_WRITE_HEADERS,
      body: JSON.stringify({ ids: idsToMark })
    });
    if (!response.ok) throw new Error(`Mark read failed: ${response.status}`);

    const marked = new Set(idsToMark);
    appStore.setArticles(appStore.articles.map((article) => {
      const unreadSimilar = article.similar_unread_ids;
      const groupChanged = unreadSimilar?.some((id) => marked.has(id));
      const mainChanged = marked.has(article.id);
      if (!mainChanged && !groupChanged) return article;
      if (!groupChanged) return { ...article, is_read: true };
      return {
        ...article,
        is_read: mainChanged || article.is_read,
        similar_unread_ids: unreadSimilar!.filter((id) => !marked.has(id))
      };
    }));
    window.dispatchEvent(new CustomEvent('reload-counts'));
  } catch (err) {
    console.error('Failed to mark articles as read:', err);
    for (const id of idsToMark) markedIds.delete(id);
  }
}

function scheduleFlush() {
  if (flushTimeout) return;
  flushTimeout = setTimeout(() => {
    flushTimeout = null;
    flushPendingMarkRead();
  }, 500); // 500ms debounce
}

function queueId(id: number) {
  if (markedIds.has(id)) return;
  markedIds.add(id);
  pendingMarkRead.push(id);
  scheduleFlush();
}

export function queueMarkAsRead(articleId: number) {
  // A grouped row stands for all its hidden articles. They leave the viewport
  // together, so mark unread group members with the visible representative.
  const group = appStore.articles.find((article) => article.id === articleId);
  if (!group?.is_read) queueId(articleId);
  for (const id of group?.similar_unread_ids ?? []) queueId(id);
}

export function resetMarkedIds() {
  markedIds.clear();
  seenIds.clear();
}

export function observeArticles(observer: IntersectionObserver, scrollContainer: HTMLElement) {
  const articleElements = scrollContainer.querySelectorAll('[data-article-id]');
  const rootBounds = scrollContainer.getBoundingClientRect();
  let elements = observedElements.get(observer);
  if (!elements) {
    elements = new WeakSet<Element>();
    observedElements.set(observer, elements);
  }

  articleElements.forEach((el) => {
    const htmlEl = el as HTMLElement;
    const articleId = parseInt(htmlEl.dataset.articleId || '0', 10);
    if (!articleId) return;

    // Skip hidden elements (e.g., desktop layout when on mobile, or vice versa)
    // Check if element has actual dimensions
    if (htmlEl.offsetWidth === 0 && htmlEl.offsetHeight === 0) return;
    const bounds = htmlEl.getBoundingClientRect();
    if (bounds.bottom > rootBounds.top && bounds.top < rootBounds.bottom) {
      seenIds.add(articleId);
    }

    // Skip elements already being observed
    if (elements.has(el)) return;

    elements.add(el);
    observer.observe(el);
  });
}

export function createAutoMarkReadObserver(scrollContainer: HTMLElement): IntersectionObserver {
  const observer: IntersectionObserver = new IntersectionObserver(
    (entries) => {
      if (!appStore.autoMarkAsRead) return;

      for (const entry of entries) {
        const articleEl = entry.target as HTMLElement;
        const articleId = parseInt(articleEl.dataset.articleId || '0', 10);
        if (!articleId) continue;

        // Entries for rows removed from the DOM (list replacement, loading
        // spinner, hide-read filtering) report non-intersecting with an all-zero
        // rect. They were never scrolled past: forget them, never mark them.
        if (!articleEl.isConnected) {
          observer.unobserve(articleEl);
          seenIds.delete(articleId);
          continue;
        }

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

          // Zero geometry means a hidden/detached element, not a scroll exit.
          const rect = entry.boundingClientRect;
          if (rect.width === 0 && rect.height === 0) continue;

          const leftFromTop = rect.bottom <= rootBounds.top;

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
  return observer;
}
