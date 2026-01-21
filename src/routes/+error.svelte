<script lang="ts">
  import { page } from '$app/stores';
</script>

<svelte:head>
  <title>Error {$page.status}</title>
</svelte:head>

<div class="flex min-h-[50vh] flex-col items-center justify-center gap-4 px-4">
  <h1 class="text-6xl font-bold text-muted-foreground">{$page.status}</h1>
  <p class="text-xl text-muted-foreground">
    {#if $page.status === 404}
      Page not found
    {:else if $page.status === 500}
      Internal server error
    {:else}
      {$page.error?.message || 'Something went wrong'}
    {/if}
  </p>
  <a
    href="/"
    class="mt-4 rounded-md bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
  >
    Go home
  </a>
</div>
