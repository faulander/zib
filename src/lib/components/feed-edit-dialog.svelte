<script lang="ts">
  import type { Feed } from '$lib/types';
  import * as Dialog from '$lib/components/ui/dialog';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { Switch } from '$lib/components/ui/switch';
  import { Separator } from '$lib/components/ui/separator';
  import { toast } from 'svelte-sonner';
  import { CheckCircle, XCircle, Loader2, Clock } from '@lucide/svelte';

  interface FeedStatistics {
    avg_articles_per_day: number;
    articles_last_7_days: number;
    articles_last_30_days: number;
    read_rate: number;
    calculated_ttl_minutes: number | null;
    ttl_override_minutes: number | null;
    ttl_calculation_reason: string | null;
    last_calculated_at: string | null;
  }

  interface FeedWithStats extends Feed {
    statistics: FeedStatistics | null;
    effective_ttl_minutes: number;
    effective_ttl_display: string;
  }

  interface Props {
    open: boolean;
    feed: Feed | null;
    onSave?: (feed: Feed) => void;
    onCancel?: () => void;
  }

  let { open = $bindable(), feed, onSave, onCancel }: Props = $props();

  let title = $state('');
  let feedUrl = $state('');
  let isSaving = $state(false);
  let isTesting = $state(false);
  let isLoading = $state(false);
  let testResult = $state<{ success: boolean; message: string } | null>(null);

  // TTL override state
  let useCustomTTL = $state(false);
  let customTTL = $state<number>(30);
  let feedStats = $state<FeedWithStats | null>(null);

  // Reset form and load feed data when feed changes
  $effect(() => {
    if (feed && open) {
      title = feed.title;
      feedUrl = feed.feed_url;
      testResult = null;
      loadFeedWithStats(feed.id);
    }
  });

  async function loadFeedWithStats(feedId: number) {
    isLoading = true;
    try {
      const res = await fetch(`/api/feeds/${feedId}`);
      if (res.ok) {
        feedStats = await res.json();
        // Initialize TTL override state
        if (feedStats?.statistics?.ttl_override_minutes !== null && feedStats?.statistics?.ttl_override_minutes !== undefined) {
          useCustomTTL = true;
          customTTL = feedStats.statistics.ttl_override_minutes;
        } else {
          useCustomTTL = false;
          customTTL = feedStats?.effective_ttl_minutes ?? 30;
        }
      }
    } catch {
      // Ignore errors loading stats
    } finally {
      isLoading = false;
    }
  }

  async function testFeedUrl() {
    if (!feedUrl.trim()) {
      toast.error('Please enter a feed URL');
      return;
    }

    isTesting = true;
    testResult = null;

    try {
      const res = await fetch('/api/feeds/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: feedUrl.trim() })
      });

      const data = await res.json();

      if (data.success) {
        testResult = {
          success: true,
          message: `Found "${data.title}" with ${data.itemCount} items`
        };
      } else {
        testResult = {
          success: false,
          message: data.error || 'Failed to fetch feed'
        };
      }
    } catch {
      testResult = {
        success: false,
        message: 'Failed to test feed'
      };
    } finally {
      isTesting = false;
    }
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();

    if (!feed) return;

    if (!title.trim() || !feedUrl.trim()) {
      toast.error('Title and URL are required');
      return;
    }

    isSaving = true;

    try {
      const payload: Record<string, unknown> = {
        title: title.trim(),
        feed_url: feedUrl.trim()
      };

      // Include TTL override if custom is enabled
      if (useCustomTTL) {
        payload.ttl_override_minutes = customTTL;
      } else if (feedStats?.statistics?.ttl_override_minutes !== null) {
        // Clear override if it was set but now disabled
        payload.ttl_override_minutes = null;
      }

      const res = await fetch(`/api/feeds/${feed.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const data = await res.json();
        toast.error(data.error || 'Failed to update feed');
        return;
      }

      const updatedFeed = await res.json();
      toast.success('Feed updated');
      onSave?.(updatedFeed);
      open = false;
    } catch {
      toast.error('Failed to update feed');
    } finally {
      isSaving = false;
    }
  }

  function handleCancel() {
    onCancel?.();
    open = false;
  }

  function formatReadRate(rate: number): string {
    return `${Math.round(rate * 100)}%`;
  }
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title>Edit Feed</Dialog.Title>
      <Dialog.Description>
        Update the feed details. Test the URL to verify it works.
      </Dialog.Description>
    </Dialog.Header>

    <form onsubmit={handleSubmit} class="space-y-4">
      <div class="space-y-2">
        <Label for="feed-title">Title</Label>
        <Input
          id="feed-title"
          type="text"
          placeholder="Feed title"
          bind:value={title}
          required
        />
      </div>

      <div class="space-y-2">
        <Label for="feed-url">Feed URL</Label>
        <div class="flex gap-2">
          <Input
            id="feed-url"
            type="url"
            placeholder="https://example.com/feed.xml"
            bind:value={feedUrl}
            required
            class="flex-1"
          />
          <Button
            type="button"
            variant="outline"
            onclick={testFeedUrl}
            disabled={isTesting}
          >
            {#if isTesting}
              <Loader2 class="h-4 w-4 animate-spin" />
            {:else}
              Test
            {/if}
          </Button>
        </div>
      </div>

      {#if testResult}
        <div
          class="flex items-start gap-2 p-3 rounded-md text-sm {testResult.success
            ? 'bg-green-500/10 text-green-600 dark:text-green-400'
            : 'bg-red-500/10 text-red-600 dark:text-red-400'}"
        >
          {#if testResult.success}
            <CheckCircle class="h-4 w-4 mt-0.5 shrink-0" />
          {:else}
            <XCircle class="h-4 w-4 mt-0.5 shrink-0" />
          {/if}
          <span>{testResult.message}</span>
        </div>
      {/if}

      {#if feed?.last_error}
        <div class="p-3 rounded-md bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 text-sm">
          <div class="font-medium">Last error:</div>
          <div>{feed.last_error}</div>
        </div>
      {/if}

      <Separator />

      <!-- Refresh Settings -->
      <div class="space-y-3">
        <div class="flex items-center gap-2">
          <Clock class="h-4 w-4 text-muted-foreground" />
          <Label class="font-medium">Refresh Settings</Label>
        </div>

        {#if isLoading}
          <div class="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 class="h-4 w-4 animate-spin" />
            Loading statistics...
          </div>
        {:else if feedStats}
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-muted-foreground">Current refresh interval:</span>
              <span class="font-medium">{feedStats.effective_ttl_display}</span>
            </div>

            {#if feedStats.statistics}
              <div class="flex justify-between">
                <span class="text-muted-foreground">Articles/day (avg):</span>
                <span>{feedStats.statistics.avg_articles_per_day.toFixed(1)}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted-foreground">Read rate:</span>
                <span>{formatReadRate(feedStats.statistics.read_rate)}</span>
              </div>
              {#if feedStats.statistics.ttl_calculation_reason}
                <div class="text-xs text-muted-foreground">
                  Based on: {feedStats.statistics.ttl_calculation_reason}
                </div>
              {/if}
            {:else}
              <div class="text-xs text-muted-foreground">
                Statistics will be calculated after more articles are fetched.
              </div>
            {/if}
          </div>

          <div class="flex items-center gap-2 pt-2">
            <Switch
              id="use-custom-ttl"
              checked={useCustomTTL}
              onCheckedChange={(checked) => {
                useCustomTTL = checked;
                if (checked && feedStats) {
                  customTTL = feedStats.effective_ttl_minutes;
                }
              }}
            />
            <Label for="use-custom-ttl" class="text-sm">Override with custom interval</Label>
          </div>

          {#if useCustomTTL}
            <div class="flex items-center gap-2 pl-8">
              <Input
                type="number"
                min="5"
                max="1440"
                bind:value={customTTL}
                class="w-24"
              />
              <span class="text-sm text-muted-foreground">minutes (5 min - 24 hr)</span>
            </div>
          {/if}
        {/if}
      </div>

      <Dialog.Footer>
        <Button type="button" variant="outline" onclick={handleCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save'}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
