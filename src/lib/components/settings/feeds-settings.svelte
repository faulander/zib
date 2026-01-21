<script lang="ts">
  import type { Feed } from '$lib/types';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Pencil, RefreshCw, X, Clock, Rss, AlertTriangle } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';
  import FeedEditDialog from '$lib/components/feed-edit-dialog.svelte';

  interface FeedWithTTL extends Feed {
    effective_ttl_minutes: number;
    effective_ttl_display: string;
    statistics: {
      avg_articles_per_day: number;
      read_rate: number;
      calculated_ttl_minutes: number | null;
      ttl_override_minutes: number | null;
      ttl_calculation_reason: string | null;
    } | null;
  }

  interface Props {
    allFeeds: FeedWithTTL[];
    errorFeeds: Feed[];
  }

  let { allFeeds = $bindable(), errorFeeds = $bindable() }: Props = $props();

  let feedSearchQuery = $state('');
  let retryingFeedId = $state<number | null>(null);
  let editingFeed = $state<Feed | null>(null);
  let showFeedEditor = $state(false);

  const filteredFeeds = $derived(
    feedSearchQuery.trim()
      ? allFeeds.filter((f) =>
          f.title.toLowerCase().includes(feedSearchQuery.toLowerCase())
        )
      : allFeeds
  );

  function editFeed(feed: Feed) {
    editingFeed = feed;
    showFeedEditor = true;
  }

  async function handleFeedSaved(updatedFeed: Feed) {
    errorFeeds = errorFeeds
      .map((f) => (f.id === updatedFeed.id ? updatedFeed : f))
      .filter((f) => f.last_error);

    try {
      const res = await fetch(`/api/feeds/${updatedFeed.id}`);
      if (res.ok) {
        const feedWithStats = await res.json();
        allFeeds = allFeeds.map((f) =>
          f.id === updatedFeed.id ? feedWithStats : f
        );
      }
    } catch {
      allFeeds = allFeeds.map((f) =>
        f.id === updatedFeed.id ? { ...f, ...updatedFeed } : f
      );
    }

    showFeedEditor = false;
    editingFeed = null;
  }

  function handleFeedEditCancel() {
    showFeedEditor = false;
    editingFeed = null;
  }

  async function retryFeed(feed: Feed) {
    retryingFeedId = feed.id;
    try {
      const res = await fetch(`/api/feeds/${feed.id}/refresh`, { method: 'POST' });
      if (res.ok) {
        const result = await res.json();
        if (result.error) {
          toast.error(`Still failing: ${result.error}`);
        } else {
          toast.success(`Refreshed ${feed.title}`);
          errorFeeds = errorFeeds.filter((f) => f.id !== feed.id);
        }
      }
    } catch {
      toast.error('Failed to retry feed');
    } finally {
      retryingFeedId = null;
    }
  }

  async function deleteFeed(feed: Feed) {
    if (!confirm(`Delete feed "${feed.title}"? This will also delete all its articles.`)) {
      return;
    }

    try {
      const res = await fetch(`/api/feeds/${feed.id}`, { method: 'DELETE' });
      if (res.ok) {
        toast.success(`Deleted ${feed.title}`);
        errorFeeds = errorFeeds.filter((f) => f.id !== feed.id);
        allFeeds = allFeeds.filter((f) => f.id !== feed.id);
      } else {
        const data = await res.json();
        toast.error(data.error || 'Failed to delete feed');
      }
    } catch (err) {
      console.error('Delete feed error:', err);
      toast.error('Failed to delete feed');
    }
  }
</script>

<section>
  <div class="mb-4">
    <h2 class="text-lg font-semibold">Feeds</h2>
    <p class="text-sm text-muted-foreground">
      {allFeeds.length} feed{allFeeds.length === 1 ? '' : 's'} - Edit feeds and adjust refresh intervals
    </p>
  </div>

  <!-- Feed Errors -->
  {#if errorFeeds.length > 0}
    <div class="mb-6">
      <div class="mb-3">
        <h3 class="text-sm font-semibold flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
          <AlertTriangle class="h-4 w-4" />
          {errorFeeds.length} feed{errorFeeds.length === 1 ? '' : 's'} with errors
        </h3>
      </div>

      <div class="space-y-2">
        {#each errorFeeds as feed (feed.id)}
          <div class="p-3 border rounded-lg border-yellow-500/30 bg-yellow-500/5">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm">{feed.title}</div>
                <div class="text-xs text-red-500 mt-1">{feed.last_error}</div>
              </div>
              <div class="flex gap-1 shrink-0">
                <Button
                  variant="outline"
                  size="icon"
                  class="h-7 w-7"
                  onclick={() => editFeed(feed)}
                  title="Edit feed"
                >
                  <Pencil class="h-3 w-3" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  class="h-7 w-7"
                  onclick={() => retryFeed(feed)}
                  disabled={retryingFeedId === feed.id}
                  title="Retry"
                >
                  <RefreshCw class="h-3 w-3 {retryingFeedId === feed.id ? 'animate-spin' : ''}" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  class="h-7 w-7 text-red-500 hover:text-red-600 hover:bg-red-500/10"
                  onclick={() => deleteFeed(feed)}
                  title="Delete feed"
                >
                  <X class="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- All Feeds -->
  <div class="mb-3">
    <Input
      type="search"
      placeholder="Search feeds..."
      bind:value={feedSearchQuery}
      class="max-w-sm"
    />
  </div>

  <div class="border rounded-lg divide-y">
    {#if filteredFeeds.length === 0}
      <div class="p-4 text-center text-muted-foreground">
        {feedSearchQuery ? 'No feeds match your search' : 'No feeds yet'}
      </div>
    {:else}
      {#each filteredFeeds as feed (feed.id)}
        <div class="p-3 flex items-center gap-3 hover:bg-muted/50 group">
          <div class="shrink-0">
            {#if feed.favicon_url}
              <img
                src={feed.favicon_url}
                alt=""
                class="h-5 w-5 rounded"
                onerror={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            {:else}
              <Rss class="h-5 w-5 text-muted-foreground" />
            {/if}
          </div>

          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">{feed.title}</div>
            <div class="flex items-center gap-3 text-xs text-muted-foreground">
              {#if feed.folder_name}
                <span>{feed.folder_name}</span>
              {/if}
              <span class="flex items-center gap-1">
                <Clock class="h-3 w-3" />
                {feed.effective_ttl_display}
                {#if feed.statistics?.ttl_override_minutes !== null && feed.statistics?.ttl_override_minutes !== undefined}
                  <span class="text-blue-500">(custom)</span>
                {/if}
              </span>
              {#if feed.statistics}
                <span>{feed.statistics.avg_articles_per_day.toFixed(1)}/day</span>
                <span>{Math.round(feed.statistics.read_rate * 100)}% read</span>
              {/if}
            </div>
          </div>

          <div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              onclick={() => editFeed(feed)}
              title="Edit feed"
            >
              <Pencil class="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              class="text-red-500 hover:text-red-600 hover:bg-red-500/10"
              onclick={() => deleteFeed(feed)}
              title="Delete feed"
            >
              <X class="h-4 w-4" />
            </Button>
          </div>
        </div>
      {/each}
    {/if}
  </div>
</section>

<FeedEditDialog
  bind:open={showFeedEditor}
  feed={editingFeed}
  onSave={handleFeedSaved}
  onCancel={handleFeedEditCancel}
/>
