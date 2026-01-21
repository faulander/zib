<script lang="ts">
  import type { Folder, Feed } from '$lib/types';
  import { appStore } from '$lib/stores/app.svelte';
  import { Button } from '$lib/components/ui/button';
  import FeedItem from './feed-item.svelte';
  import { ChevronRight, ChevronDown, Folder as FolderIcon, CheckCheck } from '@lucide/svelte';

  interface Props {
    folder: Folder;
  }

  let { folder }: Props = $props();

  let expanded = $state(false);

  const folderFeeds = $derived(appStore.feeds.filter((f) => f.folder_id === folder.id));

  const unreadCount = $derived(appStore.unreadCounts.by_folder[folder.id] || 0);

  const isSelected = $derived(appStore.selectedFolderId === folder.id && !appStore.selectedFeedId);

  async function markAllRead(e: MouseEvent) {
    e.stopPropagation();
    await fetch('/api/mark-read', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder_id: folder.id })
    });
    window.dispatchEvent(new CustomEvent('reload-data'));
  }
</script>

<div class="group">
  <Button
    variant={isSelected ? 'secondary' : 'ghost'}
    class="w-full justify-start gap-1 pr-1"
    onclick={() => appStore.selectFolder(folder.id)}
  >
    <button
      class="p-0.5 hover:bg-muted rounded"
      onclick={(e) => {
        e.stopPropagation();
        expanded = !expanded;
      }}
    >
      {#if expanded}
        <ChevronDown class="h-4 w-4" />
      {:else}
        <ChevronRight class="h-4 w-4" />
      {/if}
    </button>
    <FolderIcon class="h-4 w-4" />
    <span class="flex-1 text-left truncate">{folder.name}</span>
    {#if unreadCount > 0}
      <span class="text-xs text-muted-foreground mr-1">{unreadCount}</span>
    {/if}
    <button
      class="p-1 opacity-0 group-hover:opacity-100 hover:bg-muted rounded transition-opacity"
      onclick={markAllRead}
      title="Mark all as read"
    >
      <CheckCheck class="h-3 w-3" />
    </button>
  </Button>

  {#if expanded && folderFeeds.length > 0}
    <div class="ml-4 border-l pl-2">
      {#each folderFeeds as feed (feed.id)}
        <FeedItem {feed} />
      {/each}
    </div>
  {/if}
</div>
