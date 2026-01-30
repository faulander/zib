# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
