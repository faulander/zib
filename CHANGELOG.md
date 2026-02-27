# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.4] - 2026-02-26

### Changed

- **Engagement-based feed statistics** - Feed engagement metric now tracks genuine user interaction (opened, saved, sent to Instapaper) instead of scroll-based read marks
  - New `is_opened` flag set when an article is viewed in the reading modal
  - New `is_sent_to_instapaper` flag set on successful Instapaper send
  - Engagement rate replaces read rate in adaptive TTL calculation, feed edit dialog, and settings feed list
  - TTL thresholds recalibrated for realistic engagement rates (20%/10%/3% instead of 80%/50%/20%)

### Fixed

- Saved articles count in sidebar and tools panel now updates immediately when saving/unsaving an article

### Improved

- **Highlight theming** - Amber highlight colors now use CSS custom properties for consistent light/dark mode support
- **Article row DOM** - Deduplicated mobile/desktop article row markup into a single responsive layout
- **Card view read state** - Read articles in card view now show reduced opacity and lighter title text
- **Card focus vs highlight** - Focus ring and highlight ring no longer conflict on card views
- **Card view height** - Cards use `min-h` instead of fixed `h` to prevent content clipping
- **Highlight separator** - Subtle gradient divider between highlighted and normal articles in sort-first mode
- **Saved view empty state** - Dedicated empty message for saved articles view
- **Saved count in sidebar** - Sidebar "Saved" button now shows total saved article count
- **Tools panel saved context** - Tools panel title and count reflect saved articles view
- **Article reading font** - Article modal uses Source Serif 4 serif font for comfortable long-form reading

## [0.9.3] - 2026-02-26

### Added

- **Highlighted Feeds** - Mark important feeds so their articles stand out
  - Per-feed "Highlight this feed" toggle in feed edit dialog
  - Sparkle icon on highlighted feeds in the sidebar
  - Three display modes configurable in Settings > General:
    - **Visual emphasis** - Amber left border, subtle background tint, and bold feed name on articles from highlighted feeds
    - **Sort first** - Articles from highlighted feeds appear at the top of the list
    - **Both** - Combines visual emphasis and sort-first ordering
  - Works in both list and card views
  - Cursor-based pagination supports highlight-aware ordering

### Fixed

- Similar articles grouping no longer breaks highlight-based sort order
  - Grouping previously re-sorted all articles by date, ignoring the highlight rank

## [0.9.2] - 2026-02-25

### Fixed

- Saved articles no longer appear with muted/read styling in the saved view
  - Read articles in the saved view now display with full-contrast text, matching unread appearance

## [0.9.1] - 2026-02-25

### Fixed

- Saved articles view now shows all saved articles regardless of read status
  - Previously, the "hide read articles" setting and "unread only" filter would
    exclude read articles from the saved view, causing them to disappear


## [0.9.0] - 2026-02-25

### Added

- **Save for Later** - Bookmark articles for later reading, separate from starring
  - New `is_saved` column with dedicated "Saved" view in sidebar
  - Bookmark icon on article rows (list and card views) and in article modal
  - `l` keyboard shortcut in article modal to toggle saved
  - Saved articles excluded from automatic cleanup (same as starred)
  - Independent from star — articles can be both saved and starred
- **Drag-and-Drop Reordering** - Reorder feeds and folders by dragging in the sidebar
  - Drag folders to reorder them
  - Drag feeds between folders to move them
  - Drag uncategorized feeds to reorder
  - Drag feeds within a folder to reorder
  - Visual drop indicator during drag
  - Positions persist via batch update API endpoints
  - Sidebar now sorted by position (previously insertion order)

## [0.8.0] - 2026-02-25

### Added

- **Feed Auto-Discovery** - Automatically detect feeds from website URLs
  - Parses `<link rel="alternate">` tags for RSS/Atom feed URLs
  - Falls back to probing common feed paths (`/feed`, `/rss`, `/atom.xml`, etc.)
  - Discovered feeds shown as clickable options in the Add Feed dialog
  - Resolves relative feed URLs to absolute
- **Database Backup** - Create and download SQLite database backups
  - Atomic backup via SQLite `VACUUM INTO` (safe with WAL mode)
  - Download backup as `.db` file from Settings > Import / Export
  - Backup list with file size and creation date
  - Automatic cleanup of old backups (keeps last 5)
- **PWA Support** - Progressive Web App for mobile installability
  - Web app manifest with standalone display mode
  - Service worker caching static assets (network-first for API calls)
  - Apple mobile web app meta tags
  - Installable from browser on mobile and desktop

## [0.7.0] - 2026-02-25

### Added

- **Full-Text Search** - Search articles by keyword across all feeds
  - SQLite FTS5 virtual table indexed on title, content, and author
  - Automatic index sync via INSERT/UPDATE/DELETE triggers
  - Search input in the tools panel with 300ms debounce
  - Prefix matching for single terms, phrase matching for multi-word queries
  - Search results scoped to current feed/folder context
  - Migration populates search index for existing articles
- **Keyboard Navigation** - Vim-style keyboard shortcuts for the article list
  - `j`/`k` or Arrow keys to navigate articles with visible focus indicator
  - `Enter`/`o` to open the focused article
  - `s` to toggle star, `m` to toggle read/unread on focused article
  - `v` to open article URL in new tab, `r` to refresh current view
  - `g a` to go to All Items, `g s` to go to Starred
  - `?` to show keyboard shortcut help overlay
  - Focus ring on article rows and cards
  - Shortcuts disabled when typing in inputs or when article modal is open

## [0.6.2] - 2026-02-24

### Changed

- Filters now match against article title only by default (previously matched full content)
  - Prevents false positives from timestamps, metadata, and HTML in article body
  - New "Title only" toggle in filter editor to control per filter
  - Existing filters automatically default to title-only matching
  - Toggle off to match against full article content when needed

## [0.6.1] - 2026-02-24

### Added

- Show last 10 matched articles per filter in settings
  - Expandable section on each filter row with chevron toggle
  - Displays article title, feed name, and publish date
  - Matches loaded lazily on expand and cached until filter is edited
  - New API endpoint `GET /api/filters/:id/matches`

## [0.6.0] - 2026-02-22

### Added

- Regex support in article filter rules
  - Use `/pattern/` syntax alongside existing quoted terms (e.g., `/\d+:\d+/` matches all score patterns)
  - Regex is always case-insensitive to match existing filter behavior
  - Can be combined with AND/OR operators and parentheses
  - Invalid regex gracefully falls back to literal substring match
  - Updated filter editor help text and placeholder with regex example

## [0.5.0] - 2026-02-19

### Changed

- Migrated runtime from Node.js to Bun
- Replaced `better-sqlite3` with `bun:sqlite` (built-in, no native compilation)
- Replaced `@sveltejs/adapter-node` with `svelte-adapter-bun`
- Replaced `node-cron` with native `setInterval` scheduling
- Dockerfile now uses `oven/bun` base images (smaller, no build toolchain needed)
- Package manager switched from npm to bun

## [0.4.9] - 2026-02-01

### Added

- Article age filter for feed refreshes
  - Skips articles older than 7 days during regular feed refreshes
  - Prevents importing historical content when feeds return old articles
  - New "Import old articles" toggle in Settings > General to disable the filter
  - New feed subscriptions still import all articles regardless of age

## [0.4.8] - 2026-01-30

### Added

- Folder management in Settings > Folders
  - Add new folders with "Add Folder" button
  - Rename folders inline with edit button
  - Delete folders with option to move feeds to another folder or delete them
  - Shows feed count per folder

## [0.4.7] - 2026-01-30

### Added

- Feed sorting in Settings > Feeds
  - Sort by name, popularity (read rate), post frequency, or total articles
  - Toggle ascending/descending order

## [0.4.6] - 2026-01-30

### Added

- Font size adjustment for article list view
  - New setting in General settings with -2 to +2 offset
  - Affects article titles in both desktop and mobile layouts

## [0.4.5] - 2026-01-30

### Added

- Mobile UX improvements
  - Sidebar automatically closes when selecting a folder or feed
  - Action buttons (mark read, delete, refresh) always visible on mobile (hidden on desktop until hover)

### Fixed

- Hover states no longer "stick" on touch devices
  - Custom highlight colors now wrapped in `@media (hover: hover)` query

## [0.4.4] - 2026-01-30

### Fixed

- Similar articles still appearing in list despite being grouped
  - Made sort stable by using article ID as tiebreaker when dates are equal

## [0.4.3] - 2026-01-30

### Fixed

- Similar articles API endpoint still referenced removed `string-similarity` package
  - Updated `/api/articles/[id]/similar` to use local Dice coefficient implementation
  - Fixes "no similar articles found" error in article modal

## [0.4.2] - 2026-01-30

### Changed

- Replaced `string-similarity` npm package with local Dice coefficient implementation
  - Zero external dependencies for similarity calculation
  - Better performance without module overhead
  - Easier to maintain and customize

## [0.4.1] - 2026-01-30

### Fixed

- Infinite scroll not working when similarity grouping is enabled
  - API now returns `hasMore` metadata based on database query results (before grouping)
  - Fixes issue where grouped articles reduced array size, incorrectly stopping pagination

## [0.4.0] - 2026-01-30

### Added

- **Similar Articles Grouping** - Articles with similar titles are now automatically grouped together
  - Configurable similarity threshold in Settings (default 65%)
  - Badge indicator shows count of similar articles in list and card views
  - Similar articles section in article modal for easy navigation between related stories
  - Groups articles from any feed (including follow-ups within the same feed)
  - Uses 48-hour time window for comparison
  - Powered by string-similarity package for title comparison

### Changed

- Article modal now shows "Similar Articles" section when similarity grouping is enabled
- Settings page includes new slider for adjusting similarity threshold (0-100%)

## [0.3.0] - 2026-01-22

### Added

- Auto mark as read on scroll feature
- Configurable highlight colors for light and dark mode

## [0.2.0] - 2026-01-22

### Added

- Adaptive TTL for smart feed refresh rates
- Feed statistics tracking
- Application logging system

## [0.1.0] - 2026-01-22

### Added

- Initial release
- Folder organization for feeds
- List and card view modes
- Full content extraction with Mozilla Readability
- Article filters with AND/OR logic
- Instapaper integration
- OPML import/export
- Dark/light theme support
- Mobile responsive design
- Real-time updates via Server-Sent Events
- Infinite scroll for article list
- Feed error management in settings
