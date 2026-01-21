<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Trash2, Download, Info, AlertTriangle, AlertCircle } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';

  interface LogEntry {
    id: number;
    level: 'info' | 'warn' | 'error';
    category: string;
    message: string;
    details: string | null;
    created_at: string;
  }

  interface Props {
    logs: LogEntry[];
    logCount: number;
  }

  let { logs = $bindable(), logCount = $bindable() }: Props = $props();

  let logFilter = $state<'all' | 'info' | 'warn' | 'error'>('all');
  let isClearingLogs = $state(false);

  const filteredLogs = $derived(
    logFilter === 'all' ? logs : logs.filter((l) => l.level === logFilter)
  );

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
</script>

<section>
  <div class="flex items-center justify-between mb-4">
    <div>
      <h2 class="text-lg font-semibold">Logs</h2>
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

  <div class="border rounded-lg">
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
