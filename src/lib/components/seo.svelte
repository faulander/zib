<script lang="ts">
  import { page } from '$app/stores';
  import { PUBLIC_APP_NAME, PUBLIC_APP_URL } from '$env/static/public';

  interface Props {
    title?: string;
    description?: string;
    image?: string;
    noindex?: boolean;
    nofollow?: boolean;
  }

  let {
    title,
    description = 'Built with SvelteKit',
    image = '/og-image.png',
    noindex = false,
    nofollow = false
  }: Props = $props();

  const siteName = PUBLIC_APP_NAME || 'My App';
  const siteUrl = PUBLIC_APP_URL || 'http://localhost:5173';

  const pageTitle = $derived(title ? `${title} | ${siteName}` : siteName);
  const canonicalUrl = $derived(`${siteUrl}${$page.url.pathname}`);
  const imageUrl = $derived(image.startsWith('http') ? image : `${siteUrl}${image}`);
  const robots = $derived(
    [noindex ? 'noindex' : 'index', nofollow ? 'nofollow' : 'follow'].join(', ')
  );
</script>

<svelte:head>
  <title>{pageTitle}</title>
  <meta name="description" content={description} />
  <meta name="robots" content={robots} />
  <link rel="canonical" href={canonicalUrl} />

  <!-- Open Graph -->
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content={siteName} />
  <meta property="og:title" content={pageTitle} />
  <meta property="og:description" content={description} />
  <meta property="og:url" content={canonicalUrl} />
  <meta property="og:image" content={imageUrl} />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content={pageTitle} />
  <meta name="twitter:description" content={description} />
  <meta name="twitter:image" content={imageUrl} />
</svelte:head>
