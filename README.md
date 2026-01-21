# ZIB - RSS Reader

A modern, self-hosted RSS reader built with SvelteKit. Clean interface, fast performance, and all the features you need to stay on top of your feeds.

![ZIB Screenshot](screenshot.png)

## Features

- **Folder Organization** - Group your feeds into folders for easy navigation
- **Dual View Modes** - Switch between compact list view and visual card view with images
- **Smart Refresh** - Adaptive per-feed refresh rates based on publication frequency and your reading habits
- **Full Content Extraction** - Automatically fetches full article content using Mozilla Readability
- **Article Filters** - Hide unwanted content with keyword-based rules (supports AND/OR logic)
- **Instapaper Integration** - Save articles to read later with one click
- **OPML Import/Export** - Easy migration from other RSS readers
- **Dark Mode** - Full dark/light theme support
- **Mobile Responsive** - Works great on desktop and mobile devices
- **Real-time Updates** - Server-Sent Events push new articles to your browser instantly

## Tech Stack

- **Frontend**: SvelteKit 2, Svelte 5, TailwindCSS 4, shadcn-svelte
- **Backend**: SvelteKit API routes, better-sqlite3
- **Database**: SQLite with WAL mode for performance

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Docker

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or build and run manually
docker build -t zib .
docker run -p 3000:3000 -v zib-data:/app/data zib
```

The app will be available at `http://localhost:3000`.

## Configuration

ZIB stores all data in a SQLite database. By default, this is located at `data/rss.db`. You can change this by setting the `DATABASE_PATH` environment variable.

```bash
DATABASE_PATH=/path/to/your/rss.db
```

## Screenshots

### List View
Clean, information-dense list view for power users.

### Card View
Visual card layout with article images - great for browsing.

### Settings
Manage feeds, configure filters, view logs, and set up integrations.

## License

MIT
