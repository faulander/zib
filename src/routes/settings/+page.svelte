<script lang="ts">
  import type { PageData } from './$types';
  import type { Filter, Feed, Folder } from '$lib/types';
  import { Button } from '$lib/components/ui/button';
  import {
    ArrowLeft,
    Settings,
    Share2,
    FolderInput,
    Rss,
    Filter as FilterIcon,
    FileText,
    Folder as FolderIcon
  } from '@lucide/svelte';
  import { goto } from '$app/navigation';
  import { cn } from '$lib/utils';

  // Settings components
  import GeneralSettings from '$lib/components/settings/general-settings.svelte';
  import SharingSettings from '$lib/components/settings/sharing-settings.svelte';
  import ImportExportSettings from '$lib/components/settings/import-export-settings.svelte';
  import FoldersSettings from '$lib/components/settings/folders-settings.svelte';
  import FeedsSettings from '$lib/components/settings/feeds-settings.svelte';
  import FiltersSettings from '$lib/components/settings/filters-settings.svelte';
  import LogsSettings from '$lib/components/settings/logs-settings.svelte';

  type SettingsSection =
    | 'general'
    | 'sharing'
    | 'import-export'
    | 'folders'
    | 'feeds'
    | 'filters'
    | 'logs';

  let activeSection = $state<SettingsSection>('general');

  const sections = [
    { id: 'general' as const, label: 'General', icon: Settings },
    { id: 'sharing' as const, label: 'Sharing', icon: Share2 },
    { id: 'import-export' as const, label: 'Import / Export', icon: FolderInput },
    { id: 'folders' as const, label: 'Folders', icon: FolderIcon },
    { id: 'feeds' as const, label: 'Feeds', icon: Rss },
    { id: 'filters' as const, label: 'Filters', icon: FilterIcon },
    { id: 'logs' as const, label: 'Logs', icon: FileText }
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

  // State from server data
  let filters = $state<Filter[]>([]);
  let errorFeeds = $state<Feed[]>([]);
  let allFeeds = $state<FeedWithTTL[]>([]);
  let allFolders = $state<Folder[]>([]);
  let logs = $state<LogEntry[]>([]);
  let logCount = $state(0);
  let hideReadArticles = $state(false);
  let compactListView = $state(false);
  let autoMarkAsRead = $state(false);
  let highlightColorLight = $state('#fef3c7');
  let highlightColorDark = $state('#422006');
  let similarityThreshold = $state(0.65);
  let fontSizeOffset = $state(0);
  let instapaperUsername = $state('');
  let instapaperPassword = $state('');

  // Initialize from server data
  $effect(() => {
    filters = data.filters;
    errorFeeds = data.errorFeeds;
    allFeeds = data.allFeeds as FeedWithTTL[];
    allFolders = data.allFolders;
    logs = data.logs as LogEntry[];
    logCount = data.logCount;
    hideReadArticles = data.settings.hideReadArticles;
    compactListView = data.settings.compactListView;
    autoMarkAsRead = data.settings.autoMarkAsRead;
    highlightColorLight = data.settings.highlightColorLight;
    highlightColorDark = data.settings.highlightColorDark;
    similarityThreshold = data.settings.similarityThreshold;
    fontSizeOffset = data.settings.fontSizeOffset;
    instapaperUsername = data.settings.instapaperUsername;
    instapaperPassword = data.settings.instapaperPassword;
  });
</script>

<div class="h-screen bg-background flex">
  <!-- Sidebar -->
  <aside class="w-56 border-r bg-muted/30 p-4 flex flex-col shrink-0">
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
    <div
      class={activeSection === 'feeds' ||
      activeSection === 'logs' ||
      activeSection === 'filters' ||
      activeSection === 'folders'
        ? ''
        : 'max-w-2xl'}
    >
      {#if activeSection === 'general'}
        <GeneralSettings
          bind:hideReadArticles
          bind:compactListView
          bind:autoMarkAsRead
          bind:highlightColorLight
          bind:highlightColorDark
          bind:similarityThreshold
          bind:fontSizeOffset
        />
      {:else if activeSection === 'sharing'}
        <SharingSettings bind:instapaperUsername bind:instapaperPassword />
      {:else if activeSection === 'import-export'}
        <ImportExportSettings />
      {:else if activeSection === 'folders'}
        <FoldersSettings bind:folders={allFolders} bind:feeds={allFeeds} />
      {:else if activeSection === 'feeds'}
        <FeedsSettings bind:allFeeds bind:errorFeeds />
      {:else if activeSection === 'filters'}
        <FiltersSettings bind:filters />
      {:else if activeSection === 'logs'}
        <LogsSettings bind:logs bind:logCount />
      {/if}
    </div>
  </main>
</div>
