<script lang="ts">
  import './layout.css';
  import favicon from '$lib/assets/favicon.svg';
  import { Toaster } from '$lib/components/ui/sonner';
  import { appStore } from '$lib/stores/app.svelte';
  import { browser } from '$app/environment';
  import { updated } from '$app/state';

  let { children } = $props();

  // Initialize theme from localStorage or system preference
  if (browser) {
    const stored = localStorage.getItem('theme');
    let isDark: boolean;
    if (stored) {
      isDark = stored === 'dark';
    } else {
      isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  // Register service worker for PWA support. updateViaCache 'none' makes the
  // browser always revalidate sw.js, so new deployments reach open tabs.
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' }).catch(() => {
      // SW registration failed, app works fine without it
    });
  }

  // A new deployment exists: reload so this tab never keeps running a stale bundle
  // (skipped while reading an article so the modal isn't yanked away).
  $effect(() => {
    if (updated.current && !appStore.articleModalOpen) location.reload();
  });
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
<div
  style="--highlight-color-light: {appStore.highlightColorLight}; --highlight-color-dark: {appStore.highlightColorDark};"
>
  {@render children()}
</div>
<Toaster />
