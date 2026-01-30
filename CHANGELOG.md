# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
