<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import { Eye, EyeOff, Loader2, CheckCircle2, XCircle } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';

  interface Props {
    embeddingProvider: 'none' | 'ollama' | 'openai' | 'openai-compatible';
    embeddingModel: string;
    embeddingApiUrl: string;
    embeddingApiKey: string;
    embeddingRateLimit: number;
  }

  let {
    embeddingProvider = $bindable(),
    embeddingModel = $bindable(),
    embeddingApiUrl = $bindable(),
    embeddingApiKey = $bindable(),
    embeddingRateLimit = $bindable()
  }: Props = $props();

  let showApiKey = $state(false);
  let isSaving = $state(false);
  let isTesting = $state(false);
  let testResult = $state<{ success: boolean; message: string } | null>(null);
  let embeddingStats = $state<{ total: number; embedded: number; model: string | null } | null>(
    null
  );

  // Track the previous model to detect changes
  let previousModel = $state(embeddingModel);
  let previousProvider = $state(embeddingProvider);

  // Load stats on mount
  $effect(() => {
    loadStats();
  });

  const showApiKeyField = $derived(embeddingProvider !== 'none');
  const showRateLimit = $derived(
    embeddingProvider === 'openai' || embeddingProvider === 'openai-compatible'
  );

  const modelSuggestions = $derived.by(() => {
    if (embeddingProvider === 'ollama') {
      return ['nomic-embed-text', 'all-minilm', 'mxbai-embed-large', 'qwen3-embedding:0.6b'];
    }
    if (embeddingProvider === 'openai') {
      return ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002'];
    }
    return [];
  });

  function handleProviderChange(value: string) {
    embeddingProvider = value as Props['embeddingProvider'];

    // Auto-fill URL based on provider
    if (value === 'ollama' && !embeddingApiUrl) {
      embeddingApiUrl = 'http://localhost:11434';
    } else if (value === 'openai') {
      embeddingApiUrl = 'https://api.openai.com';
    } else if (value === 'none') {
      // Don't clear other fields when disabling
    }

    // Auto-fill model if empty
    if (value === 'ollama' && !embeddingModel) {
      embeddingModel = 'nomic-embed-text';
    } else if (value === 'openai' && !embeddingModel) {
      embeddingModel = 'text-embedding-3-small';
    }

    testResult = null;
  }

  async function loadStats() {
    try {
      const res = await fetch('/api/embeddings');
      if (res.ok) {
        embeddingStats = await res.json();
      }
    } catch {
      // Ignore
    }
  }

  async function saveSettings() {
    // Check if model/provider changed and embeddings exist
    const modelChanged =
      (embeddingModel !== previousModel || embeddingProvider !== previousProvider) &&
      embeddingStats &&
      embeddingStats.embedded > 0;

    if (modelChanged) {
      const confirmed = confirm(
        `Changing the embedding model invalidates all ${embeddingStats!.embedded} existing embeddings. Purge them and start fresh?`
      );
      if (!confirmed) return;
    }

    isSaving = true;
    try {
      const res = await fetch('/api/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          embeddingProvider,
          embeddingModel,
          embeddingApiUrl,
          embeddingApiKey,
          embeddingRateLimit
        })
      });

      if (!res.ok) {
        toast.error('Failed to save settings');
        return;
      }

      // Purge embeddings if model changed
      if (modelChanged) {
        await fetch('/api/embeddings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'purge' })
        });
        toast.success('Settings saved, embeddings purged');
      } else {
        toast.success('Embedding settings saved');
      }

      previousModel = embeddingModel;
      previousProvider = embeddingProvider;
      await loadStats();
    } catch {
      toast.error('Failed to save settings');
    } finally {
      isSaving = false;
    }
  }

  async function testConnection() {
    isTesting = true;
    testResult = null;

    // Save first so the server uses the current settings
    try {
      await fetch('/api/settings', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          embeddingProvider,
          embeddingModel,
          embeddingApiUrl,
          embeddingApiKey,
          embeddingRateLimit
        })
      });
    } catch {
      // Continue with test anyway
    }

    try {
      const res = await fetch('/api/embeddings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'test' })
      });

      const data = await res.json();

      if (data.success) {
        testResult = {
          success: true,
          message: `Connected! Model: ${data.model}, ${data.dimensions} dimensions, ${data.latencyMs}ms`
        };
      } else {
        testResult = {
          success: false,
          message: data.error || 'Connection failed'
        };
      }
    } catch (err) {
      testResult = {
        success: false,
        message: err instanceof Error ? err.message : 'Connection failed'
      };
    } finally {
      isTesting = false;
    }
  }

  let isProcessing = $state(false);
  let pollInterval: ReturnType<typeof setInterval> | null = null;

  async function triggerProcessing() {
    isProcessing = true;

    // Poll stats every 2 seconds while processing
    pollInterval = setInterval(loadStats, 2000);

    try {
      const res = await fetch('/api/embeddings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'process' })
      });
      const data = await res.json();
      if (data.success) {
        toast.success(`Processed ${data.processed} articles (${data.failed} failed)`);
      }
    } catch {
      toast.error('Failed to process embeddings');
    } finally {
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = null;
      isProcessing = false;
      await loadStats();
    }
  }

  async function purgeEmbeddings() {
    const confirmed = confirm(
      `Delete all ${embeddingStats?.embedded ?? 0} embeddings? They will be regenerated on next process.`
    );
    if (!confirmed) return;

    try {
      await fetch('/api/embeddings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'purge' })
      });
      toast.success('Embeddings purged');
      await loadStats();
    } catch {
      toast.error('Failed to purge embeddings');
    }
  }
</script>

<section>
  <div class="mb-4">
    <h2 class="text-lg font-semibold">AI / Embeddings</h2>
    <p class="text-sm text-muted-foreground">
      Configure an embedding provider for semantic article similarity grouping
    </p>
  </div>

  <div class="space-y-3">
    <!-- Provider selection -->
    <div class="p-4 border rounded-lg space-y-4">
      <div>
        <div class="font-medium">Embedding provider</div>
        <div class="text-sm text-muted-foreground">
          Choose how embeddings are generated for article similarity
        </div>
      </div>

      <div class="space-y-3">
        <div class="space-y-1.5">
          <Label for="embedding-provider">Provider</Label>
          <select
            id="embedding-provider"
            class="flex h-9 w-full rounded-md border border-input bg-background text-foreground px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            style="color-scheme: light dark;"
            value={embeddingProvider}
            onchange={(e) => handleProviderChange(e.currentTarget.value)}
          >
            <option value="none">None (Dice coefficient only)</option>
            <option value="ollama">Ollama (local)</option>
            <option value="openai">OpenAI API</option>
            <option value="openai-compatible">OpenAI-compatible API</option>
          </select>
        </div>

        {#if embeddingProvider !== 'none'}
          <div class="space-y-1.5">
            <Label for="embedding-model">Model</Label>
            <Input
              id="embedding-model"
              type="text"
              placeholder={embeddingProvider === 'ollama'
                ? 'nomic-embed-text'
                : 'text-embedding-3-small'}
              bind:value={embeddingModel}
            />
            {#if modelSuggestions.length > 0}
              <div class="flex flex-wrap gap-1.5 mt-1">
                {#each modelSuggestions as suggestion}
                  <button
                    type="button"
                    class="text-xs px-2 py-0.5 rounded-full border hover:bg-muted transition-colors {embeddingModel ===
                    suggestion
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'text-muted-foreground'}"
                    onclick={() => (embeddingModel = suggestion)}
                  >
                    {suggestion}
                  </button>
                {/each}
              </div>
            {/if}
          </div>

          <div class="space-y-1.5">
            <Label for="embedding-url">API URL</Label>
            <Input
              id="embedding-url"
              type="text"
              placeholder={embeddingProvider === 'ollama'
                ? 'http://localhost:11434'
                : 'https://api.openai.com'}
              bind:value={embeddingApiUrl}
            />
          </div>

          {#if showApiKeyField}
            <div class="space-y-1.5">
              <Label for="embedding-key">API Key</Label>
              <div class="relative">
                <Input
                  id="embedding-key"
                  type={showApiKey ? 'text' : 'password'}
                  placeholder="sk-..."
                  bind:value={embeddingApiKey}
                  class="pr-10"
                />
                <button
                  type="button"
                  class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                  onclick={() => (showApiKey = !showApiKey)}
                >
                  {#if showApiKey}
                    <EyeOff class="h-4 w-4" />
                  {:else}
                    <Eye class="h-4 w-4" />
                  {/if}
                </button>
              </div>
              <p class="text-xs text-muted-foreground">
                {#if embeddingProvider === 'ollama'}
                  Optional. Only needed if Ollama is behind an authenticated reverse proxy.
                {:else}
                  Also configurable via EMBEDDING_API_KEY environment variable.
                {/if}
              </p>
            </div>
          {/if}

          {#if showRateLimit}
            <div class="space-y-1.5">
              <Label for="embedding-rate">Rate limit (requests/min)</Label>
              <Input
                id="embedding-rate"
                type="number"
                min={1}
                max={1000}
                bind:value={embeddingRateLimit}
              />
            </div>
          {/if}

          <!-- Test & Save buttons -->
          <div class="flex gap-2 pt-2">
            <Button onclick={saveSettings} disabled={isSaving || !embeddingModel || !embeddingApiUrl}>
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
            <Button
              variant="outline"
              onclick={testConnection}
              disabled={isTesting || !embeddingModel || !embeddingApiUrl}
            >
              {#if isTesting}
                <Loader2 class="h-4 w-4 mr-1 animate-spin" />
                Testing...
              {:else}
                Test Connection
              {/if}
            </Button>
          </div>

          <!-- Test result -->
          {#if testResult}
            <div
              class="flex items-start gap-2 p-3 rounded-lg text-sm {testResult.success
                ? 'bg-green-500/10 text-green-700 dark:text-green-400'
                : 'bg-red-500/10 text-red-700 dark:text-red-400'}"
            >
              {#if testResult.success}
                <CheckCircle2 class="h-4 w-4 mt-0.5 shrink-0" />
              {:else}
                <XCircle class="h-4 w-4 mt-0.5 shrink-0" />
              {/if}
              <span>{testResult.message}</span>
            </div>
          {/if}
        {/if}
      </div>
    </div>

    <!-- Embedding status -->
    {#if embeddingProvider !== 'none' && embeddingStats}
      <div class="p-4 border rounded-lg space-y-3">
        <div>
          <div class="font-medium">Embedding status</div>
          <div class="text-sm text-muted-foreground">
            Articles with embeddings for similarity search
          </div>
        </div>

        <div class="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div class="text-sm space-y-1">
            <div>
              <span class="text-muted-foreground">Embedded:</span>
              <span class="ml-1 font-medium tabular-nums">
                {embeddingStats.embedded} / {embeddingStats.total}
              </span>
              {#if embeddingStats.total > 0}
                <span class="ml-1 text-muted-foreground">
                  ({Math.round((embeddingStats.embedded / embeddingStats.total) * 100)}%)
                </span>
              {/if}
            </div>
            {#if embeddingStats.model}
              <div>
                <span class="text-muted-foreground">Model:</span>
                <span class="ml-1 font-mono text-xs">{embeddingStats.model}</span>
              </div>
            {/if}
          </div>
          <div class="flex gap-2">
            <Button variant="outline" size="sm" onclick={triggerProcessing} disabled={isProcessing}>
              {#if isProcessing}
                <Loader2 class="h-4 w-4 mr-1 animate-spin" />
                Processing...
              {:else}
                Process now
              {/if}
            </Button>
            {#if embeddingStats.embedded > 0 && !isProcessing}
              <Button variant="outline" size="sm" onclick={purgeEmbeddings}>
                Purge
              </Button>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </div>
</section>
