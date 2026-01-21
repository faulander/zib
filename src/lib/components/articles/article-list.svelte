<script lang="ts">
  import { appStore } from '$lib/stores/app.svelte';
  import { ScrollArea } from '$lib/components/ui/scroll-area';
  import ArticleRow from './article-row.svelte';
  import ArticleCard from './article-card.svelte';
  import Spinner from '$lib/components/spinner.svelte';

  const isEmpty = $derived(appStore.articles.length === 0 && !appStore.isLoading);
</script>

<ScrollArea class="h-full">
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
    <div class={appStore.viewMode === 'cards' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4' : 'divide-y'}>
      {#each appStore.articles as article (article.id)}
        {#if appStore.viewMode === 'cards'}
          <ArticleCard {article} />
        {:else}
          <ArticleRow {article} />
        {/if}
      {/each}
    </div>
  {/if}
</ScrollArea>
