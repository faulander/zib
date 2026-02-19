# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: RSS Reader (Inoreader-style)

A single-user RSS reader web application with the following features:

### Implemented Features
- **OPML Import/Export** - Import and export feeds as OPML (in Settings)
- **Folders** - Organize feeds into folders
- **Article Views** - Switchable list/card views
- **Reading Modal** - Full article display with lazy content extraction
- **Full Content Fetching** - Extracts article content using Mozilla Readability
- **Auto-Refresh** - Background job refreshes feeds every 15 minutes (smart scheduling for 500+ feeds)
- **Mark Read/Unread** - Per article, per folder, or "older than X" bulk actions
- **Instapaper Export** - Send articles to Instapaper
- **Article Filters** - Hide articles matching keyword rules (OR/AND logic), counts respect filters
- **Mobile Responsive** - Sidebar as slide-out drawer on mobile
- **Delete Feeds** - Red X on hover to remove individual feeds
- **Feed Testing** - Test feed URLs before adding or editing
- **Feed Error Management** - Settings page shows feeds with errors, allows editing/retrying/deleting
- **Infinite Scroll** - Article list loads more articles as you scroll
- **Settings**:
  - Hide read articles (global toggle)
  - Compact list view (reduced spacing)
  - OPML import
  - Feed error management
  - Article filters

### Database (SQLite with bun:sqlite)
- `folders` - Feed organization
- `feeds` - RSS feed subscriptions
- `articles` - Fetched articles with content
- `filters` - Hide rules for unwanted content
- `settings` - App configuration (key/value)

### Key Server Files
- `src/lib/server/db.ts` - SQLite connection (WAL mode), auto-creates data directory
- `src/lib/server/feeds.ts` - Feed CRUD, error tracking
- `src/lib/server/articles.ts` - Article CRUD with filter application
- `src/lib/server/folders.ts` - Folder CRUD
- `src/lib/server/filters.ts` - Filter CRUD and rule matching
- `src/lib/server/settings.ts` - App settings (hideReadArticles, compactListView)
- `src/lib/server/feed-fetcher.ts` - RSS parsing + content extraction
- `src/lib/server/scheduler.ts` - setInterval-based scheduled tasks for auto-refresh
- `src/lib/server/opml.ts` - OPML import/export
- `src/lib/server/instapaper.ts` - Instapaper API client

### Key UI Components
- `src/lib/components/sidebar/` - Navigation with folders/feeds (error indicators)
- `src/lib/components/articles/` - List (with infinite scroll), card, and modal views
- `src/lib/components/tools-panel.svelte` - View toggle, mark-read actions
- `src/lib/components/filter-editor.svelte` - Filter rule editor
- `src/lib/components/feed-edit-dialog.svelte` - Edit feed with URL testing
- `src/lib/components/add-feed-dialog.svelte` - Add feed with URL testing

### API Endpoints
- `/api/folders` - Folder CRUD
- `/api/feeds` - Feed CRUD (POST auto-fetches articles)
- `/api/feeds/[id]` - Feed GET/PUT/PATCH/DELETE
- `/api/feeds/[id]/refresh` - Refresh single feed
- `/api/feeds/test` - Test feed URL validity
- `/api/articles` - Article listing with filters, infinite scroll support
- `/api/articles/[id]` - Article read/star updates
- `/api/articles/[id]/extract` - Lazy full content extraction
- `/api/articles/[id]/instapaper` - Send to Instapaper
- `/api/filters` - Filter CRUD
- `/api/filters/test` - Test filter rule
- `/api/settings` - App settings GET/PATCH
- `/api/mark-read` - Bulk mark read
- `/api/import/opml` - OPML import
- `/api/export/opml` - OPML export (download)
- `/api/refresh` - Manual feed refresh

### Routes
- `/` - Main feed reader view
- `/settings` - Settings (general, import/export, feed errors, filters)

## Development Commands

```bash
bun run dev          # Start development server
bun run dev -- --open # Start dev server and open browser
bun run build        # Build for production (outputs to /build)
bun run preview      # Preview production build locally
bun run check        # Run svelte-check for type errors
bun run check:watch  # Run svelte-check in watch mode
bun run lint         # Run ESLint
bun run lint:fix     # Run ESLint with auto-fix
bun run format       # Format code with Prettier
bun run format:check # Check formatting without changes
```

## Tech Stack

- **Runtime:** Bun
- **Framework:** SvelteKit 2.x with Svelte 5 (uses runes syntax: `$state`, `$props`, `$derived`, etc.)
- **Database:** SQLite via `bun:sqlite` (built-in, no native deps)
- **UI Components:** shadcn-svelte (install via `bunx shadcn-svelte@next add <component>`)
- **Styling:** TailwindCSS 4.x with tw-animate-css for animations
- **Icons:** Lucide Svelte (`@lucide/svelte`)
- **Forms:** Zod + sveltekit-superforms for validation
- **Toasts:** Sonner (via shadcn-svelte)
- **Adapter:** Bun adapter (`svelte-adapter-bun`) for server deployment
- **Type Checking:** TypeScript with strict mode enabled
- **Linting:** ESLint with Svelte and TypeScript plugins
- **Formatting:** Prettier with Svelte plugin

## Code Organization Guidelines

### Component Extraction
When a page or component exceeds a readable limit (~200-300 lines), extract logical sections into separate components. This improves:
- Readability and maintainability
- Reusability across the application
- Testing and debugging

Example: The settings page uses separate components for each section (`general-settings.svelte`, `sharing-settings.svelte`, etc.) in `src/lib/components/settings/`.

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

The Dockerfile uses `oven/bun` base images with multi-stage builds for optimal image size. No native compilation dependencies needed (bun:sqlite is built-in).

## Svelte MCP Server

This project has access to the Svelte MCP server for documentation lookup and code validation:

1. **list-sections** - Discover available Svelte 5/SvelteKit documentation sections
2. **get-documentation** - Retrieve full documentation for specific topics
3. **svelte-autofixer** - Validate Svelte code before sending to user (always use this when writing Svelte components)
4. **playground-link** - Generate Svelte Playground links (only after user confirmation, never for code written to files)
