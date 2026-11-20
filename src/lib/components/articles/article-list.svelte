<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { appStore } from '$lib/stores/app.svelte';
  import { READ_WRITE_HEADERS } from '$lib/client-version';
  import ArticleRow from './article-row.svelte';
  import ArticleCard from './article-card.svelte';
  import Spinner from '$lib/components/spinner.svelte';
  import { Button } from '$lib/components/ui/button';
  import { CheckCheck } from '@lucide/svelte';
  import {
    createAutoMarkReadObserver,
    observeArticles,
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

  let isMarkingAllRead = $state(false);

  async function markAllListedRead() {
    const ids = appStore.articles.filter((article) => !article.is_read).map((article) => article.id);
    if (ids.length === 0 || isMarkingAllRead) return;

    // In search/saved views, limit the action to the displayed articles.
    // Otherwise match the toolbar's "Mark all as read" scope.
    const restrictedView =
      appStore.showSavedOnly || appStore.showStarredOnly || !!appStore.searchQuery.trim();
    const requests: Record<string, unknown>[] = [];
    if (restrictedView) {
      for (let i = 0; i < ids.length; i += 1000) {
        requests.push({ ids: ids.slice(i, i + 1000) });
      }
    } else {
      requests.push({
        older_than: 'all',
        ...(appStore.selectedFeedId
          ? { feed_id: appStore.selectedFeedId }
          : appStore.selectedFolderId
            ? { folder_id: appStore.selectedFolderId }
            : {})
      });
    }

    isMarkingAllRead = true;
    try {
      let markedCount = 0;
      for (const body of requests) {
        const response = await fetch('/api/mark-read', {
          method: 'POST',
          headers: READ_WRITE_HEADERS,
          body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error('Failed to mark articles as read');
        const result = await response.json();
        markedCount += result.marked_count;
      }
      toast.success(`Marked ${markedCount} articles as read`);
      window.dispatchEvent(new CustomEvent('reload-data'));
    } catch {
      toast.error('Failed to mark articles as read');
      window.dispatchEvent(new CustomEvent('reload-data'));
    } finally {
      isMarkingAllRead = false;
    }
  }

  let scrollContainer = $state<HTMLDivElement | null>(null);
  let observer: IntersectionObserver | null = null;
  let lastObservedArticles: typeof appStore.articles = [];

  function distanceFromBottom() {
    if (!scrollContainer) return 0;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
    return scrollHeight - scrollTop - clientHeight;
  }

  function handleScroll() {
    // Load more when within 200px of bottom
    if (distanceFromBottom() < 200 && !appStore.isLoadingMore && appStore.hasMoreArticles) {
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
      <div class="flex flex-col items-center gap-2 py-4 text-sm text-muted-foreground">
        <span>No more articles</span>
        <Button
          variant="outline"
          size="sm"
          onclick={markAllListedRead}
          disabled={isMarkingAllRead || !appStore.articles.some((article) => !article.is_read)}
        >
          <CheckCheck class="h-4 w-4" />
          {isMarkingAllRead ? 'Marking as read…' : 'Mark all as read'}
        </Button>
      </div>
    {/if}
  {/if}
</div>
