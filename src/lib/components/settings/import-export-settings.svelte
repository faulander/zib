<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Upload, Download, Database, HardDrive } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';
  import { onMount } from 'svelte';

  let isImporting = $state(false);
  let isBackingUp = $state(false);
  let backups = $state<{ name: string; size: number; created_at: string }[]>([]);

  onMount(() => {
    loadBackups();
  });

  async function loadBackups() {
    try {
      const res = await fetch('/api/backup');
      const data = await res.json();
      backups = data.backups || [];
    } catch { /* ignore */ }
  }

  async function handleBackup() {
    isBackingUp = true;
    try {
      const res = await fetch('/api/backup', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        toast.success('Backup created successfully');
        backups = data.backups || [];
      } else {
        toast.error(data.error || 'Backup failed');
      }
    } catch {
      toast.error('Backup failed');
    } finally {
      isBackingUp = false;
    }
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
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

        const text = await res.text();
        console.log('[Import] Response status:', res.status);
        console.log('[Import] Response text:', text);

        let result;
        try {
          result = JSON.parse(text);
        } catch {
          console.error('[Import] Failed to parse JSON:', text);
          toast.error('Server returned invalid response');
          return;
        }

        if (res.ok) {
          toast.success(`Imported ${result.feeds_created || 0} feeds`);
          window.dispatchEvent(new CustomEvent('reload-data'));
        } else {
          console.error('Import failed:', result);
          toast.error(result.error || 'Import failed');
        }
      } catch (err) {
        console.error('Import failed:', err);
        toast.error('Import failed: ' + (err instanceof Error ? err.message : 'Unknown error'));
      } finally {
        isImporting = false;
      }
    };
    input.click();
  }
</script>

<section>
  <div class="mb-4">
    <h2 class="text-lg font-semibold">Import / Export</h2>
    <p class="text-sm text-muted-foreground">Import or export feeds as OPML</p>
  </div>

  <div class="space-y-3">
    <div class="flex items-center gap-4 p-4 border rounded-lg">
      <div class="flex-1">
        <div class="font-medium">Import OPML</div>
        <div class="text-sm text-muted-foreground">Import feeds and folders from an OPML file</div>
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

<section class="mt-8">
  <div class="mb-4">
    <h2 class="text-lg font-semibold">Database Backup</h2>
    <p class="text-sm text-muted-foreground">Create and download SQLite database backups</p>
  </div>

  <div class="space-y-3">
    <div class="flex items-center gap-4 p-4 border rounded-lg">
      <div class="flex-1">
        <div class="font-medium">Create Backup</div>
        <div class="text-sm text-muted-foreground">Create a backup of the current database</div>
      </div>
      <Button onclick={handleBackup} disabled={isBackingUp}>
        <Database class="h-4 w-4 mr-2" />
        {isBackingUp ? 'Backing up...' : 'Backup'}
      </Button>
    </div>

    <div class="flex items-center gap-4 p-4 border rounded-lg">
      <div class="flex-1">
        <div class="font-medium">Download Backup</div>
        <div class="text-sm text-muted-foreground">Download a fresh database backup file</div>
      </div>
      <a href="/api/backup?download=latest">
        <Button variant="outline">
          <Download class="h-4 w-4 mr-2" />
          Download
        </Button>
      </a>
    </div>

    {#if backups.length > 0}
      <div class="p-4 border rounded-lg">
        <div class="font-medium mb-2">Recent Backups</div>
        <div class="space-y-1">
          {#each backups as backup (backup.name)}
            <div class="flex items-center gap-2 text-sm text-muted-foreground">
              <HardDrive class="h-3 w-3" />
              <span class="flex-1">{backup.name}</span>
              <span>{formatBytes(backup.size)}</span>
              <span>{new Date(backup.created_at).toLocaleDateString()}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</section>
