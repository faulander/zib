<script lang="ts">
  import type { Article } from '$lib/types';
  import { appStore } from '$lib/stores/app.svelte';
  import * as Card from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';
  import { Star, Circle } from '@lucide/svelte';
  import { cn } from '$lib/utils';

  interface Props {
    article: Article;
  }

  let { article }: Props = $props();

  const publishedDate = $derived(
    article.published_at
      ? new Date(article.published_at).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        })
      : ''
  );

  // Extract a snippet from content
  const snippet = $derived(() => {
    const content = article.full_content || article.rss_content || '';
    // Strip HTML tags and get first 150 chars
    const text = content.replace(/<[^>]*>/g, '').trim();
    return text.length > 150 ? text.slice(0, 150) + '...' : text;
  });

  async function toggleRead(e: MouseEvent) {
    e.stopPropagation();
    const newValue = !article.is_read;

    await fetch(`/api/articles/${article.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_read: newValue })
    });

    appStore.updateArticleInList(article.id, { is_read: newValue });
    window.dispatchEvent(new CustomEvent('reload-counts'));
  }

  async function toggleStar(e: MouseEvent) {
    e.stopPropagation();
    const newValue = !article.is_starred;

    await fetch(`/api/articles/${article.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_starred: newValue })
    });

    appStore.updateArticleInList(article.id, { is_starred: newValue });
  }

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
</script>

<Card.Root
  class={cn(
    'cursor-pointer hover:shadow-md transition-shadow',
    !article.is_read && 'border-l-4 border-l-primary'
  )}
  onclick={handleClick}
>
  <Card.Header class="pb-2">
    <div class="flex items-start justify-between gap-2">
      <Card.Title class="text-base line-clamp-2">{article.title}</Card.Title>
      <div class="flex shrink-0">
        <Button
          variant="ghost"
          size="icon"
          class="h-7 w-7"
          onclick={toggleRead}
          title={article.is_read ? 'Mark as unread' : 'Mark as read'}
        >
          <Circle
            class={cn(
              'h-3 w-3',
              article.is_read ? 'text-muted-foreground' : 'fill-primary text-primary'
            )}
          />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          class="h-7 w-7"
          onclick={toggleStar}
          title={article.is_starred ? 'Remove star' : 'Star'}
        >
          <Star
            class={cn(
              'h-4 w-4',
              article.is_starred && 'fill-yellow-400 text-yellow-400'
            )}
          />
        </Button>
      </div>
    </div>
    <Card.Description class="text-xs">
      {#if article.feed_title}
        <span>{article.feed_title}</span>
        {#if publishedDate}
          <span> · {publishedDate}</span>
        {/if}
      {:else if publishedDate}
        <span>{publishedDate}</span>
      {/if}
    </Card.Description>
  </Card.Header>

  {#if snippet()}
    <Card.Content class="pt-0">
      <p class="text-sm text-muted-foreground line-clamp-3">{snippet()}</p>
    </Card.Content>
  {/if}
</Card.Root>
