<script lang="ts">
  import { Input } from '$lib/components/ui/input';
  import { Switch } from '$lib/components/ui/switch';
  import { Slider } from '$lib/components/ui/slider';
  import { toast } from 'svelte-sonner';
  import { appStore } from '$lib/stores/app.svelte';

  interface Props {
    hideReadArticles: boolean;
    compactListView: boolean;
    autoMarkAsRead: boolean;
    highlightColorLight: string;
    highlightColorDark: string;
    similarityThreshold: number;
  }

  let {
    hideReadArticles = $bindable(),
    compactListView = $bindable(),
    autoMarkAsRead = $bindable(),
    highlightColorLight = $bindable(),
    highlightColorDark = $bindable(),
    similarityThreshold = $bindable()
  }: Props = $props();

  // Slider value (single number for type="single")
  let sliderValue = $state(similarityThreshold);

  // Sync slider value when prop changes
  $effect(() => {
    sliderValue = similarityThreshold;
  });

  function handleSliderCommit(value: number) {
    similarityThreshold = value;
    updateSetting('similarityThreshold', value);
  }

  async function updateSetting(
    key:
      | 'hideReadArticles'
      | 'compactListView'
      | 'autoMarkAsRead'
      | 'highlightColorLight'
      | 'highlightColorDark'
      | 'similarityThreshold',
    value: boolean | string | number
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
        } else if (key === 'autoMarkAsRead') {
          appStore.setAutoMarkAsRead(value as boolean);
        } else if (key === 'highlightColorLight') {
          appStore.setHighlightColorLight(value as string);
        } else if (key === 'highlightColorDark') {
          appStore.setHighlightColorDark(value as string);
        } else if (key === 'similarityThreshold') {
          appStore.setSimilarityThreshold(value as number);
        }
      }
    } catch (err) {
      console.error('Failed to update setting:', err);
      toast.error('Failed to save setting');
    }
  }
</script>

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
        <div class="text-sm text-muted-foreground">Reduce vertical spacing in list view</div>
      </div>
      <Switch
        checked={compactListView}
        onCheckedChange={(checked) => {
          compactListView = checked;
          updateSetting('compactListView', checked);
        }}
      />
    </div>

    <div class="flex items-center justify-between p-4 border rounded-lg">
      <div>
        <div class="font-medium">Auto-mark as read</div>
        <div class="text-sm text-muted-foreground">
          Automatically mark articles as read when scrolling past them
        </div>
      </div>
      <Switch
        checked={autoMarkAsRead}
        onCheckedChange={(checked) => {
          autoMarkAsRead = checked;
          updateSetting('autoMarkAsRead', checked);
        }}
      />
    </div>

    <div class="p-4 border rounded-lg space-y-4">
      <div>
        <div class="font-medium">Similar articles grouping</div>
        <div class="text-sm text-muted-foreground">
          Group articles with similar titles together. Set to 0 to disable.
        </div>
      </div>

      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-sm">Similarity threshold</span>
          <span class="text-sm font-mono tabular-nums">{Math.round(sliderValue * 100)}%</span>
        </div>
        <Slider
          type="single"
          bind:value={sliderValue}
          min={0}
          max={1}
          step={0.05}
          onValueCommit={handleSliderCommit}
        />
        <div class="flex justify-between text-xs text-muted-foreground">
          <span>Off</span>
          <span>Strict (90%+)</span>
        </div>
      </div>
    </div>

    <div class="p-4 border rounded-lg space-y-4">
      <div>
        <div class="font-medium">Highlight color</div>
        <div class="text-sm text-muted-foreground">Color used for hover states on articles</div>
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
