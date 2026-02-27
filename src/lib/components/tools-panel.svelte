<script lang="ts">
  import { appStore } from '$lib/stores/app.svelte';
  import { Button } from '$lib/components/ui/button';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
  import { toast } from 'svelte-sonner';
  import { LayoutList, LayoutGrid, CheckCheck, RefreshCw, Filter, Clock, Search, X } from '@lucide/svelte';

  let searchValue = $state('');

  $effect(() => {
    const value = searchValue;
    const timeout = setTimeout(() => {
      appStore.setSearchQuery(value);
    }, 300);
    return () => clearTimeout(timeout);
  });

  function clearSearch() {
    searchValue = '';
    appStore.setSearchQuery('');
  }

  async function markReadOlderThan(period: 'day' | 'week' | 'month' | 'all') {
    const filters: Record<string, unknown> = { older_than: period };

    if (appStore.selectedFeedId) {
      filters.feed_id = appStore.selectedFeedId;
    } else if (appStore.selectedFolderId) {
      filters.folder_id = appStore.selectedFolderId;
    }

    try {
      const res = await fetch('/api/mark-read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters)
      });

      const data = await res.json();

      if (res.ok) {
        toast.success(`Marked ${data.marked_count} articles as read`);
        window.dispatchEvent(new CustomEvent('reload-data'));
      } else {
        toast.error('Failed to mark articles as read');
      }
    } catch {
      toast.error('Failed to mark articles as read');
    }
  }

  async function handleRefresh() {
    appStore.setIsRefreshing(true);

    try {
      const feedIds = appStore.selectedFeedId
        ? [appStore.selectedFeedId]
        : appStore.selectedFolderId
          ? appStore.feeds.filter((f) => f.folder_id === appStore.selectedFolderId).map((f) => f.id)
          : undefined;

      await fetch('/api/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feed_ids: feedIds })
      });

      window.dispatchEvent(new CustomEvent('reload-data'));
      toast.success('Feeds refreshed');
    } catch {
      toast.error('Failed to refresh feeds');
    } finally {
      appStore.setIsRefreshing(false);
    }
  }
</script>

<div class="flex items-center justify-between px-4 py-2 border-b bg-background">
  <div class="flex items-center gap-2">
    <h2 class="font-medium text-sm">
      {#if appStore.showSavedOnly}
        Saved
      {:else if appStore.showStarredOnly}
        Starred
      {:else if appStore.selectedFeedId}
        {appStore.feeds.find((f) => f.id === appStore.selectedFeedId)?.title || 'Feed'}
      {:else if appStore.selectedFolderId}
        {appStore.folders.find((f) => f.id === appStore.selectedFolderId)?.name || 'Folder'}
      {:else}
        All Items
      {/if}
    </h2>

    <span class="text-xs text-muted-foreground">
      {#if appStore.showSavedOnly}
        ({appStore.unreadCounts.saved_total ?? appStore.articles.length} articles)
      {:else if appStore.showStarredOnly}
        ({appStore.articles.length} articles)
      {:else}
        {@const unreadCount = appStore.selectedFeedId
          ? (appStore.unreadCounts.by_feed[appStore.selectedFeedId] ?? 0)
          : appStore.selectedFolderId
            ? (appStore.unreadCounts.by_folder[appStore.selectedFolderId] ?? 0)
            : appStore.unreadCounts.total}
        ({unreadCount} unread)
      {/if}
    </span>

    <!-- Search input -->
    <div class="relative flex items-center">
      <Search class="absolute left-2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
      <input
        type="text"
        placeholder="Search articles..."
        bind:value={searchValue}
        class="h-8 w-40 sm:w-56 rounded-md border bg-background pl-7 pr-7 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
      />
      {#if searchValue}
        <button
          type="button"
          onclick={clearSearch}
          class="absolute right-1.5 p-0.5 rounded hover:bg-muted"
        >
          <X class="h-3.5 w-3.5 text-muted-foreground" />
        </button>
      {/if}
    </div>
  </div>

  <div class="flex items-center gap-1">
    <!-- Filter: unread only -->
    <Button
      variant={appStore.showUnreadOnly ? 'secondary' : 'ghost'}
      size="sm"
      onclick={() => appStore.setShowUnreadOnly(!appStore.showUnreadOnly)}
      title="Show unread only"
      class="px-2 sm:px-3"
    >
      <Filter class="h-4 w-4 sm:mr-1" />
      <span class="hidden sm:inline">Unread</span>
    </Button>

    <!-- View toggle -->
    <div class="flex border rounded-md">
      <Button
        variant={appStore.viewMode === 'list' ? 'secondary' : 'ghost'}
        size="icon"
        class="h-8 w-8 rounded-r-none"
        onclick={() => appStore.setViewMode('list')}
        title="List view"
      >
        <LayoutList class="h-4 w-4" />
      </Button>
      <Button
        variant={appStore.viewMode === 'cards' ? 'secondary' : 'ghost'}
        size="icon"
        class="h-8 w-8 rounded-l-none"
        onclick={() => appStore.setViewMode('cards')}
        title="Card view"
      >
        <LayoutGrid class="h-4 w-4" />
      </Button>
    </div>

    <!-- Refresh -->
    <Button
      variant="ghost"
      size="icon"
      onclick={handleRefresh}
      disabled={appStore.isRefreshing}
      title={appStore.selectedFeedId
        ? 'Refresh this feed'
        : appStore.selectedFolderId
          ? 'Refresh feeds in this folder'
          : 'Refresh all feeds'}
    >
      <RefreshCw class="h-4 w-4 {appStore.isRefreshing ? 'animate-spin' : ''}" />
    </Button>

    <!-- Mark read dropdown -->
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button variant="ghost" size="sm" class="px-2 sm:px-3" {...props}>
            <CheckCheck class="h-4 w-4 sm:mr-1" />
            <span class="hidden sm:inline">Mark Read</span>
          </Button>
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="end">
        <DropdownMenu.Item onclick={() => markReadOlderThan('day')}>
          <Clock class="h-4 w-4 mr-2" />
          Older than 1 day
        </DropdownMenu.Item>
        <DropdownMenu.Item onclick={() => markReadOlderThan('week')}>
          <Clock class="h-4 w-4 mr-2" />
          Older than 1 week
        </DropdownMenu.Item>
        <DropdownMenu.Item onclick={() => markReadOlderThan('month')}>
          <Clock class="h-4 w-4 mr-2" />
          Older than 1 month
        </DropdownMenu.Item>
        <DropdownMenu.Separator />
        <DropdownMenu.Item onclick={() => markReadOlderThan('all')}>
          <CheckCheck class="h-4 w-4 mr-2" />
          Mark all as read
        </DropdownMenu.Item>
      </DropdownMenu.Content>
    </DropdownMenu.Root>
  </div>
</div>
