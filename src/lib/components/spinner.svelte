<script lang="ts">
  import { cn } from '$lib/utils';
  import { LoaderCircle } from '@lucide/svelte';

  interface Props {
    class?: string;
    size?: 'sm' | 'md' | 'lg';
  }

  let { class: className, size = 'md' }: Props = $props();

  const sizes = {
    sm: 'size-4',
    md: 'size-6',
    lg: 'size-8'
  };
</script>

<LoaderCircle class={cn('animate-spin text-muted-foreground', sizes[size], className)} />
