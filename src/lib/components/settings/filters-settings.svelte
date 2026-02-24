<script lang="ts">
  import type { Filter } from '$lib/types';
  import { Button } from '$lib/components/ui/button';
  import { Switch } from '$lib/components/ui/switch';
  import { Plus, Pencil, Trash2, ChevronDown, ChevronRight } from '@lucide/svelte';
  import Spinner from '$lib/components/spinner.svelte';
  import FilterEditor from '$lib/components/filter-editor.svelte';

  interface MatchedArticle {
    id: number;
    title: string;
    feed_title: string;
    published_at: string | null;
  }

  interface Props {
    filters: Filter[];
  }

  let { filters = $bindable() }: Props = $props();

  let editingFilter = $state<Filter | null>(null);
  let showEditor = $state(false);
  let expandedFilterId = $state<number | null>(null);
  let matchedArticles = $state<Record<number, MatchedArticle[]>>({});
  let loadingMatches = $state<number | null>(null);

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

  async function toggleExpanded(filter: Filter) {
    if (expandedFilterId === filter.id) {
      expandedFilterId = null;
      return;
    }

    expandedFilterId = filter.id;

    if (!matchedArticles[filter.id]) {
      loadingMatches = filter.id;
      try {
        const res = await fetch(`/api/filters/${filter.id}/matches?limit=10`);
        const data = await res.json();
        matchedArticles = { ...matchedArticles, [filter.id]: data };
      } catch {
        matchedArticles = { ...matchedArticles, [filter.id]: [] };
      } finally {
        loadingMatches = null;
      }
    }
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  }

  async function handleSave(savedFilter: Filter) {
    if (editingFilter) {
      filters = filters.map((f) => (f.id === savedFilter.id ? savedFilter : f));
      // Clear cached matches since the rule may have changed
      const { [savedFilter.id]: _, ...rest } = matchedArticles;
      matchedArticles = rest;
    } else {
      filters = [...filters, savedFilter];
    }
    showEditor = false;
    editingFilter = null;
  }

  function handleCancel() {
    showEditor = false;
    editingFilter = null;
  }
</script>

<section>
  <div class="flex items-center justify-between mb-4">
    <div>
      <h2 class="text-lg font-semibold">Filters</h2>
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
        <div class="border rounded-lg">
          <div class="flex items-center gap-3 p-3 group hover:bg-muted/50">
            <button
              class="text-muted-foreground hover:text-foreground transition-colors"
              onclick={() => toggleExpanded(filter)}
              aria-label="Show matched articles"
            >
              {#if expandedFilterId === filter.id}
                <ChevronDown class="h-4 w-4" />
              {:else}
                <ChevronRight class="h-4 w-4" />
              {/if}
            </button>
            <Switch checked={filter.is_enabled} onCheckedChange={() => toggleFilter(filter)} />
            <button class="flex-1 min-w-0 text-left" onclick={() => toggleExpanded(filter)}>
              <div class="font-medium">{filter.name}</div>
              <div class="text-sm text-muted-foreground truncate">{filter.rule}</div>
            </button>
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

          {#if expandedFilterId === filter.id}
            <div class="border-t px-3 py-2">
              {#if loadingMatches === filter.id}
                <div class="flex items-center gap-2 py-2 text-sm text-muted-foreground">
                  <Spinner class="h-4 w-4" />
                  Loading matches...
                </div>
              {:else if matchedArticles[filter.id]?.length}
                <div class="text-xs font-medium text-muted-foreground mb-2">
                  Last {matchedArticles[filter.id].length} matched articles
                </div>
                <div class="space-y-1">
                  {#each matchedArticles[filter.id] as article (article.id)}
                    <div class="text-sm py-1 flex items-baseline gap-2">
                      <span class="truncate flex-1">{article.title}</span>
                      <span class="text-xs text-muted-foreground whitespace-nowrap shrink-0">
                        {article.feed_title}
                      </span>
                      {#if article.published_at}
                        <span class="text-xs text-muted-foreground whitespace-nowrap shrink-0">
                          {formatDate(article.published_at)}
                        </span>
                      {/if}
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="text-sm text-muted-foreground py-2">No matching articles found.</div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</section>

<FilterEditor
  bind:open={showEditor}
  filter={editingFilter}
  onSave={handleSave}
  onCancel={handleCancel}
/>
