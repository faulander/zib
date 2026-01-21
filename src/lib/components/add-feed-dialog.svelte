<script lang="ts">
  import * as Dialog from '$lib/components/ui/dialog';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { appStore } from '$lib/stores/app.svelte';
  import { toast } from 'svelte-sonner';

  interface Props {
    open: boolean;
  }

  let { open = $bindable() }: Props = $props();

  let feedUrl = $state('');
  let folderId = $state<number | null>(null);
  let isSubmitting = $state(false);

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();

    if (!feedUrl.trim()) {
      toast.error('Please enter a feed URL');
      return;
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
        <Input
          id="feed-url"
          type="url"
          placeholder="https://example.com/feed.xml"
          bind:value={feedUrl}
          required
        />
      </div>

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
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Adding...' : 'Add Feed'}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
