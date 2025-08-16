# Product Roadmap

> Last Updated: 2025-08-16
> Version: 1.0.0
> Status: Planning

## Phase 1: Core RSS Reader (2 weeks)

**Goal:** Build a functional RSS reader with essential features
**Success Criteria:** Users can import feeds, read articles, and filter content

### Must-Have Features

- [ ] Backend API setup with FastAPI and SQLite - Set up project structure `M`
- [ ] Feed management (add, edit, delete feeds) - CRUD operations for RSS feeds `M`
- [ ] OPML import functionality - Parse and import OPML files `S`
- [ ] OPML export functionality - Generate OPML from user's feeds `S`
- [ ] RSS feed parser and updater - Fetch and parse RSS/Atom feeds `L`
- [ ] Basic filtering system - Keyword and source-based filtering `M`
- [ ] Split-pane UI (categories left, entries right) - Core interface layout `M`

### Should-Have Features

- [ ] Feed categories/folders - Organize feeds into groups `S`
- [ ] Mark as read/unread functionality - Track reading status `S`
- [ ] Mobile-responsive design - Ensure usability on all devices `M`

### Dependencies

- Python environment with uv
- SvelteKit setup
- Docker configuration

## Phase 2: Enhanced User Experience (1 week)

**Goal:** Polish the reading experience with theming and navigation
**Success Criteria:** Smooth, customizable reading experience across devices

### Must-Have Features

- [ ] Dark/Light theme toggle - Implement theme switching `S`
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