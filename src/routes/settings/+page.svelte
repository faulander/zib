<script lang="ts">
  import type { PageData } from './$types';
  import type { Filter, Feed } from '$lib/types';
  import { Button } from '$lib/components/ui/button';
  import { Switch } from '$lib/components/ui/switch';
  import { Separator } from '$lib/components/ui/separator';
  import FilterEditor from '$lib/components/filter-editor.svelte';
  import FeedEditDialog from '$lib/components/feed-edit-dialog.svelte';
  import { ArrowLeft, Plus, Pencil, Trash2, Upload, Download, AlertTriangle, RefreshCw, X } from '@lucide/svelte';
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { appStore } from '$lib/stores/app.svelte';

  let { data }: { data: PageData } = $props();

  let filters = $state<Filter[]>([]);
  let errorFeeds = $state<Feed[]>([]);
  let hideReadArticles = $state(false);
  let compactListView = $state(false);

  // Initialize from server data
  $effect(() => {
    filters = data.filters;
    errorFeeds = data.errorFeeds;
    hideReadArticles = data.settings.hideReadArticles;
    compactListView = data.settings.compactListView;
  });

  async function updateSetting(key: 'hideReadArticles' | 'compactListView', value: boolean) {
    try {
      const res = await fetch('/api/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value })
      });

      if (res.ok) {
        if (key === 'hideReadArticles') {
          appStore.setHideReadArticles(value);
        } else if (key === 'compactListView') {
          appStore.setCompactListView(value);
        }
      }
    } catch (err) {
      console.error('Failed to update setting:', err);
      toast.error('Failed to save setting');
    }
  }
  let editingFilter = $state<Filter | null>(null);
  let showEditor = $state(false);

  async function toggleFilter(filter: Filter) {
    const newValue = !filter.is_enabled;

    await fetch(`/api/filters/${filter.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_enabled: newValue })
    });

    filters = filters.map((f) => (f.id === filter.id ? { ...f, is_enabled: newValue } : f));
  }

  async function deleteFilter(filter: Filter) {
    if (!confirm(`Delete filter "${filter.name}"?`)) {
      return;
    }

    await fetch(`/api/filters/${filter.id}`, {
      method: 'DELETE'
    });

    filters = filters.filter((f) => f.id !== filter.id);
  }

  function editFilter(filter: Filter) {
    editingFilter = filter;
    showEditor = true;
  }

  function addFilter() {
    editingFilter = null;
    showEditor = true;
  }

  async function handleSave(savedFilter: Filter) {
    if (editingFilter) {
      // Update existing
      filters = filters.map((f) => (f.id === savedFilter.id ? savedFilter : f));
    } else {
      // Add new
      filters = [...filters, savedFilter];
    }
    showEditor = false;
    editingFilter = null;
  }

  function handleCancel() {
    showEditor = false;
    editingFilter = null;
  }

  let isImporting = $state(false);
  let retryingFeedId = $state<number | null>(null);
  let editingFeed = $state<Feed | null>(null);
  let showFeedEditor = $state(false);

  function editFeed(feed: Feed) {
    editingFeed = feed;
    showFeedEditor = true;
  }

  function handleFeedSaved(updatedFeed: Feed) {
    // If the feed was successfully saved and tested, it might not have errors anymore
    // Refresh the error feeds list
    errorFeeds = errorFeeds.map((f) =>
      f.id === updatedFeed.id ? updatedFeed : f
    ).filter((f) => f.last_error);
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
    } catch (err) {
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
      }
    } catch (err) {
      toast.error('Failed to delete feed');
    }
  }

  function handleImportClick() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.opml,.xml';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      isImporting = true;
      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await fetch('/api/import/opml', {
          method: 'POST',
          body: formData
        });

        if (res.ok) {
          const result = await res.json();
          toast.success(`Imported ${result.feedsImported || 0} feeds`);
        } else {
          toast.error('Import failed');
        }
      } catch (err) {
        console.error('Import failed:', err);
        toast.error('Import failed');
      } finally {
        isImporting = false;
      }
    };
    input.click();
  }
</script>

<div class="min-h-screen bg-background">
  <div class="max-w-2xl mx-auto p-6">
    <div class="flex items-center gap-4 mb-6">
      <Button variant="ghost" size="icon" onclick={() => goto('/')}>
        <ArrowLeft class="h-5 w-5" />
      </Button>
      <h1 class="text-2xl font-bold">Settings</h1>
    </div>

    <Separator class="mb-6" />

    <!-- General Settings Section -->
    <section class="mb-8">
      <div class="mb-4">
        <h2 class="text-lg font-semibold">General</h2>
        <p class="text-sm text-muted-foreground">Display preferences</p>
      </div>

      <div class="space-y-3">
        <div class="flex items-center justify-between p-4 border rounded-lg">
          <div>
            <div class="font-medium">Hide read articles</div>
            <div class="text-sm text-muted-foreground">
              Only show unread articles in the article list
            </div>
          </div>
          <Switch
            checked={hideReadArticles}
            onCheckedChange={(checked) => {
              hideReadArticles = checked;
              updateSetting('hideReadArticles', checked);
            }}
          />
        </div>

        <div class="flex items-center justify-between p-4 border rounded-lg">
          <div>
            <div class="font-medium">Compact list view</div>
            <div class="text-sm text-muted-foreground">
              Reduce vertical spacing in list view
            </div>
          </div>
          <Switch
            checked={compactListView}
            onCheckedChange={(checked) => {
              compactListView = checked;
              updateSetting('compactListView', checked);
            }}
          />
        </div>
      </div>
    </section>

    <Separator class="mb-6" />

    <!-- Import/Export Section -->
    <section class="mb-8">
      <div class="mb-4">
        <h2 class="text-lg font-semibold">Import / Export</h2>
        <p class="text-sm text-muted-foreground">Import or export feeds as OPML</p>
      </div>

      <div class="space-y-3">
        <div class="flex items-center gap-4 p-4 border rounded-lg">
          <div class="flex-1">
            <div class="font-medium">Import OPML</div>
            <div class="text-sm text-muted-foreground">
              Import feeds and folders from an OPML file
            </div>
          </div>
          <Button onclick={handleImportClick} disabled={isImporting}>
            <Upload class="h-4 w-4 mr-2" />
            {isImporting ? 'Importing...' : 'Import'}
          </Button>
        </div>

        <div class="flex items-center gap-4 p-4 border rounded-lg">
          <div class="flex-1">
            <div class="font-medium">Export OPML</div>
            <div class="text-sm text-muted-foreground">
              Download all feeds and folders as an OPML file
            </div>
          </div>
          <a href="/api/export/opml" download="feeds.opml">
            <Button variant="outline">
              <Download class="h-4 w-4 mr-2" />
              Export
            </Button>
          </a>
        </div>
      </div>
    </section>

    <Separator class="mb-6" />

    <!-- Feed Errors Section -->
    {#if errorFeeds.length > 0}
      <section class="mb-8">
        <div class="mb-4">
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <AlertTriangle class="h-5 w-5 text-yellow-500" />
            Feed Errors
          </h2>
          <p class="text-sm text-muted-foreground">
            {errorFeeds.length} feed{errorFeeds.length === 1 ? '' : 's'} with errors
          </p>
        </div>

        <div class="space-y-2">
          {#each errorFeeds as feed (feed.id)}
            <div class="p-4 border rounded-lg border-yellow-500/30 bg-yellow-500/5">
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <div class="font-medium">{feed.title}</div>
                  {#if feed.folder_name}
                    <div class="text-xs text-muted-foreground">{feed.folder_name}</div>
                  {/if}
                  <div class="text-sm text-red-500 mt-1">{feed.last_error}</div>
                  <div class="text-xs text-muted-foreground mt-1">
                    Failed {feed.error_count} time{feed.error_count === 1 ? '' : 's'}
                  </div>
                </div>
                <div class="flex gap-1 shrink-0">
                  <Button
                    variant="outline"
                    size="icon"
                    onclick={() => editFeed(feed)}
                    title="Edit feed"
                  >
                    <Pencil class="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    onclick={() => retryFeed(feed)}
                    disabled={retryingFeedId === feed.id}
                    title="Retry"
                  >
                    <RefreshCw class="h-4 w-4 {retryingFeedId === feed.id ? 'animate-spin' : ''}" />
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    class="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                    onclick={() => deleteFeed(feed)}
                    title="Delete feed"
                  >
                    <X class="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </section>

      <Separator class="mb-6" />
    {/if}

    <!-- Filters Section -->
    <section>
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold">Article Filters</h2>
          <p class="text-sm text-muted-foreground">Hide articles matching these rules</p>
        </div>
        <Button onclick={addFilter}>
          <Plus class="h-4 w-4 mr-2" />
          Add Filter
        </Button>
      </div>

      {#if filters.length === 0}
        <div class="text-center py-8 text-muted-foreground border rounded-lg">
          No filters defined yet. Create one to hide unwanted articles.
        </div>
      {:else}
        <div class="space-y-2">
          {#each filters as filter (filter.id)}
            <div class="flex items-center gap-3 p-3 border rounded-lg group hover:bg-muted/50">
              <Switch checked={filter.is_enabled} onCheckedChange={() => toggleFilter(filter)} />
              <div class="flex-1 min-w-0">
                <div class="font-medium">{filter.name}</div>
                <div class="text-sm text-muted-foreground truncate">{filter.rule}</div>
              </div>
              <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button variant="ghost" size="icon" onclick={() => editFilter(filter)}>
                  <Pencil class="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  class="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                  onclick={() => deleteFilter(filter)}
                >
                  <Trash2 class="h-4 w-4" />
                </Button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>
  </div>
</div>

<FilterEditor
  bind:open={showEditor}
  filter={editingFilter}
  onSave={handleSave}
  onCancel={handleCancel}
/>

<FeedEditDialog
  bind:open={showFeedEditor}
  feed={editingFeed}
  onSave={handleFeedSaved}
  onCancel={handleFeedEditCancel}
/>
