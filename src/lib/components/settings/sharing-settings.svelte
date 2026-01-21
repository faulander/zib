<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { Pencil, Trash2, Eye, EyeOff } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';

  interface Props {
    instapaperUsername: string;
    instapaperPassword: string;
  }

  let {
    instapaperUsername = $bindable(),
    instapaperPassword = $bindable()
  }: Props = $props();

  let showInstapaperPassword = $state(false);
  let isSavingInstapaper = $state(false);
  let isEditingInstapaper = $state(false);

  // Store original values for cancel
  let originalUsername = $state('');
  let originalPassword = $state('');

  $effect(() => {
    originalUsername = instapaperUsername;
    originalPassword = instapaperPassword;
  });

  async function saveInstapaperSettings() {
    isSavingInstapaper = true;
    try {
      const res = await fetch('/api/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instapaperUsername,
          instapaperPassword
        })
      });

      if (res.ok) {
        toast.success('Instapaper settings saved');
        isEditingInstapaper = false;
        originalUsername = instapaperUsername;
        originalPassword = instapaperPassword;
      } else {
        toast.error('Failed to save settings');
      }
    } catch {
      toast.error('Failed to save settings');
    } finally {
      isSavingInstapaper = false;
    }
  }

  async function removeInstapaperSettings() {
    if (!confirm('Remove Instapaper account?')) return;

    isSavingInstapaper = true;
    try {
      const res = await fetch('/api/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instapaperUsername: '',
          instapaperPassword: ''
        })
      });

      if (res.ok) {
        instapaperUsername = '';
        instapaperPassword = '';
        originalUsername = '';
        originalPassword = '';
        toast.success('Instapaper account removed');
      } else {
        toast.error('Failed to remove account');
      }
    } catch {
      toast.error('Failed to remove account');
    } finally {
      isSavingInstapaper = false;
    }
  }

  function cancelEdit() {
    isEditingInstapaper = false;
    instapaperUsername = originalUsername;
    instapaperPassword = originalPassword;
  }
</script>

<section>
  <div class="mb-4">
    <h2 class="text-lg font-semibold">Sharing</h2>
    <p class="text-sm text-muted-foreground">Save articles to read-later services</p>
  </div>

  <div class="p-4 border rounded-lg space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <div class="font-medium">Instapaper</div>
        <div class="text-sm text-muted-foreground">
          Save articles to your Instapaper account
        </div>
      </div>
      {#if instapaperUsername && !isEditingInstapaper}
        <div class="flex items-center gap-2">
          <span class="flex items-center gap-1.5 text-sm text-green-600 dark:text-green-400">
            <span class="h-2 w-2 rounded-full bg-green-500"></span>
            Connected
          </span>
        </div>
      {/if}
    </div>

    {#if instapaperUsername && !isEditingInstapaper}
      <!-- Connected state -->
      <div class="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
        <div class="text-sm">
          <span class="text-muted-foreground">Account:</span>
          <span class="ml-1 font-medium">{instapaperUsername}</span>
        </div>
        <div class="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onclick={() => (isEditingInstapaper = true)}
          >
            <Pencil class="h-3 w-3 mr-1" />
            Edit
          </Button>
          <Button
            variant="outline"
            size="sm"
            onclick={removeInstapaperSettings}
            disabled={isSavingInstapaper}
            class="text-red-500 hover:text-red-600 hover:bg-red-500/10"
          >
            <Trash2 class="h-3 w-3 mr-1" />
            Remove
          </Button>
        </div>
      </div>
    {:else}
      <!-- Edit/Add state -->
      <div class="space-y-3">
        <div class="space-y-1.5">
          <Label for="instapaper-username">Username or Email</Label>
          <Input
            id="instapaper-username"
            type="text"
            placeholder="your@email.com"
            bind:value={instapaperUsername}
          />
        </div>

        <div class="space-y-1.5">
          <Label for="instapaper-password">Password (optional)</Label>
          <div class="relative">
            <Input
              id="instapaper-password"
              type={showInstapaperPassword ? 'text' : 'password'}
              placeholder="Leave empty if not set"
              bind:value={instapaperPassword}
              class="pr-10"
            />
            <button
              type="button"
              class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
              onclick={() => (showInstapaperPassword = !showInstapaperPassword)}
            >
              {#if showInstapaperPassword}
                <EyeOff class="h-4 w-4" />
              {:else}
                <Eye class="h-4 w-4" />
              {/if}
            </button>
          </div>
          <p class="text-xs text-muted-foreground">
            Only needed if you set a password in Instapaper
          </p>
        </div>

        <div class="flex gap-2">
          <Button
            onclick={saveInstapaperSettings}
            disabled={isSavingInstapaper || !instapaperUsername}
          >
            {isSavingInstapaper ? 'Saving...' : 'Save'}
          </Button>
          {#if isEditingInstapaper}
            <Button variant="outline" onclick={cancelEdit}>
              Cancel
            </Button>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</section>
