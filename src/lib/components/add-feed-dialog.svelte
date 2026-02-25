<script lang="ts">
  import * as Dialog from '$lib/components/ui/dialog';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { appStore } from '$lib/stores/app.svelte';
  import { toast } from 'svelte-sonner';
  import { CheckCircle, XCircle, Loader2 } from '@lucide/svelte';

  interface Props {
    open: boolean;
  }

  let { open = $bindable() }: Props = $props();

  let feedUrl = $state('');
  let folderId = $state<number | null>(null);
  let isSubmitting = $state(false);
  let isTesting = $state(false);
  let testResult = $state<{ success: boolean; title?: string; message: string } | null>(null);
  let discoveredFeeds = $state<{ url: string; title: string; type: string }[]>([]);

  // Reset test result when URL changes
  $effect(() => {
    feedUrl;
    testResult = null;
    discoveredFeeds = [];
  });

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

      if (data.discovered_feeds && data.discovered_feeds.length > 0) {
        discoveredFeeds = data.discovered_feeds;
        testResult = {
          success: false,
          message: data.message || `Found ${data.discovered_feeds.length} feed(s)`
        };
      } else if (data.success) {
        discoveredFeeds = [];
        testResult = {
          success: true,
          title: data.title,
          message: `Found "${data.title}" with ${data.itemCount} items`
        };
      } else {
        discoveredFeeds = [];
        testResult = {
          success: false,
          message: data.error || 'Failed to fetch feed'
        };
      }
    } catch (err) {
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

    if (!feedUrl.trim()) {
      toast.error('Please enter a feed URL');
      return;
    }

    // Test first if not already tested successfully
    if (!testResult?.success) {
      await testFeedUrl();
      if (!testResult?.success) {
        return;
      }
    }

    isSubmitting = true;

    try {
      const res = await fetch('/api/feeds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          feed_url: feedUrl.trim(),
          folder_id: folderId
        })
      });

      const data = await res.json();

      if (!res.ok) {
        toast.error(data.error || 'Failed to add feed');
        return;
      }

      toast.success('Feed added successfully');
      feedUrl = '';
      folderId = null;
      testResult = null;
      discoveredFeeds = [];
      open = false;

      // Trigger data reload
      window.dispatchEvent(new CustomEvent('reload-data'));
    } catch (err) {
      toast.error('Failed to add feed');
    } finally {
      isSubmitting = false;
    }
  }
</script>

<Dialog.Root bind:open>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>Add Feed</Dialog.Title>
      <Dialog.Description>
        Enter the URL of the RSS or Atom feed you want to subscribe to.
      </Dialog.Description>
    </Dialog.Header>

    <form onsubmit={handleSubmit} class="space-y-4">
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

      {#if discoveredFeeds.length > 0}
        <div class="space-y-2">
          <p class="text-sm font-medium">Discovered feeds:</p>
          {#each discoveredFeeds as feed (feed.url)}
            <button
              type="button"
              class="w-full text-left p-3 rounded-md border hover:bg-muted transition-colors"
              onclick={() => {
                feedUrl = feed.url;
                discoveredFeeds = [];
                testResult = null;
                testFeedUrl();
              }}
            >
              <div class="font-medium text-sm">{feed.title}</div>
              <div class="text-xs text-muted-foreground truncate">{feed.url}</div>
            </button>
          {/each}
        </div>
      {/if}

      <div class="space-y-2">
        <Label for="folder">Folder (optional)</Label>
        <select
          id="folder"
          class="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
          bind:value={folderId}
        >
          <option value={null}>No folder</option>
          {#each appStore.folders as folder (folder.id)}
            <option value={folder.id}>{folder.name}</option>
          {/each}
        </select>
      </div>

      <Dialog.Footer>
        <Button type="button" variant="outline" onclick={() => (open = false)}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting || isTesting}>
          {isSubmitting ? 'Adding...' : 'Add Feed'}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
