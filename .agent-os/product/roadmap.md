# Product Roadmap

> Last Updated: 2025-08-18
> Version: 1.2.0
> Status: Phase 1-3 Complete, Phase 4 Partially Complete

## Phase 0: Already Completed

The following backend infrastructure has been implemented:

- [x] **Backend API setup with FastAPI and SQLite** - Complete project structure
- [x] **Feed management (add, edit, delete feeds)** - Full CRUD operations for RSS feeds
- [x] **OPML import functionality** - Parse and import OPML files with job tracking
- [x] **RSS feed parser and updater** - Comprehensive feed fetching with async HTTP, parsing, article extraction
- [x] **Article system** - Complete article model with content sanitization, deduplication, read status
- [x] **Feed categories/folders** - Organize feeds into groups with color coding
- [x] **Mark as read/unread functionality** - Full read status tracking with starring
- [x] **Basic filtering system** - Filter by feed, category, read status, search, tags, author, date
- [x] **Article API endpoints** - Complete REST API for article management and reading
- [x] **User settings system** - Comprehensive preferences storage and API
- [x] **Filter management system** - Advanced filter rules with Boolean logic and phrase search

## Phase 1: Frontend Implementation (1-2 weeks) - COMPLETED

**Goal:** Build a functional web interface for the RSS reader
**Success Criteria:** Users can browse feeds, read articles, and manage their reading through a web UI

### Must-Have Features

- [x] **SvelteKit frontend setup** - Complete with Vite, TailwindCSS 3.x, and proper configuration `M`
- [x] **Split-pane UI (feeds left, articles right)** - Core interface layout implemented `M`
- [x] **Feed browser** - Sidebar with categories and feeds navigation `M`
- [x] **Article list view** - Article cards with read status, starring, and metadata `L`
- [x] **Article reader** - Modal display with full article content and read status controls `M`
- [x] **Basic filtering interface** - Search, category selection, read status filters implemented `M`

### Should-Have Features

- [x] **Full dark mode** - Opinionated dark-only design, theme toggle removed `S`
- [x] **Mobile-responsive design** - TailwindCSS responsive design implemented `M`
- [ ] Keyboard shortcuts - Navigate without mouse `S`

### Frontend Components Completed

- [x] **Header Component** - Search bar and branding (dark mode only)
- [x] **Sidebar Component** - Category navigation with unread counts
- [x] **ArticleList Component** - Article cards with read/star controls, webpage redirect for short articles
- [x] **Settings Page** - Complete filter management and general preferences
- [x] **Main Layout** - Split-pane design with dark theme, dynamic page titles
- [x] **TailwindCSS Configuration** - v3.x setup working properly

### Dependencies

- Python environment with uv
- SvelteKit setup
- Docker configuration

## Phase 2: Enhanced User Experience (1 week) - COMPLETED

**Goal:** Polish the reading experience with navigation and advanced UI features
**Success Criteria:** Smooth, customizable reading experience across devices

### Must-Have Features

- [ ] Keyboard shortcuts - Navigate without mouse `S`
- [x] **Infinite scroll or pagination** - Handle large article lists `M`
- [x] **Article preview pane** - Quick article viewing with modal interface `M`

### Should-Have Features

- [ ] Reading time estimates - Calculate time per article `XS`
- [ ] Font size adjustment - Accessibility feature `S`
- [ ] Full-text extraction - Get complete articles when possible `L`

### Dependencies

- [x] Phase 1 completion
- [x] TailwindCSS theming setup

## Phase 3: Advanced Filtering & Search (2 weeks) - COMPLETED

**Goal:** Implement powerful content discovery and filtering
**Success Criteria:** Users can create complex filters and find content efficiently

### Must-Have Features

- [x] **Advanced filter rules engine** - Complex filtering logic with phrase search and Boolean operators `L`
- [x] **Save filter presets** - Store unlimited filters with category scoping `M`
- [x] **Full-text search** - Search across article titles and authors with phrase support `L`
- [x] **Boolean expression support** - AND/OR operators with quoted phrase support `M`

### Should-Have Features

- [x] **Filter by read status** - Show only unread items integrated in main interface `S`
- [x] **Filter editing** - Complete CRUD operations for filter management `S`
- [ ] Filter by date range - Time-based filtering `S`
- [ ] Smart filters (trending, popular) - AI-based filtering `XL`

### Dependencies

- Full-text search index
- Filter rule parser

## Phase 4: Performance & Polish (1 week) - PARTIALLY COMPLETED

**Goal:** Optimize performance and user workflow
**Success Criteria:** Fast, reliable feed updates and smooth UI

### Must-Have Features

- [x] **Background feed updates** - Automatic refresh with configurable intervals `M`
- [x] **Feed update scheduling** - User-configurable refresh intervals in minutes `M`
- [ ] Performance optimization - Database indexing, caching `L`
- [ ] Error handling and recovery - Graceful failure handling `M`

### Should-Have Features

- [x] **Duplicate detection** - Built into RSS parser to avoid duplicate articles `M`
- [ ] Feed health monitoring - Track broken feeds `S`
- [ ] Bulk operations - Mark multiple as read `S`

### New Features Implemented

- [x] **Auto-refresh service** - Backend scheduler with frontend sync integration
- [x] **Dynamic page titles** - Unread count displayed in browser title
- [x] **Webpage redirect for short articles** - Configurable threshold to open links directly

### Dependencies

- [x] Background job system - Implemented with asyncio
- [ ] Caching layer

## Phase 5: Advanced Features (3 weeks)

**Goal:** Add power user features and integrations
**Success Criteria:** Feature parity with premium RSS readers

### Must-Have Features

- [ ] **Authentication system** - Login/session management for API access (moved from Phase 1) `M`
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