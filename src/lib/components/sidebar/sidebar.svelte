<script lang="ts">
  import { appStore } from '$lib/stores/app.svelte';
  import { Button } from '$lib/components/ui/button';
  import { Separator } from '$lib/components/ui/separator';
  import FolderItem from './folder-item.svelte';
  import FeedItem from './feed-item.svelte';
  import AddFeedDialog from '$lib/components/add-feed-dialog.svelte';
  import { Inbox, Star, FolderPlus, RefreshCw, Upload, Settings } from '@lucide/svelte';
  import { goto } from '$app/navigation';

  let addFeedOpen = $state(false);
  let importOpmlOpen = $state(false);

  const uncategorizedFeeds = $derived(appStore.feeds.filter((f) => f.folder_id === null));

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

  function handleImportClick() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.opml,.xml';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/import/opml', {
          method: 'POST',
          body: formData
        });

        if (res.ok) {
          window.dispatchEvent(new CustomEvent('reload-data'));
        }
      } catch (err) {
        console.error('Import failed:', err);
      }
    };
    input.click();
  }
</script>

<div class="flex h-full flex-col">
  <div class="flex items-center justify-between p-4">
    <h2 class="text-lg font-semibold">Feeds</h2>
    <div class="flex gap-1">
      <Button variant="ghost" size="icon" onclick={handleImportClick} title="Import OPML">
        <Upload class="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onclick={handleRefreshAll}
        disabled={appStore.isRefreshing}
        title="Refresh all feeds"
      >
        <RefreshCw class="h-4 w-4 {appStore.isRefreshing ? 'animate-spin' : ''}" />
      </Button>
    </div>
  </div>

  <Separator />

  <div class="flex-1 overflow-y-auto">
    <div class="p-2">
      <!-- All Items -->
      <Button
        variant={!appStore.selectedFolderId && !appStore.selectedFeedId && !appStore.showStarredOnly
          ? 'secondary'
          : 'ghost'}
        class="w-full justify-start gap-2"
        onclick={() => {
          appStore.selectFolder(null);
          appStore.selectFeed(null);
          appStore.setShowStarredOnly(false);
        }}
      >
        <Inbox class="h-4 w-4" />
        <span class="flex-1 text-left">All Items</span>
        {#if appStore.unreadCounts.total > 0}
          <span class="text-xs text-muted-foreground">{appStore.unreadCounts.total}</span>
        {/if}
      </Button>

      <!-- Starred -->
      <Button
        variant={appStore.showStarredOnly ? 'secondary' : 'ghost'}
        class="w-full justify-start gap-2"
        onclick={() => appStore.setShowStarredOnly(true)}
      >
        <Star class="h-4 w-4" />
        <span class="flex-1 text-left">Starred</span>
      </Button>

      <Separator class="my-2" />

      <!-- Folders -->
      {#each appStore.folders as folder (folder.id)}
        <FolderItem {folder} />
      {/each}

      <!-- Uncategorized Feeds -->
      {#if uncategorizedFeeds.length > 0}
        <div class="mt-2">
          {#each uncategorizedFeeds as feed (feed.id)}
            <FeedItem {feed} />
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <Separator />

  <div class="p-2 space-y-2">
    <Button variant="outline" class="w-full" onclick={() => (addFeedOpen = true)}>
      <FolderPlus class="mr-2 h-4 w-4" />
      Add Feed
    </Button>
    <Button variant="ghost" class="w-full justify-start" onclick={() => goto('/settings')}>
      <Settings class="mr-2 h-4 w-4" />
      Settings
    </Button>
  </div>
</div>

<AddFeedDialog bind:open={addFeedOpen} />
