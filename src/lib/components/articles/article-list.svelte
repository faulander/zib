<script lang="ts">
  import { appStore } from '$lib/stores/app.svelte';
  import ArticleRow from './article-row.svelte';
  import ArticleCard from './article-card.svelte';
  import Spinner from '$lib/components/spinner.svelte';
  import {
    createAutoMarkReadObserver,
    resetMarkedIds,
    observeArticles
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

  let scrollContainer: HTMLDivElement;
  let observer: IntersectionObserver | null = null;
  let lastArticleCount = 0;

  function handleScroll() {
    if (!scrollContainer || appStore.isLoadingMore || !appStore.hasMoreArticles) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
    // Load more when within 200px of bottom
    if (scrollHeight - scrollTop - clientHeight < 200) {
      window.dispatchEvent(new CustomEvent('load-more-articles'));
    }
  }

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

    // Create observer only if we don't have one
    if (!observer) {
      observer = createAutoMarkReadObserver(scrollContainer);
      // Initial observation after DOM has settled
      setTimeout(() => {
        if (observer && scrollContainer) {
          observeArticles(observer, scrollContainer);
        }
      }, 150);
    }

    return () => {
      observer?.disconnect();
      observer = null;
    };
  });

  // Observe new articles when more are loaded (not when read status changes)
  $effect(() => {
    const articleCount = appStore.articles.length;

    // Only re-observe if new articles were added (count increased)
    if (observer && scrollContainer && articleCount > lastArticleCount) {
      setTimeout(() => {
        if (observer && scrollContainer) {
          observeArticles(observer, scrollContainer);
        }
      }, 50);
    }
    lastArticleCount = articleCount;
  });

  // Reset marked IDs when filter changes
  $effect(() => {
    const _filter = appStore.currentFilter;
    resetMarkedIds();
    lastArticleCount = 0; // Reset count so we re-observe on filter change
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
      <div class="text-center py-4 text-sm text-muted-foreground">No more articles</div>
    {/if}
  {/if}
</div>
