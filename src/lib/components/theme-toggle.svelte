<script lang="ts">
  import { Moon, Sun } from '@lucide/svelte';
  import { browser } from '$app/environment';

  let isDark = $state(false);

  // Initialize theme from localStorage or system preference
  if (browser) {
    const stored = localStorage.getItem('theme');
    if (stored) {
      isDark = stored === 'dark';
    } else {
      isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    updateTheme();
  }

  function updateTheme() {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  function toggle() {
    isDark = !isDark;
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateTheme();
  }
</script>

<button
  onclick={toggle}
  class="rounded-md p-2 hover:bg-accent"
  aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
>
  {#if isDark}
    <Sun class="size-5" />
  {:else}
    <Moon class="size-5" />
  {/if}
</button>
