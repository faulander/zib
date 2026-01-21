<script lang="ts">
  import './layout.css';
  import favicon from '$lib/assets/favicon.svg';
  import { Toaster } from '$lib/components/ui/sonner';
  import { appStore } from '$lib/stores/app.svelte';

  let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
<div
  style="--highlight-color-light: {appStore.highlightColorLight}; --highlight-color-dark: {appStore.highlightColorDark};"
>
  {@render children()}
</div>
<Toaster />
