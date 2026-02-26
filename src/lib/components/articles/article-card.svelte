<script lang="ts">
  import type { Article } from '$lib/types';
  import { appStore } from '$lib/stores/app.svelte';
  import { Rss, Layers } from '@lucide/svelte';
  import { cn } from '$lib/utils';
  import { Badge } from '$lib/components/ui/badge';

  interface Props {
    article: Article;
  }

  let { article }: Props = $props();
  let imageError = $state(false);

  const publishedDate = $derived(
    article.published_at
      ? new Date(article.published_at).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric'
        })
      : ''
  );

  const showImage = $derived(article.image_url && !imageError);

  function handleClick() {
    if (!article.is_read) {
      fetch(`/api/articles/${article.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: true })
      });
      appStore.updateArticleInList(article.id, { is_read: true });
      window.dispatchEvent(new CustomEvent('reload-counts'));
    }

    appStore.selectArticle(article.id);
  }

  function handleImageError() {
    imageError = true;
  }

  const focused = $derived(appStore.articles[appStore.focusedArticleIndex]?.id === article.id);
  const showTypographic = $derived(
    article.is_feed_highlighted &&
    (appStore.highlightMode === 'typographic' || appStore.highlightMode === 'both')
  );
</script>

<div
  data-article-id={article.id}
  data-is-read={article.is_read}
  class={cn(
    'bg-card text-card-foreground rounded-xl border shadow-sm cursor-pointer overflow-hidden h-[280px] flex flex-col transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-primary/50',
    !article.is_read && 'border-l-4 border-l-primary',
    focused && 'ring-2 ring-primary bg-accent/50',
    showTypographic && 'ring-2 ring-amber-400/50 dark:ring-amber-600/50'
  )}
  onclick={handleClick}
  onkeydown={(e) => e.key === 'Enter' && handleClick()}
  role="button"
  tabindex="0"
>
  <!-- Image area - fixed height -->
  <div class="relative w-full h-40 shrink-0 overflow-hidden bg-muted">
    {#if showImage}
      <img
        src={article.image_url}
        alt=""
        class="w-full h-full object-cover"
        loading="lazy"
        onerror={handleImageError}
      />
    {:else}
      <div class="w-full h-full flex items-center justify-center bg-muted/50">
        <Rss class="h-12 w-12 text-muted-foreground/30" />
      </div>
    {/if}

    {#if article.similar_count && article.similar_count > 0}
      <Badge variant="secondary" class="absolute top-2 right-2 gap-1 text-xs">
        <Layers class="h-3 w-3" />
        +{article.similar_count}
      </Badge>
    {/if}
  </div>

  <!-- Content area -->
  <div class="flex flex-col flex-1 p-3">
    <h3 class="text-sm font-semibold line-clamp-2">{article.title}</h3>
    <div class="text-xs text-muted-foreground mt-auto">
      {#if article.feed_title}
        <div class={cn('truncate', showTypographic && 'font-semibold text-amber-700 dark:text-amber-400')}>{article.feed_title}</div>
      {/if}
      {#if publishedDate}
        <div>{publishedDate}</div>
      {/if}
    </div>
  </div>
</div>
