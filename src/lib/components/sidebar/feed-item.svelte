<script lang="ts">
  import type { Feed } from '$lib/types';
  import { appStore } from '$lib/stores/app.svelte';
  import { Button } from '$lib/components/ui/button';
  import { Rss, CheckCheck, X, AlertTriangle } from '@lucide/svelte';

  interface Props {
    feed: Feed;
  }

  let { feed }: Props = $props();

  const unreadCount = $derived(appStore.unreadCounts.by_feed[feed.id] || 0);
  const hasError = $derived(!!feed.last_error);

  const isSelected = $derived(appStore.selectedFeedId === feed.id);

  async function markAllRead(e: MouseEvent) {
    e.stopPropagation();
    await fetch('/api/mark-read', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feed_id: feed.id })
    });
    window.dispatchEvent(new CustomEvent('reload-data'));
  }

  async function deleteFeed(e: MouseEvent) {
    e.stopPropagation();
    if (!confirm(`Delete "${feed.title}"? This will also delete all its articles.`)) {
      return;
    }

    await fetch(`/api/feeds/${feed.id}`, {
      method: 'DELETE'
    });
    window.dispatchEvent(new CustomEvent('reload-data'));
  }
</script>

<div class="group">
  <Button
    variant={isSelected ? 'secondary' : 'ghost'}
    class="w-full justify-start gap-2 pr-1 h-8 text-sm {isSelected ? '' : 'sidebar-item-hover'}"
    onclick={() => {
      appStore.selectFeed(feed.id);
      appStore.setSidebarOpen(false);
    }}
  >
    {#if hasError}
      <span title={feed.last_error ?? ''}>
        <AlertTriangle class="h-4 w-4 text-yellow-500" />
      </span>
    {:else if feed.favicon_url}
      <img
        src={feed.favicon_url}
        alt=""
        class="h-4 w-4 rounded"
        onerror={(e) => {
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
    {:else}
      <Rss class="h-4 w-4 text-muted-foreground" />
    {/if}
    <span class="flex-1 text-left truncate">{feed.title}</span>
    {#if unreadCount > 0}
      <span class="text-xs text-muted-foreground mr-1">{unreadCount}</span>
    {/if}
    <button
      class="p-1 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 hover:bg-muted rounded transition-opacity"
      onclick={markAllRead}
      title="Mark all as read"
    >
      <CheckCheck class="h-3 w-3" />
    </button>
    <button
      class="p-1 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 rounded transition-opacity text-red-500 hover:bg-red-500/20"
      onclick={deleteFeed}
      title="Delete feed"
    >
      <X class="h-3 w-3" />
    </button>
  </Button>
</div>
