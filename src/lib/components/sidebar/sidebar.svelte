<script lang="ts">
  import { appStore } from '$lib/stores/app.svelte';
  import { Button } from '$lib/components/ui/button';
  import { Separator } from '$lib/components/ui/separator';
  import FolderItem from './folder-item.svelte';
  import FeedItem from './feed-item.svelte';
  import AddFeedDialog from '$lib/components/add-feed-dialog.svelte';
  import { Inbox, FolderPlus, RefreshCw, Settings, Bookmark } from '@lucide/svelte';
  import { goto } from '$app/navigation';

  let addFeedOpen = $state(false);

  let draggedItem = $state<{ type: 'feed' | 'folder'; id: number } | null>(null);
  let dragOverId = $state<number | null>(null);
  let dragOverType = $state<'feed' | 'folder' | null>(null);

  const uncategorizedFeeds = $derived(appStore.feeds.filter((f) => f.folder_id === null));

  const sortedFolders = $derived(
    [...appStore.folders].sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id)
  );
  const sortedUncategorizedFeeds = $derived(
    [...uncategorizedFeeds].sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id)
  );

  const isAllSelected = $derived(
    !appStore.selectedFolderId && !appStore.selectedFeedId && !appStore.showStarredOnly && !appStore.showSavedOnly
  );

  async function handleRefreshAll() {
    appStore.setIsRefreshing(true);
    try {
      await fetch('/api/refresh', { method: 'POST' });
      // Reload data after refresh
      window.dispatchEvent(new CustomEvent('reload-data'));
    } finally {
      appStore.setIsRefreshing(false);
    }
  }

  function clearDrag() {
    draggedItem = null;
    dragOverId = null;
    dragOverType = null;
  }

  async function handleDrop(targetType: 'folder' | 'feed', targetId: number) {
    if (!draggedItem) return;

    if (draggedItem.type === 'folder' && targetType === 'folder') {
      const currentOrder = sortedFolders.map(f => f.id);
      const fromIdx = currentOrder.indexOf(draggedItem.id);
      const toIdx = currentOrder.indexOf(targetId);
      if (fromIdx === -1 || toIdx === -1 || fromIdx === toIdx) { clearDrag(); return; }

      currentOrder.splice(fromIdx, 1);
      currentOrder.splice(toIdx, 0, draggedItem.id);

      const items = currentOrder.map((id, i) => ({ id, position: i }));
      await fetch('/api/folders/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items })
      });
      window.dispatchEvent(new CustomEvent('reload-data'));
    } else if (draggedItem.type === 'feed' && targetType === 'folder') {
      await fetch(`/api/feeds/${draggedItem.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_id: targetId })
      });
      window.dispatchEvent(new CustomEvent('reload-data'));
    } else if (draggedItem.type === 'feed' && targetType === 'feed') {
      const currentOrder = sortedUncategorizedFeeds.map(f => f.id);
      const fromIdx = currentOrder.indexOf(draggedItem.id);
      const toIdx = currentOrder.indexOf(targetId);
      if (fromIdx === -1 || toIdx === -1 || fromIdx === toIdx) { clearDrag(); return; }

      currentOrder.splice(fromIdx, 1);
      currentOrder.splice(toIdx, 0, draggedItem.id);

      const items = currentOrder.map((id, i) => ({ id, position: i }));
      await fetch('/api/feeds/reorder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items })
      });
      window.dispatchEvent(new CustomEvent('reload-data'));
    }

    clearDrag();
  }
</script>

<div class="flex h-full flex-col">
  <div class="flex items-center justify-between p-4 pr-12 lg:pr-4">
    <h2 class="text-lg font-semibold">ZIB</h2>
    <div class="flex gap-1">
      <Button
        variant="ghost"
        size="icon"
        onclick={handleRefreshAll}
        disabled={appStore.isRefreshing}
        title="Refresh all feeds"
      >
        <RefreshCw class="h-4 w-4 {appStore.isRefreshing ? 'animate-spin' : ''}" />
      </Button>
      <Button variant="ghost" size="icon" onclick={() => goto('/settings')} title="Settings">
        <Settings class="h-4 w-4" />
      </Button>
    </div>
  </div>

  <Separator />

  <div class="flex-1 overflow-y-auto">
    <div class="p-2">
      <!-- All Items -->
      <Button
        variant={isAllSelected ? 'secondary' : 'ghost'}
        class="w-full justify-start gap-2 {isAllSelected ? '' : 'sidebar-item-hover'}"
        onclick={() => {
          appStore.selectFolder(null);
          appStore.selectFeed(null);
          appStore.setShowStarredOnly(false);
          appStore.setSidebarOpen(false);
        }}
      >
        <Inbox class="h-4 w-4" />
        <span class="flex-1 text-left">All Items</span>
        {#if appStore.unreadCounts.total > 0}
          <span class="text-xs text-muted-foreground">{appStore.unreadCounts.total}</span>
        {/if}
      </Button>


      <!-- Saved -->
      <Button
        variant={appStore.showSavedOnly ? 'secondary' : 'ghost'}
        class="w-full justify-start gap-2 {appStore.showSavedOnly ? '' : 'sidebar-item-hover'}"
        onclick={() => {
          appStore.setShowSavedOnly(true);
          appStore.setSidebarOpen(false);
        }}
      >
        <Bookmark class="h-4 w-4" />
        <span class="flex-1 text-left">Saved</span>
      </Button>

      <Separator class="my-2" />

      <!-- Folders -->
      {#each sortedFolders as folder (folder.id)}
        <div
          role="listitem"
          draggable="true"
          ondragstart={(e) => {
            draggedItem = { type: 'folder', id: folder.id };
            e.dataTransfer?.setData('text/plain', '');
          }}
          ondragover={(e) => {
            e.preventDefault();
            dragOverId = folder.id;
            dragOverType = 'folder';
          }}
          ondragleave={() => { if (dragOverId === folder.id) dragOverId = null; }}
          ondrop={(e) => {
            e.preventDefault();
            handleDrop('folder', folder.id);
          }}
          ondragend={clearDrag}
          class={dragOverId === folder.id && dragOverType === 'folder' ? 'border-t-2 border-primary' : ''}
        >
          <FolderItem {folder} />
        </div>
      {/each}

      <!-- Uncategorized Feeds -->
      {#if sortedUncategorizedFeeds.length > 0}
        <div class="mt-2">
          {#each sortedUncategorizedFeeds as feed (feed.id)}
            <div
              role="listitem"
              draggable="true"
              ondragstart={(e) => {
                draggedItem = { type: 'feed', id: feed.id };
                e.dataTransfer?.setData('text/plain', '');
              }}
              ondragover={(e) => {
                e.preventDefault();
                dragOverId = feed.id;
                dragOverType = 'feed';
              }}
              ondragleave={() => { if (dragOverId === feed.id) dragOverId = null; }}
              ondrop={(e) => {
                e.preventDefault();
                handleDrop('feed', feed.id);
              }}
              ondragend={clearDrag}
              class={dragOverId === feed.id && dragOverType === 'feed' ? 'border-t-2 border-primary' : ''}
            >
              <FeedItem {feed} />
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <Separator />

  <div class="p-2">
    <Button variant="outline" class="w-full" onclick={() => (addFeedOpen = true)}>
      <FolderPlus class="mr-2 h-4 w-4" />
      Add Feed
    </Button>
  </div>
</div>

<AddFeedDialog bind:open={addFeedOpen} />
