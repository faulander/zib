import { appStore } from '$lib/stores/app.svelte';

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

async function flushPendingMarkRead() {
  if (pendingMarkRead.length === 0) return;

  const idsToMark = [...pendingMarkRead];
  pendingMarkRead = [];

  // Mark each article as read
  for (const id of idsToMark) {
    try {
      const response = await fetch(`/api/articles/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: true })
      });
      if (!response.ok) throw new Error(`Mark read failed: ${response.status}`);
      appStore.updateArticleInList(id, { is_read: true });
    } catch (err) {
      console.error('Failed to mark article as read:', err);
      markedIds.delete(id);
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

export function getVisibleUnreadArticleIds(scrollContainer: HTMLElement): number[] {
  const rootBounds = scrollContainer.getBoundingClientRect();
  const articleElements = scrollContainer.querySelectorAll<HTMLElement>('[data-article-id]');
  const visibleIds: number[] = [];

  for (const articleEl of articleElements) {
    const articleId = parseInt(articleEl.dataset.articleId || '0', 10);
    if (!articleId || articleEl.dataset.isRead === 'true') continue;

    const articleBounds = articleEl.getBoundingClientRect();
    const isVisible =
      articleBounds.bottom > rootBounds.top && articleBounds.top < rootBounds.bottom;

    if (isVisible) {
      visibleIds.push(articleId);
    }
  }

  return visibleIds;
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
  return new IntersectionObserver(
    (entries) => {
      if (!appStore.autoMarkAsRead) return;

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
