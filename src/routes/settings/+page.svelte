<script lang="ts">
  import type { PageData } from './$types';
  import type { Filter } from '$lib/types';
  import { Button } from '$lib/components/ui/button';
  import { Switch } from '$lib/components/ui/switch';
  import { Separator } from '$lib/components/ui/separator';
  import FilterEditor from '$lib/components/filter-editor.svelte';
  import { ArrowLeft, Plus, Pencil, Trash2 } from '@lucide/svelte';
  import { goto } from '$app/navigation';

  let { data }: { data: PageData } = $props();

  let filters = $state<Filter[]>([]);

  // Initialize filters from server data
  $effect(() => {
    filters = data.filters;
  });
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
