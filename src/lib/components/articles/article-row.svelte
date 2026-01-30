<script lang="ts">
  import type { Article } from '$lib/types';
  import { appStore } from '$lib/stores/app.svelte';
  import { cn } from '$lib/utils';
  import { BookmarkPlus, Loader2, Layers } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';
  import { Badge } from '$lib/components/ui/badge';

  interface Props {
    article: Article;
  }

  let { article }: Props = $props();
  let isSaving = $state(false);

  function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '';

    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    // If today, show relative time
    if (date.toDateString() === now.toDateString()) {
      if (diffMins < 1) return 'now';
      if (diffMins < 60) return `${diffMins}m`;
      return `${diffHours}h`;
    }

    // If yesterday
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return 'yesterday';
    }

    // Otherwise show date
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric'
    });
  }

  const publishedDate = $derived(formatDate(article.published_at));

  function handleClick() {
    // Mark as read when opening
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

  async function saveToInstapaper(e: MouseEvent) {
    e.stopPropagation();
    if (isSaving) return;

    isSaving = true;
    try {
      const res = await fetch(`/api/articles/${article.id}/instapaper`, {
        method: 'POST'
      });

      if (res.ok) {
        toast.success('Saved to Instapaper');
      } else {
        const data = await res.json();
        toast.error(data.error || 'Failed to save');
      }
    } catch {
      toast.error('Failed to save to Instapaper');
    } finally {
      isSaving = false;
    }
  }
</script>

<!-- Desktop layout: single row -->
<div
  data-article-id={article.id}
  data-is-read={article.is_read}
  class={cn(
    'w-full text-left px-4 transition-colors cursor-pointer article-row-hover hidden sm:flex items-center gap-3',
    appStore.compactListView ? 'py-1' : 'py-2',
    article.is_read && 'text-muted-foreground'
  )}
  role="button"
  tabindex="0"
  onclick={handleClick}
  onkeydown={(e) => e.key === 'Enter' && handleClick()}
>
  {#if article.feed_title}
    <span class="text-xs opacity-60 truncate w-28 shrink-0">{article.feed_title}</span>
  {/if}

  <h3 class={cn('text-sm truncate flex-1 min-w-0', !article.is_read && 'font-semibold')}>
    {article.title}
  </h3>

  {#if article.similar_count && article.similar_count > 0}
    <Badge variant="secondary" class="shrink-0 gap-1 text-xs">
      <Layers class="h-3 w-3" />
      +{article.similar_count}
    </Badge>
  {/if}

  {#if appStore.instapaperEnabled}
    <button
      type="button"
      class="shrink-0 p-1 rounded hover:bg-muted transition-colors opacity-60 hover:opacity-100 disabled:opacity-40"
      onclick={saveToInstapaper}
      title="Save to Instapaper"
      disabled={isSaving}
    >
      {#if isSaving}
        <Loader2 class="h-4 w-4 animate-spin" />
      {:else}
        <BookmarkPlus class="h-4 w-4" />
      {/if}
    </button>
  {/if}

  <span class="text-xs opacity-60 shrink-0 w-16 text-right">{publishedDate}</span>
</div>

<!-- Mobile layout: stacked rows -->
<div
  data-article-id={article.id}
  data-is-read={article.is_read}
  class={cn(
    'w-full text-left px-4 transition-colors cursor-pointer article-row-hover flex sm:hidden flex-col gap-0.5',
    appStore.compactListView ? 'py-1.5' : 'py-2',
    article.is_read && 'text-muted-foreground'
  )}
  role="button"
  tabindex="0"
  onclick={handleClick}
  onkeydown={(e) => e.key === 'Enter' && handleClick()}
>
  <div class="flex items-center gap-2">
    {#if article.feed_title}
      <span class="text-xs opacity-60 truncate flex-1">{article.feed_title}</span>
    {/if}
    <span class="text-xs opacity-60 shrink-0">{publishedDate}</span>
    {#if appStore.instapaperEnabled}
      <button
        type="button"
        class="shrink-0 p-1 -m-1 rounded hover:bg-muted transition-colors opacity-60 hover:opacity-100 disabled:opacity-40"
        onclick={saveToInstapaper}
        title="Save to Instapaper"
        disabled={isSaving}
      >
        {#if isSaving}
          <Loader2 class="h-4 w-4 animate-spin" />
        {:else}
          <BookmarkPlus class="h-4 w-4" />
        {/if}
      </button>
    {/if}
  </div>
  <div class="flex items-center gap-2">
    <h3 class={cn('text-sm flex-1', !article.is_read && 'font-semibold')}>
      {article.title}
    </h3>
    {#if article.similar_count && article.similar_count > 0}
      <Badge variant="secondary" class="shrink-0 gap-1 text-xs">
        <Layers class="h-3 w-3" />
        +{article.similar_count}
      </Badge>
    {/if}
  </div>
</div>
