# Product Roadmap

> Last Updated: 2025-08-16
> Version: 1.0.0
> Status: In Development

## Phase 0: Already Completed

The following backend infrastructure has been implemented:

- [x] **Backend API setup with FastAPI and SQLite** - Complete project structure
- [x] **Feed management (add, edit, delete feeds)** - Full CRUD operations for RSS feeds
- [x] **OPML import functionality** - Parse and import OPML files with job tracking
- [x] **RSS feed parser and updater** - Comprehensive feed fetching with async HTTP, parsing, article extraction
- [x] **Article system** - Complete article model with content sanitization, deduplication, read status
- [x] **Feed categories/folders** - Organize feeds into groups with color coding
- [x] **Mark as read/unread functionality** - Full read status tracking with starring
- [x] **Advanced filtering system** - Filter by feed, category, read status, search, tags, author, date
- [x] **Article API endpoints** - Complete REST API for article management and reading

## Phase 1: Frontend Implementation (1-2 weeks) - IN PROGRESS

**Goal:** Build a functional web interface for the RSS reader
**Success Criteria:** Users can browse feeds, read articles, and manage their reading through a web UI

### Must-Have Features

- [x] **SvelteKit frontend setup** - Complete with Vite, TailwindCSS 3.x, and proper configuration `M`
- [ ] Authentication system - Login/session management for API access `M`
- [x] **Split-pane UI (feeds left, articles right)** - Core interface layout implemented `M`
- [x] **Feed browser** - Sidebar with categories and feeds navigation `M`
- [x] **Article list view** - Article cards with read status, starring, and metadata `L`
- [ ] Article reader - Display individual articles with read status controls `M`
- [ ] Basic filtering interface - Search, category selection, read status filters `M`

### Should-Have Features

- [x] **Dark/Light theme toggle** - Working theme switching with system preference detection `S`
- [x] **Mobile-responsive design** - TailwindCSS responsive design implemented `M`
- [ ] Keyboard shortcuts - Navigate without mouse `S`

### Frontend Components Completed

- [x] **Header Component** - Search bar, theme toggle, branding
- [x] **Sidebar Component** - Category navigation with unread counts
- [x] **ArticleList Component** - Article cards with read/star controls
- [x] **Main Layout** - Split-pane design with proper dark theme
- [x] **TailwindCSS Configuration** - v3.x setup working properly

### Dependencies

- Python environment with uv
- SvelteKit setup
- Docker configuration

## Phase 2: Enhanced User Experience (1 week)

**Goal:** Polish the reading experience with navigation and advanced UI features
**Success Criteria:** Smooth, customizable reading experience across devices

### Must-Have Features

- [ ] Keyboard shortcuts - Navigate without mouse `S`
- [ ] Infinite scroll or pagination - Handle large article lists `M`
- [ ] Article preview pane - Quick article viewing `M`

### Should-Have Features

- [ ] Reading time estimates - Calculate time per article `XS`
- [ ] Font size adjustment - Accessibility feature `S`
- [ ] Full-text extraction - Get complete articles when possible `L`

### Dependencies

- Phase 1 completion
- TailwindCSS theming setup

## Phase 3: Advanced Filtering & Search (2 weeks)

**Goal:** Implement powerful content discovery and filtering
**Success Criteria:** Users can create complex filters and find content efficiently

### Must-Have Features

- [ ] Advanced filter rules engine - Complex filtering logic `L`
- [ ] Save filter presets - Store and reuse filters `M`
- [ ] Full-text search - Search across all articles `L`
- [ ] Regular expression support - Power user filtering `M`

### Should-Have Features

- [ ] Filter by date range - Time-based filtering `S`
- [ ] Filter by read status - Show only unread items `S`
- [ ] Smart filters (trending, popular) - AI-based filtering `XL`

### Dependencies

- Full-text search index
- Filter rule parser

## Phase 4: Performance & Polish (1 week)

**Goal:** Optimize performance and user workflow
**Success Criteria:** Fast, reliable feed updates and smooth UI

### Must-Have Features

- [ ] Background feed updates - Automatic refresh `M`
- [ ] Feed update scheduling - Configurable update intervals `M`
- [ ] Performance optimization - Database indexing, caching `L`
- [ ] Error handling and recovery - Graceful failure handling `M`

### Should-Have Features

- [ ] Duplicate detection - Avoid showing same article twice `M`
- [ ] Feed health monitoring - Track broken feeds `S`
- [ ] Bulk operations - Mark multiple as read `S`

### Dependencies

- Background job system
- Caching layer

## Phase 5: Advanced Features (3 weeks)

**Goal:** Add power user features and integrations
**Success Criteria:** Feature parity with premium RSS readers

### Must-Have Features

- [ ] Saved articles/bookmarks - Archive important articles `M`
- [ ] Tags and labels - Custom organization system `M`
- [ ] Export options (PDF, Markdown) - Save articles externally `L`
- [ ] Statistics dashboard - Reading habits analytics `L`

### Should-Have Features

- [ ] Webhook integrations - Connect to other services `L`
- [ ] Email digest - Daily/weekly summaries `XL`
- [ ] AI-powered recommendations - Content suggestions `XL`
- [ ] Multi-user support (optional) - Shared instance capability `XL`

### Dependencies

- Export libraries
- Analytics framework
- Optional: AI service integration