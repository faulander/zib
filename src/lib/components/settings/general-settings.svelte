<script lang="ts">
  import { Input } from '$lib/components/ui/input';
  import { Switch } from '$lib/components/ui/switch';
  import { toast } from 'svelte-sonner';
  import { appStore } from '$lib/stores/app.svelte';

  interface Props {
    hideReadArticles: boolean;
    compactListView: boolean;
    highlightColorLight: string;
    highlightColorDark: string;
  }

  let {
    hideReadArticles = $bindable(),
    compactListView = $bindable(),
    highlightColorLight = $bindable(),
    highlightColorDark = $bindable()
  }: Props = $props();

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
