<script lang="ts">
  import { appStore } from '$lib/stores/app.svelte';
  import * as Dialog from '$lib/components/ui/dialog';

  function handleOpenChange(open: boolean) {
    appStore.setKeyboardHelpOpen(open);
  }

  const shortcuts = [
    {
      group: 'Navigation',
      items: [
        { keys: ['j', '↓'], description: 'Move down' },
        { keys: ['k', '↑'], description: 'Move up' },
        { keys: ['Enter', 'o'], description: 'Open article' },
        { keys: ['Escape'], description: 'Close / clear focus' }
      ]
    },
    {
      group: 'Actions',
      items: [
        { keys: ['s'], description: 'Toggle star' },
        { keys: ['m'], description: 'Toggle read/unread' },
        { keys: ['v'], description: 'Open in new tab' },
        { keys: ['r'], description: 'Refresh' }
      ]
    },
    {
      group: 'Go to',
      items: [
        { keys: ['g', 'a'], description: 'All Items' },
        { keys: ['g', 's'], description: 'Starred' }
      ]
    },
    {
      group: 'Other',
      items: [
        { keys: ['?'], description: 'Show shortcuts' },
        { keys: ['f'], description: 'Focus search' }
      ]
    }
  ];
</script>

<Dialog.Root open={appStore.keyboardHelpOpen} onOpenChange={handleOpenChange}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>Keyboard Shortcuts</Dialog.Title>
    </Dialog.Header>
    <div class="grid gap-4">
      {#each shortcuts as section (section.group)}
        <div>
          <h4 class="text-sm font-semibold text-muted-foreground mb-2">{section.group}</h4>
          <div class="space-y-1.5">
            {#each section.items as shortcut (shortcut.description)}
              <div class="flex items-center justify-between">
                <span class="text-sm">{shortcut.description}</span>
                <div class="flex items-center gap-1">
                  {#each shortcut.keys as key (key)}
                    {#if shortcut.keys.indexOf(key) > 0}
                      <span class="text-xs text-muted-foreground">then</span>
                    {/if}
                    <kbd class="px-1.5 py-0.5 bg-muted rounded text-xs font-mono border">{key}</kbd>
                  {/each}
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </Dialog.Content>
</Dialog.Root>
