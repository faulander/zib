<script lang="ts">
  import type { Filter } from '$lib/types';
  import * as Dialog from '$lib/components/ui/dialog';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { Switch } from '$lib/components/ui/switch';
  import { Textarea } from '$lib/components/ui/textarea';
  import Spinner from '$lib/components/spinner.svelte';

  interface Props {
    open: boolean;
    filter: Filter | null;
    onSave: (filter: Filter) => void;
    onCancel: () => void;
  }

  let { open = $bindable(), filter, onSave, onCancel }: Props = $props();

  let name = $state('');
  let rule = $state('');
  let isEnabled = $state(true);
  let matchCount = $state<number | null>(null);
  let isTesting = $state(false);
  let isSaving = $state(false);

  // Reset form when filter changes
  $effect(() => {
    if (open) {
      if (filter) {
        name = filter.name;
        rule = filter.rule;
        isEnabled = filter.is_enabled;
      } else {
        name = '';
        rule = '';
        isEnabled = true;
      }
      matchCount = null;
    }
  });

  async function testRule() {
    if (!rule.trim()) return;

    isTesting = true;
    matchCount = null;

    try {
      const res = await fetch('/api/filters/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule })
      });
      const data = await res.json();
      matchCount = data.match_count;
    } catch {
      matchCount = null;
    } finally {
      isTesting = false;
    }
  }

  async function handleSave() {
    if (!name.trim() || !rule.trim()) return;

    isSaving = true;

    try {
      if (filter) {
        // Update existing
        const res = await fetch(`/api/filters/${filter.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, rule, is_enabled: isEnabled })
        });
        const savedFilter = await res.json();
        onSave(savedFilter);
      } else {
        // Create new
        const res = await fetch('/api/filters', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, rule, is_enabled: isEnabled })
        });
        const savedFilter = await res.json();
        onSave(savedFilter);
      }
    } finally {
      isSaving = false;
    }
  }

  function handleOpenChange(isOpen: boolean) {
    if (!isOpen) {
      onCancel();
    }
  }
</script>

<Dialog.Root bind:open onOpenChange={handleOpenChange}>
  <Dialog.Content class="sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title>{filter ? 'Edit Filter' : 'New Filter'}</Dialog.Title>
      <Dialog.Description>
        Create rules to automatically hide articles containing certain keywords.
      </Dialog.Description>
    </Dialog.Header>

    <div class="space-y-4 py-4">
      <div class="space-y-2">
        <Label for="name">Name</Label>
        <Input id="name" bind:value={name} placeholder="e.g., Fussball" />
      </div>

      <div class="space-y-2">
        <Label for="rule">Rule</Label>
        <Textarea
          id="rule"
          bind:value={rule}
          placeholder={`"Rapid Wien" OR "Austria Wien" OR "Sturm Graz"`}
          rows={3}
        />
        <p class="text-xs text-muted-foreground">
          Use quotes for phrases. Combine with OR (match any) or AND (match all).
        </p>
      </div>

      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Switch id="enabled" bind:checked={isEnabled} />
          <Label for="enabled">Enabled</Label>
        </div>

        <div class="flex items-center gap-2">
          <Button variant="outline" size="sm" onclick={testRule} disabled={!rule.trim() || isTesting}>
            {#if isTesting}
              <Spinner class="h-4 w-4 mr-2" />
            {/if}
            Test
          </Button>
          {#if matchCount !== null}
            <span class="text-sm text-muted-foreground">
              {matchCount} article{matchCount === 1 ? '' : 's'} match
            </span>
          {/if}
        </div>
      </div>
    </div>

    <Dialog.Footer>
      <Button variant="outline" onclick={onCancel}>Cancel</Button>
      <Button onclick={handleSave} disabled={!name.trim() || !rule.trim() || isSaving}>
        {#if isSaving}
          <Spinner class="h-4 w-4 mr-2" />
        {/if}
        Save
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
