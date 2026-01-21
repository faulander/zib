<script lang="ts">
  import type { Article } from '$lib/types';
  import { appStore } from '$lib/stores/app.svelte';
  import { cn } from '$lib/utils';

  interface Props {
    article: Article;
  }

  let { article }: Props = $props();

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
</script>

<div
  class={cn(
    'w-full text-left px-4 py-2 hover:bg-muted/50 transition-colors flex items-center gap-3 cursor-pointer',
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

  <span class="text-xs opacity-60 shrink-0 w-16 text-right">{publishedDate}</span>
</div>
