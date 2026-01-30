<script lang="ts">
  import type { Folder, Feed } from '$lib/types';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import * as Dialog from '$lib/components/ui/dialog';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
  import { Pencil, X, Folder as FolderIcon, Check, ChevronDown, Plus } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';

  interface Props {
    folders: Folder[];
    feeds: Feed[];
  }

  let { folders = $bindable(), feeds = $bindable() }: Props = $props();

  // Add new folder state
  let isAddingFolder = $state(false);
  let newFolderName = $state('');

  // Edit state
  let editingFolderId = $state<number | null>(null);
  let editingName = $state('');

  // Delete dialog state
  let deleteDialogOpen = $state(false);
  let folderToDelete = $state<Folder | null>(null);
  let deleteAction = $state<'delete' | 'move'>('move');
  let targetFolderId = $state<number | null>(null);

  const folderFeeds = $derived((folderId: number) => feeds.filter((f) => f.folder_id === folderId));

  const otherFolders = $derived((excludeId: number) => folders.filter((f) => f.id !== excludeId));

  function startAddingFolder() {
    isAddingFolder = true;
    newFolderName = '';
  }

  function cancelAddingFolder() {
    isAddingFolder = false;
    newFolderName = '';
  }

  async function createFolder() {
    if (!newFolderName.trim()) {
      toast.error('Folder name cannot be empty');
      return;
    }

    try {
      const res = await fetch('/api/folders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newFolderName.trim() })
      });

      if (res.ok) {
        const created = await res.json();
        folders = [...folders, created];
        toast.success('Folder created');
        cancelAddingFolder();
      } else {
        const data = await res.json();
        toast.error(data.error || 'Failed to create folder');
      }
    } catch {
      toast.error('Failed to create folder');
    }
  }

  function handleNewFolderKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      createFolder();
    } else if (e.key === 'Escape') {
      cancelAddingFolder();
    }
  }

  function startEditing(folder: Folder) {
    editingFolderId = folder.id;
    editingName = folder.name;
  }

  function cancelEditing() {
    editingFolderId = null;
    editingName = '';
  }

  async function saveEdit(folder: Folder) {
    if (!editingName.trim()) {
      toast.error('Folder name cannot be empty');
      return;
    }

    try {
      const res = await fetch(`/api/folders/${folder.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editingName.trim() })
      });

      if (res.ok) {
        const updated = await res.json();
        folders = folders.map((f) => (f.id === folder.id ? updated : f));
        toast.success('Folder renamed');
        cancelEditing();
      } else {
        const data = await res.json();
        toast.error(data.error || 'Failed to rename folder');
      }
    } catch {
      toast.error('Failed to rename folder');
    }
  }

  function confirmDelete(folder: Folder) {
    folderToDelete = folder;
    deleteAction = 'move';
    targetFolderId = null;
    deleteDialogOpen = true;
  }

  async function executeDelete() {
    if (!folderToDelete) return;

    const feedsInFolder = folderFeeds(folderToDelete.id);

    try {
      let url = `/api/folders/${folderToDelete.id}`;

      if (feedsInFolder.length > 0) {
        if (deleteAction === 'delete') {
          url += '?action=delete';
        } else {
          url += `?action=move&target_folder_id=${targetFolderId ?? ''}`;
        }
      }

      const res = await fetch(url, { method: 'DELETE' });

      if (res.ok) {
        toast.success(`Deleted folder "${folderToDelete.name}"`);
        folders = folders.filter((f) => f.id !== folderToDelete!.id);

        if (deleteAction === 'delete') {
          // Remove feeds from local state
          feeds = feeds.filter((f) => f.folder_id !== folderToDelete!.id);
        } else {
          // Update feeds in local state
          feeds = feeds.map((f) =>
            f.folder_id === folderToDelete!.id ? { ...f, folder_id: targetFolderId } : f
          );
        }

        deleteDialogOpen = false;
        folderToDelete = null;
      } else {
        const data = await res.json();
        toast.error(data.error || 'Failed to delete folder');
      }
    } catch {
      toast.error('Failed to delete folder');
    }
  }

  function handleKeydown(e: KeyboardEvent, folder: Folder) {
    if (e.key === 'Enter') {
      saveEdit(folder);
    } else if (e.key === 'Escape') {
      cancelEditing();
    }
  }
</script>

<section>
  <div class="mb-4 flex items-center justify-between">
    <div>
      <h2 class="text-lg font-semibold">Folders</h2>
      <p class="text-sm text-muted-foreground">
        {folders.length} folder{folders.length === 1 ? '' : 's'} - Rename or delete folders
      </p>
    </div>
    {#if !isAddingFolder}
      <Button variant="outline" onclick={startAddingFolder}>
        <Plus class="h-4 w-4 mr-2" />
        Add Folder
      </Button>
    {/if}
  </div>

  <div class="border rounded-lg divide-y">
    {#if isAddingFolder}
      <div class="p-3 flex items-center gap-3 bg-muted/50">
        <FolderIcon class="h-5 w-5 text-muted-foreground shrink-0" />
        <Input
          type="text"
          placeholder="New folder name"
          bind:value={newFolderName}
          onkeydown={handleNewFolderKeydown}
          class="flex-1"
          autofocus
        />
        <Button variant="ghost" size="icon" onclick={createFolder} title="Create">
          <Check class="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onclick={cancelAddingFolder} title="Cancel">
          <X class="h-4 w-4" />
        </Button>
      </div>
    {/if}
    {#if folders.length === 0 && !isAddingFolder}
      <div class="p-4 text-center text-muted-foreground">No folders yet</div>
    {/if}
    {#if folders.length > 0}
      {#each folders as folder (folder.id)}
        {@const feedCount = folderFeeds(folder.id).length}
        <div class="p-3 flex items-center gap-3 hover:bg-muted/50 group">
          <FolderIcon class="h-5 w-5 text-muted-foreground shrink-0" />

          {#if editingFolderId === folder.id}
            <Input
              type="text"
              bind:value={editingName}
              onkeydown={(e) => handleKeydown(e, folder)}
              class="flex-1"
              autofocus
            />
            <Button variant="ghost" size="icon" onclick={() => saveEdit(folder)} title="Save">
              <Check class="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onclick={cancelEditing} title="Cancel">
              <X class="h-4 w-4" />
            </Button>
          {:else}
            <div class="flex-1 min-w-0">
              <div class="font-medium truncate">{folder.name}</div>
              <div class="text-xs text-muted-foreground">
                {feedCount} feed{feedCount === 1 ? '' : 's'}
              </div>
            </div>

            <div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                onclick={() => startEditing(folder)}
                title="Rename folder"
              >
                <Pencil class="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                class="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                onclick={() => confirmDelete(folder)}
                title="Delete folder"
              >
                <X class="h-4 w-4" />
              </Button>
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</section>

<Dialog.Root bind:open={deleteDialogOpen}>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>Delete Folder</Dialog.Title>
      <Dialog.Description>
        {#if folderToDelete}
          {@const feedCount = folderFeeds(folderToDelete.id).length}
          {#if feedCount > 0}
            This folder contains {feedCount} feed{feedCount === 1 ? '' : 's'}. What would you like
            to do with them?
          {:else}
            Are you sure you want to delete "{folderToDelete.name}"?
          {/if}
        {/if}
      </Dialog.Description>
    </Dialog.Header>

    {#if folderToDelete && folderFeeds(folderToDelete.id).length > 0}
      <div class="space-y-4 py-4">
        <div class="space-y-2">
          <label class="flex items-center gap-2">
            <input
              type="radio"
              name="deleteAction"
              value="move"
              checked={deleteAction === 'move'}
              onchange={() => (deleteAction = 'move')}
            />
            <span>Move feeds to another folder</span>
          </label>

          {#if deleteAction === 'move'}
            <div class="ml-6">
              <DropdownMenu.Root>
                <DropdownMenu.Trigger>
                  <Button variant="outline" class="w-full justify-between">
                    {targetFolderId === null
                      ? 'Uncategorized'
                      : (otherFolders(folderToDelete.id).find((f) => f.id === targetFolderId)
                          ?.name ?? 'Select folder')}
                    <ChevronDown class="h-4 w-4 ml-2" />
                  </Button>
                </DropdownMenu.Trigger>
                <DropdownMenu.Content>
                  <DropdownMenu.Item onclick={() => (targetFolderId = null)}>
                    <Check
                      class="h-4 w-4 mr-2 {targetFolderId === null ? 'opacity-100' : 'opacity-0'}"
                    />
                    Uncategorized
                  </DropdownMenu.Item>
                  {#each otherFolders(folderToDelete.id) as otherFolder}
                    <DropdownMenu.Item onclick={() => (targetFolderId = otherFolder.id)}>
                      <Check
                        class="h-4 w-4 mr-2 {targetFolderId === otherFolder.id
                          ? 'opacity-100'
                          : 'opacity-0'}"
                      />
                      {otherFolder.name}
                    </DropdownMenu.Item>
                  {/each}
                </DropdownMenu.Content>
              </DropdownMenu.Root>
            </div>
          {/if}
        </div>

        <label class="flex items-center gap-2">
          <input
            type="radio"
            name="deleteAction"
            value="delete"
            checked={deleteAction === 'delete'}
            onchange={() => (deleteAction = 'delete')}
          />
          <span class="text-red-500">Delete feeds and all their articles</span>
        </label>
      </div>
    {/if}

    <Dialog.Footer>
      <Button variant="outline" onclick={() => (deleteDialogOpen = false)}>Cancel</Button>
      <Button variant="destructive" onclick={executeDelete}>Delete Folder</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
