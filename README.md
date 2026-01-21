# SvelteKit Template

A production-ready SvelteKit template with Svelte 5, TailwindCSS 4, shadcn-svelte, and essential utilities pre-configured.

## Features

- **Svelte 5** with runes syntax (`$state`, `$props`, `$derived`)
- **TailwindCSS 4** with dark mode support
- **shadcn-svelte** UI components
- **TypeScript** with strict mode
- **ESLint + Prettier** for code quality
- **Zod + Superforms** for form validation
- **Docker** ready for deployment
- Pre-built components: SEO, Theme Toggle, Spinner, Toast notifications

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

## Available Scripts

| Command                | Description                      |
| ---------------------- | -------------------------------- |
| `npm run dev`          | Start development server         |
| `npm run build`        | Build for production             |
| `npm run preview`      | Preview production build         |
| `npm run check`        | Run svelte-check for type errors |
| `npm run lint`         | Run ESLint                       |
| `npm run lint:fix`     | Run ESLint with auto-fix         |
| `npm run format`       | Format code with Prettier        |
| `npm run format:check` | Check code formatting            |

## Project Structure

```
src/
├── routes/
│   ├── +layout.svelte      # Root layout (includes Toaster)
│   ├── +page.svelte        # Home page
│   ├── +error.svelte       # Error page (404, 500, etc.)
│   └── api/
│       └── health/         # Health check endpoint
├── lib/
│   ├── api.ts              # Typed fetch wrapper
│   ├── utils.ts            # Utility functions (cn, etc.)
│   └── components/
│       ├── seo.svelte      # SEO meta tags
│       ├── theme-toggle.svelte  # Dark/light mode toggle
│       ├── spinner.svelte  # Loading spinner
│       └── ui/             # shadcn-svelte components
└── hooks.server.ts         # Server hooks (logging, auth prep)
```

## Usage Guide

### SEO Component

Add meta tags to any page:

```svelte
<script>
  import Seo from '$lib/components/seo.svelte';
</script>

<Seo
  title="Page Title"
  description="Page description for search engines"
  image="/og-image.png"
  noindex={false}
  nofollow={false}
/>
```

### Theme Toggle (Dark/Light Mode)

The theme toggle persists user preference in localStorage:

```svelte
<script>
  import ThemeToggle from '$lib/components/theme-toggle.svelte';
</script>

<header>
  <ThemeToggle />
</header>
```

### Toast Notifications

Toaster is pre-configured in the layout. Import and use anywhere:

```svelte
<script>
  import { toast } from 'svelte-sonner';

  function handleSubmit() {
    toast.success('Saved successfully!');
  }

  function handleError() {
    toast.error('Something went wrong');
  }
</script>

<button onclick={handleSubmit}>Save</button>
```

Available toast types:

- `toast('Default message')`
- `toast.success('Success!')`
- `toast.error('Error!')`
- `toast.info('Info')`
- `toast.warning('Warning')`
- `toast.loading('Loading...')`

### Loading Spinner

```svelte
<script>
  import Spinner from '$lib/components/spinner.svelte';

  let loading = $state(true);
</script>

{#if loading}
  <Spinner />
  <!-- Default: md -->
  <Spinner size="sm" />
  <!-- Small -->
  <Spinner size="lg" />
  <!-- Large -->
{/if}
```

### API Fetch Utility

Type-safe API calls with automatic JSON handling and error management:

```typescript
import { api, ApiError } from '$lib/api';

// GET request
const users = await api.get<User[]>('/api/users');

// POST request
const newUser = await api.post<User>('/api/users', {
  name: 'John',
  email: 'john@example.com'
});

// PUT request
await api.put('/api/users/1', { name: 'Jane' });

// PATCH request
await api.patch('/api/users/1', { name: 'Jane' });

// DELETE request
await api.delete('/api/users/1');

// Error handling
try {
  await api.get('/api/protected');
} catch (e) {
  if (e instanceof ApiError) {
    console.log(e.status); // HTTP status code
    console.log(e.message); // Error message
    console.log(e.data); // Response body (if any)
  }
}
```

### Form Validation with Superforms

Server-side validation with Zod schemas:

```typescript
// src/routes/contact/+page.server.ts
import { z } from 'zod';
import { superValidate, fail } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';

const schema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  message: z.string().min(10, 'Message must be at least 10 characters')
});

export const load = async () => {
  const form = await superValidate(zod(schema));
  return { form };
};

export const actions = {
  default: async ({ request }) => {
    const form = await superValidate(request, zod(schema));

    if (!form.valid) {
      return fail(400, { form });
    }

    // Process valid form data
    console.log(form.data);

    return { form };
  }
};
```

```svelte
<!-- src/routes/contact/+page.svelte -->
<script lang="ts">
  import { superForm } from 'sveltekit-superforms';

  let { data } = $props();
  const { form, errors, enhance } = superForm(data.form);
</script>

<form method="POST" use:enhance>
  <label>
    Name
    <input name="name" bind:value={$form.name} />
    {#if $errors.name}<span class="error">{$errors.name}</span>{/if}
  </label>

  <label>
    Email
    <input name="email" type="email" bind:value={$form.email} />
    {#if $errors.email}<span class="error">{$errors.email}</span>{/if}
  </label>

  <label>
    Message
    <textarea name="message" bind:value={$form.message}></textarea>
    {#if $errors.message}<span class="error">{$errors.message}</span>{/if}
  </label>

  <button type="submit">Send</button>
</form>
```

### Adding shadcn-svelte Components

Install additional UI components as needed:

```bash
# Add a button component
npx shadcn-svelte@next add button

# Add multiple components
npx shadcn-svelte@next add button card dialog

# View all available components
npx shadcn-svelte@next add
```

Usage:

```svelte
<script>
  import { Button } from '$lib/components/ui/button';
</script>

<Button variant="default">Click me</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Cancel</Button>
```

### Environment Variables

Configure in `.env` (copy from `.env.example`):

```bash
# Public variables (exposed to client)
PUBLIC_APP_NAME="My App"
PUBLIC_APP_URL="http://localhost:5173"

# Private variables (server-only)
DATABASE_URL="postgresql://..."
AUTH_SECRET="your-secret-key"
```

Access in code:

```typescript
// Client-safe variables
import { PUBLIC_APP_NAME } from '$env/static/public';

// Server-only variables
import { DATABASE_URL } from '$env/static/private';
```

### Server Hooks

The `src/hooks.server.ts` file includes:

- Request timing/logging
- Error handling with user-friendly messages
- Prepared structure for authentication

To add authentication:

```typescript
// src/hooks.server.ts
export const handle: Handle = async ({ event, resolve }) => {
  // Get session from cookie
  const sessionId = event.cookies.get('session');

  if (sessionId) {
    // Fetch user from database
    const user = await getUser(sessionId);
    event.locals.user = user;
  }

  return resolve(event);
};
```

## Styling

### Tailwind CSS

Use Tailwind classes directly:

```svelte
<div class="flex items-center gap-4 p-4 bg-background text-foreground">
  <h1 class="text-2xl font-bold">Hello</h1>
</div>
```

### CSS Variables

Available theme colors (defined in `src/routes/layout.css`):

| Variable        | Usage               |
| --------------- | ------------------- |
| `--background`  | Page background     |
| `--foreground`  | Default text        |
| `--primary`     | Primary actions     |
| `--secondary`   | Secondary elements  |
| `--muted`       | Muted backgrounds   |
| `--accent`      | Accent highlights   |
| `--destructive` | Destructive actions |
| `--border`      | Borders             |
| `--input`       | Form inputs         |
| `--ring`        | Focus rings         |

### Class Merging

Use the `cn()` utility for conditional classes:

```svelte
<script>
  import { cn } from '$lib/utils';

  let { active, className } = $props();
</script>

<div class={cn('px-4 py-2 rounded-md', active && 'bg-primary text-primary-foreground', className)}>
  Content
</div>
```

## Deployment

### Docker

Build and run:

```bash
# Build image
docker build -t myapp .

# Run container
docker run -p 3000:3000 myapp

# With environment variables
docker run -p 3000:3000 \
  -e DATABASE_URL="postgresql://..." \
  -e AUTH_SECRET="your-secret" \
  myapp
```

The Dockerfile includes:

- Multi-stage build for small image size
- Non-root user for security
- Health check at `/api/health`

### Node.js

```bash
# Build
npm run build

# Run
node build
```

### Health Check

The `/api/health` endpoint returns:

```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## License

MIT
