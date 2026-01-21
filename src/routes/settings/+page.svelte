<script lang="ts">
  import type { PageData } from './$types';
  import type { Filter, Feed } from '$lib/types';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Switch } from '$lib/components/ui/switch';
  import FilterEditor from '$lib/components/filter-editor.svelte';
  import FeedEditDialog from '$lib/components/feed-edit-dialog.svelte';
  import { ArrowLeft, Plus, Pencil, Trash2, Upload, Download, AlertTriangle, RefreshCw, X, Clock, Rss, FileText, Info, AlertCircle, Share2, Eye, EyeOff, Settings, Filter as FilterIcon, FolderInput } from '@lucide/svelte';
  import { Label } from '$lib/components/ui/label';
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { appStore } from '$lib/stores/app.svelte';
  import { cn } from '$lib/utils';

  type SettingsSection = 'general' | 'sharing' | 'import-export' | 'feeds' | 'filters' | 'logs';

  let activeSection = $state<SettingsSection>('general');

  const sections = [
    { id: 'general' as const, label: 'General', icon: Settings },
    { id: 'sharing' as const, label: 'Sharing', icon: Share2 },
    { id: 'import-export' as const, label: 'Import / Export', icon: FolderInput },
    { id: 'feeds' as const, label: 'Feeds', icon: Rss },
    { id: 'filters' as const, label: 'Filters', icon: FilterIcon },
    { id: 'logs' as const, label: 'Logs', icon: FileText },
  ];

  let { data }: { data: PageData } = $props();

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

  interface LogEntry {
    id: number;
    level: 'info' | 'warn' | 'error';
    category: string;
    message: string;
    details: string | null;
    created_at: string;
  }

  let filters = $state<Filter[]>([]);
  let errorFeeds = $state<Feed[]>([]);
  let allFeeds = $state<FeedWithTTL[]>([]);
  let logs = $state<LogEntry[]>([]);
  let logCount = $state(0);
  let hideReadArticles = $state(false);
  let compactListView = $state(false);
  let highlightColorLight = $state('#fef3c7');
  let highlightColorDark = $state('#422006');
  let feedSearchQuery = $state('');
  let logFilter = $state<'all' | 'info' | 'warn' | 'error'>('all');

  // Instapaper settings
  let instapaperUsername = $state('');
  let instapaperPassword = $state('');
  let showInstapaperPassword = $state(false);
  let isSavingInstapaper = $state(false);
  let isEditingInstapaper = $state(false);

  // Initialize from server data
  $effect(() => {
    filters = data.filters;
    errorFeeds = data.errorFeeds;
    allFeeds = data.allFeeds as FeedWithTTL[];
    logs = data.logs as LogEntry[];
    logCount = data.logCount;
    hideReadArticles = data.settings.hideReadArticles;
    compactListView = data.settings.compactListView;
    highlightColorLight = data.settings.highlightColorLight;
    highlightColorDark = data.settings.highlightColorDark;
    instapaperUsername = data.settings.instapaperUsername;
    instapaperPassword = data.settings.instapaperPassword;
  });

  const filteredLogs = $derived(
    logFilter === 'all' ? logs : logs.filter((l) => l.level === logFilter)
  );

  const filteredFeeds = $derived(
    feedSearchQuery.trim()
      ? allFeeds.filter((f) =>
          f.title.toLowerCase().includes(feedSearchQuery.toLowerCase())
        )
      : allFeeds
  );

  async function updateSetting(
    key: 'hideReadArticles' | 'compactListView' | 'highlightColorLight' | 'highlightColorDark',
    value: boolean | string
  ) {
    try {
      const res = await fetch('/api/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: value })
      });

      if (res.ok) {
        if (key === 'hideReadArticles') {
          appStore.setHideReadArticles(value as boolean);
        } else if (key === 'compactListView') {
          appStore.setCompactListView(value as boolean);
        } else if (key === 'highlightColorLight') {
          appStore.setHighlightColorLight(value as string);
        } else if (key === 'highlightColorDark') {
          appStore.setHighlightColorDark(value as string);
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
  let isClearingLogs = $state(false);

  async function clearLogs() {
    if (!confirm('Clear all logs?')) return;

    isClearingLogs = true;
    try {
      const res = await fetch('/api/logs', { method: 'DELETE' });
      if (res.ok) {
        logs = [];
        logCount = 0;
        toast.success('Logs cleared');
      }
    } catch {
      toast.error('Failed to clear logs');
    } finally {
      isClearingLogs = false;
    }
  }

  function formatLogTime(isoDate: string): string {
    const date = new Date(isoDate);
    return date.toLocaleString();
  }

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

  function editFeed(feed: Feed) {
    editingFeed = feed;
    showFeedEditor = true;
  }

  async function handleFeedSaved(updatedFeed: Feed) {
    // If the feed was successfully saved and tested, it might not have errors anymore
    // Refresh the error feeds list
    errorFeeds = errorFeeds.map((f) =>
      f.id === updatedFeed.id ? updatedFeed : f
    ).filter((f) => f.last_error);

    // Reload the feed with full stats from server
    try {
      const res = await fetch(`/api/feeds/${updatedFeed.id}`);
      if (res.ok) {
        const feedWithStats = await res.json();
        allFeeds = allFeeds.map((f) =>
          f.id === updatedFeed.id ? feedWithStats : f
        );
      }
    } catch {
      // Ignore errors, just update with what we have
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

<div class="min-h-screen bg-background flex">
  <!-- Sidebar -->
  <aside class="w-56 border-r bg-muted/30 p-4 flex flex-col">
    <div class="flex items-center gap-2 mb-6">
      <Button variant="ghost" size="icon" onclick={() => goto('/')}>
        <ArrowLeft class="h-5 w-5" />
      </Button>
      <h1 class="text-lg font-bold">Settings</h1>
    </div>

    <nav class="space-y-1">
      {#each sections as section}
        <button
          type="button"
          class={cn(
            'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors text-left',
            activeSection === section.id
              ? 'bg-primary text-primary-foreground'
              : 'hover:bg-muted text-muted-foreground hover:text-foreground'
          )}
          onclick={() => (activeSection = section.id)}
        >
          <section.icon class="h-4 w-4" />
          {section.label}
          {#if section.id === 'feeds' && errorFeeds.length > 0}
            <span class="ml-auto text-xs bg-yellow-500 text-yellow-950 rounded-full px-1.5">
              {errorFeeds.length}
            </span>
          {/if}
        </button>
      {/each}
    </nav>
  </aside>

  <!-- Main content -->
  <main class="flex-1 p-6 overflow-y-auto">
    <div class="max-w-2xl">

    {#if activeSection === 'general'}
    <!-- General Settings Section -->
    <section>
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

        <div class="p-4 border rounded-lg space-y-4">
          <div>
            <div class="font-medium">Highlight color</div>
            <div class="text-sm text-muted-foreground">
              Color used for hover states on articles
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label for="highlight-light" class="text-sm font-medium">Light mode</label>
              <div class="flex gap-2">
                <input
                  type="color"
                  id="highlight-light-picker"
                  value={highlightColorLight}
                  onchange={(e) => {
                    highlightColorLight = e.currentTarget.value;
                    updateSetting('highlightColorLight', e.currentTarget.value);
                  }}
                  class="w-10 h-10 rounded border cursor-pointer"
                />
                <Input
                  id="highlight-light"
                  type="text"
                  value={highlightColorLight}
                  oninput={(e) => {
                    const val = e.currentTarget.value;
                    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                      highlightColorLight = val;
                      updateSetting('highlightColorLight', val);
                    } else {
                      highlightColorLight = val;
                    }
                  }}
                  onblur={(e) => {
                    const val = e.currentTarget.value;
                    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                      updateSetting('highlightColorLight', val);
                    }
                  }}
                  placeholder="#fef3c7"
                  class="flex-1 font-mono"
                />
              </div>
            </div>

            <div class="space-y-2">
              <label for="highlight-dark" class="text-sm font-medium">Dark mode</label>
              <div class="flex gap-2">
                <input
                  type="color"
                  id="highlight-dark-picker"
                  value={highlightColorDark}
                  onchange={(e) => {
                    highlightColorDark = e.currentTarget.value;
                    updateSetting('highlightColorDark', e.currentTarget.value);
                  }}
                  class="w-10 h-10 rounded border cursor-pointer"
                />
                <Input
                  id="highlight-dark"
                  type="text"
                  value={highlightColorDark}
                  oninput={(e) => {
                    const val = e.currentTarget.value;
                    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                      highlightColorDark = val;
                      updateSetting('highlightColorDark', val);
                    } else {
                      highlightColorDark = val;
                    }
                  }}
                  onblur={(e) => {
                    const val = e.currentTarget.value;
                    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                      updateSetting('highlightColorDark', val);
                    }
                  }}
                  placeholder="#422006"
                  class="flex-1 font-mono"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <Separator class="mb-6" />

    <!-- Sharing Section -->
    <section class="mb-8">
      <div class="mb-4">
        <h2 class="text-lg font-semibold flex items-center gap-2">
          <Share2 class="h-5 w-5" />
          Sharing
        </h2>
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
                <Button
                  variant="outline"
                  onclick={() => {
                    isEditingInstapaper = false;
                    // Reset to saved values
                    instapaperUsername = data.settings.instapaperUsername;
                    instapaperPassword = data.settings.instapaperPassword;
                  }}
                >
                  Cancel
                </Button>
              {/if}
            </div>
          </div>
        {/if}
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

    <!-- Manage Feeds Section -->
    <section class="mb-8">
      <div class="mb-4">
        <h2 class="text-lg font-semibold flex items-center gap-2">
          <Rss class="h-5 w-5" />
          Manage Feeds
        </h2>
        <p class="text-sm text-muted-foreground">
          {allFeeds.length} feed{allFeeds.length === 1 ? '' : 's'} - Edit feeds and adjust refresh intervals
        </p>
      </div>

      <div class="mb-3">
        <Input
          type="search"
          placeholder="Search feeds..."
          bind:value={feedSearchQuery}
          class="max-w-sm"
        />
      </div>

      <div class="border rounded-lg divide-y max-h-96 overflow-y-auto">
        {#if filteredFeeds.length === 0}
          <div class="p-4 text-center text-muted-foreground">
            {feedSearchQuery ? 'No feeds match your search' : 'No feeds yet'}
          </div>
        {:else}
          {#each filteredFeeds as feed (feed.id)}
            <div class="p-3 flex items-center gap-3 hover:bg-muted/50 group">
              <!-- Feed icon -->
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

              <!-- Feed info -->
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

              <!-- Actions -->
              <div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="icon"
                  onclick={() => editFeed(feed)}
                  title="Edit feed"
                >
                  <Pencil class="h-4 w-4" />
                </Button>
              </div>
            </div>
          {/each}
        {/if}
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

    <Separator class="mb-6" />

    <!-- Logs Section -->
    <section class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <FileText class="h-5 w-5" />
            Logs
          </h2>
          <p class="text-sm text-muted-foreground">
            {logCount} log entries
          </p>
        </div>
        <div class="flex gap-2">
          <a href="/api/logs/export" download>
            <Button variant="outline" size="sm">
              <Download class="h-4 w-4 mr-2" />
              Download
            </Button>
          </a>
          <Button
            variant="outline"
            size="sm"
            onclick={clearLogs}
            disabled={isClearingLogs || logCount === 0}
          >
            <Trash2 class="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      <!-- Log filter tabs -->
      <div class="flex gap-1 mb-3">
        <Button
          variant={logFilter === 'all' ? 'secondary' : 'ghost'}
          size="sm"
          onclick={() => (logFilter = 'all')}
        >
          All
        </Button>
        <Button
          variant={logFilter === 'info' ? 'secondary' : 'ghost'}
          size="sm"
          onclick={() => (logFilter = 'info')}
        >
          <Info class="h-3 w-3 mr-1" />
          Info
        </Button>
        <Button
          variant={logFilter === 'warn' ? 'secondary' : 'ghost'}
          size="sm"
          onclick={() => (logFilter = 'warn')}
        >
          <AlertTriangle class="h-3 w-3 mr-1" />
          Warn
        </Button>
        <Button
          variant={logFilter === 'error' ? 'secondary' : 'ghost'}
          size="sm"
          onclick={() => (logFilter = 'error')}
        >
          <AlertCircle class="h-3 w-3 mr-1" />
          Error
        </Button>
      </div>

      <div class="border rounded-lg max-h-80 overflow-y-auto">
        {#if filteredLogs.length === 0}
          <div class="p-4 text-center text-muted-foreground">
            No logs to display
          </div>
        {:else}
          <div class="divide-y text-sm font-mono">
            {#each filteredLogs as log (log.id)}
              <div class="p-2 hover:bg-muted/50 {log.level === 'error' ? 'bg-red-500/5' : log.level === 'warn' ? 'bg-yellow-500/5' : ''}">
                <div class="flex items-start gap-2">
                  <span class="shrink-0 w-4">
                    {#if log.level === 'error'}
                      <AlertCircle class="h-4 w-4 text-red-500" />
                    {:else if log.level === 'warn'}
                      <AlertTriangle class="h-4 w-4 text-yellow-500" />
                    {:else}
                      <Info class="h-4 w-4 text-blue-500" />
                    {/if}
                  </span>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{formatLogTime(log.created_at)}</span>
                      <span class="px-1.5 py-0.5 rounded bg-muted">{log.category}</span>
                    </div>
                    <div class="mt-0.5 break-words">{log.message}</div>
                    {#if log.details}
                      <div class="mt-1 text-xs text-muted-foreground break-all">{log.details}</div>
                    {/if}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
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
