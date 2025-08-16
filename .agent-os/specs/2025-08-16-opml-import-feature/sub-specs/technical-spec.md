# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-16-opml-import-feature/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Technical Requirements

### OPML File Processing
- Support OPML 1.0 and 2.0 formats with proper XML namespace handling
- Parse hierarchical outline structures with unlimited nesting depth
- Extract feed metadata including title, description, xmlUrl, htmlUrl, and category attributes
- Handle malformed XML gracefully with detailed error reporting
- Support large OPML files up to 10MB with streaming XML parsing
- Preserve custom OPML attributes for potential future use

### Category Management
- Create category hierarchy matching OPML outline structure
- Handle category name conflicts with intelligent naming strategies (append numbers, merge options)
- Support Unicode category names with proper encoding
- Maintain category order and nesting relationships
- Provide category mapping preview before import execution

### Feed Import & Validation
- Validate RSS/Atom feed URLs with HTTP HEAD requests before import
- Extract feed metadata (title, description, language) during validation
- Handle redirects and feed URL normalization
- Support both RSS and Atom feed formats
- Implement feed discovery for HTML URLs (locate RSS/Atom links)
- Set appropriate User-Agent headers for feed validation requests

### Duplicate Handling Strategies
- **Skip**: Ignore duplicate feeds/categories without modification
- **Update**: Replace existing feed/category metadata with OPML data
- **Merge**: Combine OPML data with existing data intelligently
- **Prompt**: Flag duplicates for user decision (API response includes conflicts)
- Duplicate detection based on normalized feed URLs and category paths

### Progress Tracking
- Implement job-based import system with unique import IDs
- Track progress at multiple levels: file parsing, category creation, feed validation, feed import
- Store import status in database with timestamps and error details
- Support progress polling via REST API endpoints
- Implement automatic cleanup of completed import jobs after 24 hours

### Error Handling & Recovery
- Collect all errors without stopping import process
- Categorize errors: XML parsing, network errors, validation failures, database constraints
- Provide user-friendly error messages with suggested resolutions
- Support partial import completion with detailed failure reports
- Log detailed error information for debugging and support

## Approach Options

**Option A: Synchronous Import Processing**
- Pros: Simple implementation, immediate results, easier error handling
- Cons: Timeout risks for large files, poor UX for slow operations, blocks API threads

**Option B: Asynchronous Import with Job Queue** (Selected)
- Pros: Better user experience, scalable for large imports, non-blocking API, progress tracking
- Cons: More complex implementation, requires job storage, eventual consistency

**Option C: Streaming Import with WebSocket Progress**
- Pros: Real-time progress updates, great UX, efficient for large files
- Cons: Complex WebSocket implementation, connection management overhead, not RESTful

**Rationale:** Option B provides the best balance of user experience and implementation complexity. Asynchronous processing allows handling large OPML files without timeout issues while providing progress tracking through polling. This approach scales well and integrates cleanly with the existing FastAPI architecture.

## External Dependencies

- **xmltodict** - Convert OPML XML to Python dictionaries for easier manipulation
  - Justification: Simplifies XML parsing and provides better error handling than raw XML libraries

- **aiohttp** - Asynchronous HTTP client for feed URL validation
  - Justification: Non-blocking HTTP requests for feed validation, integrates well with FastAPI's async nature

- **feedparser** - Parse RSS/Atom feeds for metadata extraction during validation
  - Justification: Battle-tested library for handling various feed formats and extracting consistent metadata

- **urllib3** - Advanced URL parsing and normalization
  - Justification: Robust URL handling for feed URL normalization and duplicate detection

## Performance Considerations

### Memory Management
- Stream large OPML files instead of loading entirely into memory
- Process feeds in batches to avoid overwhelming the database
- Implement configurable batch sizes based on system resources

### Database Optimization
- Use database transactions for atomic import operations
- Implement bulk insert operations for categories and feeds
- Add database indexes for feed URL and category path lookups

### Network Efficiency
- Implement connection pooling for feed validation requests
- Use concurrent validation with configurable limits (default: 10 concurrent requests)
- Implement timeout and retry logic for network requests
- Cache feed validation results to avoid duplicate requests

## Security Considerations

- Validate OPML file size and structure before processing
- Sanitize category names and feed metadata to prevent XSS
- Limit concurrent imports per user to prevent abuse
- Implement rate limiting for feed validation requests
- Validate all URLs against prohibited schemes (file://, javascript:, etc.)
- Store import jobs with user authentication context