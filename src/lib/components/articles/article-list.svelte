<script lang="ts">
  import { onDestroy } from 'svelte';
  import { appStore } from '$lib/stores/app.svelte';
  import ArticleRow from './article-row.svelte';
  import ArticleCard from './article-card.svelte';
  import Spinner from '$lib/components/spinner.svelte';
  import {
    createAutoMarkReadObserver,
    getVisibleUnreadArticleIds,
    observeArticles,
    queueMarkAsRead,
    resetMarkedIds
  } from './use-auto-mark-read.svelte';

  const isEmpty = $derived(appStore.articles.length === 0 && !appStore.isLoading);

  // Find the index where highlighted articles end (for separator)
  const highlightSortActive = $derived(
    appStore.highlightMode === 'sort-first' || appStore.highlightMode === 'both'
  );
  const highlightBoundary = $derived(() => {
    if (!highlightSortActive) return -1;
    const articles = appStore.articles;
    let lastHighlighted = -1;
    for (let i = 0; i < articles.length; i++) {
      if (articles[i].is_feed_highlighted) lastHighlighted = i;
      else if (lastHighlighted >= 0) break;
    }
    // Only show separator if there are both highlighted and non-highlighted articles
    if (lastHighlighted >= 0 && lastHighlighted < articles.length - 1) {
      return lastHighlighted;
    }
    return -1;
  });

  const BOTTOM_DWELL_MS = 2000;

  let scrollContainer = $state<HTMLDivElement | null>(null);
  let observer: IntersectionObserver | null = null;
  let lastObservedArticles: typeof appStore.articles = [];
  let bottomMarkTimeout: ReturnType<typeof setTimeout> | null = null;
  let hasScrolledDown = false;
  let lastScrollTop = 0;

  function clearBottomMarkTimeout() {
    if (!bottomMarkTimeout) return;
    clearTimeout(bottomMarkTimeout);
    bottomMarkTimeout = null;
  }

  function scheduleBottomMark() {
    clearBottomMarkTimeout();
    const container = scrollContainer;
    if (!container) return;
    const visibleArticleIds = getVisibleUnreadArticleIds(container);
    if (visibleArticleIds.length === 0) return;

    bottomMarkTimeout = setTimeout(() => {
      bottomMarkTimeout = null;
      if (!appStore.autoMarkAsRead || appStore.hasMoreArticles || !hasScrolledDown) return;

      for (const articleId of visibleArticleIds) {
        const articleEl = container.querySelector<HTMLElement>(
          `[data-article-id="${articleId}"]`
        );
        if (articleEl?.dataset.isRead === 'false') {
          queueMarkAsRead(articleId);
        }
      }
    }, BOTTOM_DWELL_MS);
  }

  function checkBottomState() {
    if (!scrollContainer) return 0;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    const isAtBottom = distanceFromBottom <= 1;

    const isAtEndOfList = isAtBottom && !appStore.hasMoreArticles;

    if (isAtEndOfList && appStore.autoMarkAsRead && hasScrolledDown) {
      scheduleBottomMark();
    } else {
      clearBottomMarkTimeout();
    }

    return distanceFromBottom;
  }

  function handleScroll(event?: Event) {
    if (event && scrollContainer) {
      const scrollTop = scrollContainer.scrollTop;
      if (scrollTop > lastScrollTop + 1) hasScrolledDown = true;
      lastScrollTop = scrollTop;
    }
    const distanceFromBottom = checkBottomState();

    // Load more when within 200px of bottom
    if (distanceFromBottom < 200 && !appStore.isLoadingMore && appStore.hasMoreArticles) {
      window.dispatchEvent(new CustomEvent('load-more-articles'));
    }
  }

  // Recheck after each page settles: grouped rows or a short page may not
  // fill the viewport, so no scroll event will request the next page.
  $effect(() => {
    const _deps = [
      appStore.articles.length,
      appStore.hasMoreArticles,
      appStore.autoMarkAsRead,
      appStore.isLoadingMore
    ];

    if (!scrollContainer || appStore.isLoading || appStore.isLoadingMore) return;

    const timeout = setTimeout(handleScroll, 150);
    return () => clearTimeout(timeout);
  });

  // Setup observer when autoMarkAsRead is enabled
  $effect(() => {
    const enabled = appStore.autoMarkAsRead;

    if (!scrollContainer || !enabled) {
      if (observer) {
        observer.disconnect();
        observer = null;
      }
      return;
    }

    if (!observer) {
      observer = createAutoMarkReadObserver(scrollContainer);
      observeArticles(observer, scrollContainer);
    }

    return () => {
      observer?.disconnect();
      observer = null;
    };
  });

  // Synchronously register rendered rows before the user can scroll past them.
  // Replacement pages can have the same number of rows as the previous page.
  $effect(() => {
    const articles = appStore.articles;
    if (appStore.isLoading) return;
    if (
      observer &&
      scrollContainer &&
      (articles.length !== lastObservedArticles.length ||
        articles.some((article, i) => article.id !== lastObservedArticles[i].id))
    ) {
      observeArticles(observer, scrollContainer);
    }
    lastObservedArticles = articles;
  });

  // Reset marked IDs when filter changes
  $effect(() => {
    const _filter = [
      appStore.selectedFolderId,
      appStore.selectedFeedId,
      appStore.showUnreadOnly,
      appStore.showStarredOnly,
      appStore.showSavedOnly,
      appStore.hideReadArticles,
      appStore.searchQuery,
      appStore.highlightMode,
      appStore.similarityThreshold
    ];
    resetMarkedIds();
    clearBottomMarkTimeout();
    hasScrolledDown = false;
    lastScrollTop = scrollContainer?.scrollTop ?? 0;
    if (observer && scrollContainer) observeArticles(observer, scrollContainer);
  });

  // Scroll focused article into view
  $effect(() => {
    const idx = appStore.focusedArticleIndex;
    if (idx < 0 || idx >= appStore.articles.length) return;
    const articleId = appStore.articles[idx].id;
    const el = scrollContainer?.querySelector(`[data-article-id="${articleId}"]`);
    if (el) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  });

  onDestroy(clearBottomMarkTimeout);
</script>

<div class="h-full overflow-y-auto" bind:this={scrollContainer} onscroll={handleScroll}>
  {#if appStore.isLoading}
    <div class="flex items-center justify-center h-64">
      <Spinner size="lg" />
    </div>
  {:else if isEmpty}
    <div class="flex flex-col items-center justify-center h-64 text-muted-foreground">
      <p class="text-lg">No articles</p>
      <p class="text-sm">
        {#if appStore.showSavedOnly}
          No saved articles yet
        {:else if appStore.showStarredOnly}
          No starred articles yet
        {:else if appStore.selectedFeedId}
          This feed has no articles
        {:else if appStore.selectedFolderId}
          No articles in this folder
        {:else}
          Add some feeds to get started
        {/if}
      </p>
    </div>
  {:else}
    <div
      class={appStore.viewMode === 'cards'
        ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 p-4'
        : 'divide-y'}
    >
      {#each appStore.articles as article, i (article.id)}
        {#if appStore.viewMode === 'cards'}
          <ArticleCard {article} />
        {:else}
          <ArticleRow {article} />
          {#if i === highlightBoundary()}
            <div class="highlight-separator"></div>
          {/if}
        {/if}
      {/each}
    </div>

    {#if appStore.isLoadingMore}
      <div class="flex items-center justify-center py-4">
        <Spinner size="sm" />
      </div>
    {/if}

    {#if !appStore.hasMoreArticles && appStore.articles.length > 0}
      <div class="text-center py-4 text-sm text-muted-foreground">No more articles</div>
    {/if}
  {/if}
</div>
