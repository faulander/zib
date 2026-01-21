# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: RSS Reader (Inoreader-style)

A single-user RSS reader web application with the following features:

### Implemented Features
- **OPML Import** - Import feeds from other RSS readers
- **Folders** - Organize feeds into folders
- **Article Views** - Switchable list/card views
- **Reading Modal** - Full article display with lazy content extraction
- **Full Content Fetching** - Extracts article content using Mozilla Readability
- **Auto-Refresh** - Background job refreshes feeds every 15 minutes (smart scheduling for 500+ feeds)
- **Mark Read/Unread** - Per article, per folder, or "older than X" bulk actions
- **Star/Favorite** - Mark important articles
- **Instapaper Export** - Send articles to Instapaper
- **Article Filters** - Hide articles matching keyword rules (OR/AND logic)
- **Mobile Responsive** - Sidebar as slide-out drawer on mobile
- **Delete Feeds** - Red X on hover to remove individual feeds

### Database (SQLite with better-sqlite3)
- `folders` - Feed organization
- `feeds` - RSS feed subscriptions
- `articles` - Fetched articles with content
- `filters` - Hide rules for unwanted content
- `settings` - App configuration (key/value)

### Key Server Files
- `src/lib/server/db.ts` - SQLite connection (WAL mode)
- `src/lib/server/feeds.ts` - Feed CRUD
- `src/lib/server/articles.ts` - Article CRUD with filter application
- `src/lib/server/folders.ts` - Folder CRUD
- `src/lib/server/filters.ts` - Filter CRUD and rule matching
- `src/lib/server/feed-fetcher.ts` - RSS parsing + content extraction
- `src/lib/server/scheduler.ts` - Cron jobs for auto-refresh
- `src/lib/server/opml.ts` - OPML import/export
- `src/lib/server/instapaper.ts` - Instapaper API client

### Key UI Components
- `src/lib/components/sidebar/` - Navigation with folders/feeds
- `src/lib/components/articles/` - List, card, and modal views
- `src/lib/components/tools-panel.svelte` - View toggle, mark-read actions
- `src/lib/components/filter-editor.svelte` - Filter rule editor

### API Endpoints
- `/api/folders` - Folder CRUD
- `/api/feeds` - Feed CRUD
- `/api/articles` - Article listing with filters
- `/api/articles/[id]` - Article read/star updates
- `/api/articles/[id]/extract` - Lazy full content extraction
- `/api/articles/[id]/instapaper` - Send to Instapaper
- `/api/filters` - Filter CRUD
- `/api/filters/test` - Test filter rule
- `/api/mark-read` - Bulk mark read
- `/api/import/opml` - OPML import
- `/api/refresh` - Manual feed refresh

### Routes
- `/` - Main feed reader view
- `/settings` - Settings page with filter management

## Development Commands

```bash
npm run dev          # Start development server
npm run dev -- --open # Start dev server and open browser
npm run build        # Build for production (outputs to /build)
npm run preview      # Preview production build locally
npm run check        # Run svelte-check for type errors
npm run check:watch  # Run svelte-check in watch mode
npm run lint         # Run ESLint
npm run lint:fix     # Run ESLint with auto-fix
npm run format       # Format code with Prettier
npm run format:check # Check formatting without changes
```

## Tech Stack

- **Framework:** SvelteKit 2.x with Svelte 5 (uses runes syntax: `$state`, `$props`, `$derived`, etc.)
- **UI Components:** shadcn-svelte (install via `npx shadcn-svelte@next add <component>`)
- **Styling:** TailwindCSS 4.x with tw-animate-css for animations
- **Icons:** Lucide Svelte (`@lucide/svelte`)
- **Forms:** Zod + sveltekit-superforms for validation
- **Toasts:** Sonner (via shadcn-svelte)
- **Adapter:** Node adapter (`@sveltejs/adapter-node`) for server deployment
- **Type Checking:** TypeScript with strict mode enabled
- **Linting:** ESLint with Svelte and TypeScript plugins
- **Formatting:** Prettier with Svelte plugin

## Architecture

### Project Structure

- `src/routes/` - SvelteKit file-based routing (pages and layouts)
- `src/routes/+error.svelte` - Global error page
- `src/routes/api/health/` - Health check endpoint for monitoring
- `src/lib/` - Shared code accessible via `$lib` alias
- `src/lib/api.ts` - Typed fetch wrapper for API calls
- `src/lib/components/` - Reusable Svelte components
- `src/lib/components/ui/` - shadcn-svelte UI components
- `src/lib/components/seo.svelte` - SEO meta tags component
- `src/lib/components/theme-toggle.svelte` - Dark/light mode toggle
- `src/lib/components/spinner.svelte` - Loading spinner component
- `src/lib/utils.ts` - Utility functions including `cn()` for Tailwind class merging
- `src/hooks.server.ts` - Server hooks for auth, logging, error handling

### Theme Toggle

Use the `<ThemeToggle>` component for dark/light mode switching:

```svelte
<script>
  import ThemeToggle from '$lib/components/theme-toggle.svelte';
</script>

<ThemeToggle />
```

### Toast Notifications

Toaster is pre-configured in the layout. Use the `toast` function:

```svelte
<script>
  import { toast } from 'svelte-sonner';

  function showToast() {
    toast.success('Operation completed!');
    toast.error('Something went wrong');
    toast.info('Here is some info');
  }
</script>
```

### API Utility

Use the typed `api` helper for fetch requests:

```typescript
import { api, ApiError } from '$lib/api';

// GET request
const users = await api.get<User[]>('/api/users');

// POST request
const newUser = await api.post<User>('/api/users', { name: 'John' });

// Error handling
try {
  await api.get('/api/protected');
} catch (e) {
  if (e instanceof ApiError) {
    console.log(e.status, e.message);
  }
}
```

### SEO Component

Use the `<Seo>` component for page meta tags:

```svelte
<script>
  import Seo from '$lib/components/seo.svelte';
</script>

<Seo
  title="Page Title"
  description="Page description for search engines"
  image="/custom-og-image.png"
/>
```

### Form Validation with Superforms

Example server-side validation:

```typescript
// +page.server.ts
import { z } from 'zod';
import { superValidate, fail } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

export const load = async () => {
  const form = await superValidate(zod(schema));
  return { form };
};

export const actions = {
  default: async ({ request }) => {
    const form = await superValidate(request, zod(schema));
    if (!form.valid) return fail(400, { form });
    // Handle valid form...
    return { form };
  }
};
```

### Styling System

CSS variables are defined in `src/routes/layout.css` following the shadcn-svelte design system:

- Semantic colors: `--background`, `--foreground`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`
- Component colors: `--card`, `--popover`, `--sidebar` (with `-foreground` variants)
- Dark mode: Toggle via `.dark` class on parent element

Use the `cn()` utility from `$lib/utils` to merge Tailwind classes with proper precedence.

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `PUBLIC_*` variables are exposed to the client
- Other variables are server-only
- Access via `$env/static/public` or `$env/static/private`

## Docker Deployment

Build and run with Docker:

```bash
docker build -t myapp .
docker run -p 3000:3000 myapp
```

The Dockerfile uses multi-stage builds for optimal image size and includes a health check at `/api/health`.

## Svelte MCP Server

This project has access to the Svelte MCP server for documentation lookup and code validation:

1. **list-sections** - Discover available Svelte 5/SvelteKit documentation sections
2. **get-documentation** - Retrieve full documentation for specific topics
3. **svelte-autofixer** - Validate Svelte code before sending to user (always use this when writing Svelte components)
4. **playground-link** - Generate Svelte Playground links (only after user confirmation, never for code written to files)
