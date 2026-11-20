import adapter from 'svelte-adapter-bun';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  // Consult https://svelte.dev/docs/kit/integrations
  // for more information about preprocessors
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter(),
    // Trust all origins - this is a single-user app without authentication
    // and runs behind a reverse proxy which may change the Origin header
    csrf: {
      trustedOrigins: ['*']
    },
    // Poll /_app/version.json so open tabs learn about new deployments
    version: {
      pollInterval: 60_000
    }
  }
};

export default config;
