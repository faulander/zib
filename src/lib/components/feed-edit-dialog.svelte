<script lang="ts">
  import type { Feed } from '$lib/types';
  import * as Dialog from '$lib/components/ui/dialog';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { toast } from 'svelte-sonner';
  import { CheckCircle, XCircle, Loader2 } from '@lucide/svelte';

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
  let testResult = $state<{ success: boolean; message: string } | null>(null);

  // Reset form when feed changes
  $effect(() => {
    if (feed) {
      title = feed.title;
      feedUrl = feed.feed_url;
      testResult = null;
    }
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

    if (!feed) return;

    if (!title.trim() || !feedUrl.trim()) {
      toast.error('Title and URL are required');
      return;
    }

    isSaving = true;

    try {
      const res = await fetch(`/api/feeds/${feed.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          feed_url: feedUrl.trim()
        })
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
    } catch (err) {
      toast.error('Failed to update feed');
    } finally {
      isSaving = false;
    }
  }

  function handleCancel() {
    onCancel?.();
    open = false;
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
