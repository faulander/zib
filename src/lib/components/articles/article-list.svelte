<script lang="ts">
  import { appStore } from '$lib/stores/app.svelte';
  import ArticleRow from './article-row.svelte';
  import ArticleCard from './article-card.svelte';
  import Spinner from '$lib/components/spinner.svelte';
  import { createAutoMarkReadObserver, resetMarkedIds } from './use-auto-mark-read.svelte';

  const isEmpty = $derived(appStore.articles.length === 0 && !appStore.isLoading);

  let scrollContainer: HTMLDivElement;
  let observer: IntersectionObserver | null = null;

  function handleScroll() {
    if (!scrollContainer || appStore.isLoadingMore || !appStore.hasMoreArticles) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
    // Load more when within 200px of bottom
    if (scrollHeight - scrollTop - clientHeight < 200) {
      window.dispatchEvent(new CustomEvent('load-more-articles'));
    }
  }

  function observeArticles() {
    if (!observer || !scrollContainer) return;
    const articleElements = scrollContainer.querySelectorAll('[data-article-id]');
    articleElements.forEach((el) => observer?.observe(el));
  }

  // Setup observer when autoMarkAsRead is enabled
  $effect(() => {
    const enabled = appStore.autoMarkAsRead;

    if (scrollContainer && enabled) {
      observer = createAutoMarkReadObserver(scrollContainer);
      observeArticles();
    } else if (observer) {
      observer.disconnect();
      observer = null;
    }

    return () => {
      observer?.disconnect();
      observer = null;
    };
  });

  // Re-observe when articles change
  $effect(() => {
    const _articles = appStore.articles;

    if (observer && scrollContainer) {
      observer.disconnect();
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        observeArticles();
      }, 0);
    }
  });

  // Reset marked IDs when filter changes
  $effect(() => {
    const _filter = appStore.currentFilter;
    resetMarkedIds();
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
        {#if appStore.showStarredOnly}
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
      {#each appStore.articles as article (article.id)}
        {#if appStore.viewMode === 'cards'}
          <ArticleCard {article} />
        {:else}
          <ArticleRow {article} />
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
