<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Upload, Download } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';

  let isImporting = $state(false);

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

        const result = await res.json();

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
