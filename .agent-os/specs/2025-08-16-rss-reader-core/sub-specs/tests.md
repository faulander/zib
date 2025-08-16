# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-08-16-rss-reader-core/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Test Coverage

### Unit Tests

**Article Model Tests**
- Test article creation with all fields
- Test article validation (required fields, URL format)
- Test unique constraints (feed_id + url, feed_id + guid)
- Test read status tracking with timestamps
- Test relationship with Feed model
- Test article deletion and cascade behavior

**Feed Update Job Model Tests**
- Test job creation and status tracking
- Test relationship with Feed model
- Test job completion status updates
- Test error message storage
- Test next run scheduling

**Feed Parser Service Tests**
- Test RSS feed parsing with valid feed
- Test Atom feed parsing with valid feed
- Test handling of malformed XML
- Test duplicate article detection
- Test conditional request headers (ETag, Last-Modified)
- Test feed timeout handling
- Test network error handling
- Test content extraction and sanitization

**Background Scheduler Service Tests**
- Test job scheduling for all active feeds
- Test job execution and status updates
- Test error handling and retry logic
- Test feed health monitoring
- Test scheduler startup and shutdown
- Test job persistence across restarts

**Article Service Tests**
- Test article filtering by feed, category, read status
- Test article pagination
- Test read status updates (single and bulk)
- Test article search functionality
- Test statistics calculation
- Test article retrieval with feed information

### Integration Tests

**Article API Tests**
- Test GET /api/articles with various filters
- Test GET /api/articles/{id} with include options
- Test PATCH /api/articles/{id}/read-status
- Test PATCH /api/articles/bulk-read-status
- Test GET /api/articles/stats
- Test error responses (404, 400, 500)
- Test pagination edge cases
- Test authorization (if applicable)

**Feed Refresh API Tests**
- Test POST /api/feeds/{id}/refresh
- Test GET /api/feeds/{id}/articles
- Test GET /api/categories/{id}/articles
- Test manual refresh with force parameter
- Test refresh error handling

**Background Job Integration Tests**
- Test full feed update workflow
- Test article creation from RSS feed
- Test duplicate article prevention
- Test feed error tracking
- Test scheduler integration with database
- Test job cleanup and maintenance

**Database Integration Tests**
- Test article queries with complex filters
- Test index performance on large datasets
- Test cascade deletion behavior
- Test transaction handling for bulk operations
- Test database migration up/down

### Feature Tests

**End-to-End RSS Reader Workflow**
- Create feed → Schedule updates → Fetch articles → Read articles
- Import OPML → Background updates → Filter articles → Mark as read
- Add multiple feeds → Bulk article operations → Statistics viewing

**Feed Update Scenarios**
- New feed with articles → Background update → Verify articles created
- Existing feed with new articles → Update → Verify only new articles added
- Feed with updated articles → Update → Verify content changes
- Broken feed → Update attempts → Verify error handling

**Article Management Scenarios**
- Read status tracking across multiple articles
- Filtering articles by various criteria combinations
- Pagination with large article datasets
- Search functionality across titles and content

## Mocking Requirements

**HTTP Requests**
- Mock external RSS/Atom feed URLs
- Mock network timeouts and connection errors
- Mock HTTP status codes (200, 304, 404, 500)
- Mock response headers (ETag, Last-Modified, Content-Type)

**Time-Based Operations**
- Mock datetime.now() for consistent test timestamps
- Mock scheduler timing for background job tests
- Mock feed update intervals and scheduling

**External Dependencies**
- Mock feedparser library responses
- Mock APScheduler job execution
- Mock database connection errors
- Mock file system operations (if any)

## Test Data Setup

**Sample RSS Feed**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <description>Test RSS feed for unit tests</description>
    <link>https://example.com</link>
    <item>
      <title>Test Article 1</title>
      <description>Test article content</description>
      <link>https://example.com/article1</link>
      <guid>test-guid-1</guid>
      <pubDate>Wed, 16 Aug 2025 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

**Sample Atom Feed**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Atom Feed</title>
  <id>https://example.com/atom</id>
  <updated>2025-08-16T10:00:00Z</updated>
  <entry>
    <title>Test Atom Article</title>
    <id>https://example.com/atom/1</id>
    <updated>2025-08-16T10:00:00Z</updated>
    <content type="html">Test atom content</content>
  </entry>
</feed>
```

**Database Fixtures**
- Test feeds with various configurations
- Test categories for feed organization
- Test articles with different read states
- Test update jobs in various states

## Performance Tests

**Article Query Performance**
- Test article listing with 10,000+ articles
- Test filtering performance with complex criteria
- Test pagination with large datasets
- Test search performance across content

**Feed Update Performance**
- Test batch feed updates (50+ feeds)
- Test concurrent feed fetching
- Test database write performance for article creation
- Test memory usage during large feed processing

## Error Recovery Tests

**Network Failure Scenarios**
- Test feed fetch timeout recovery
- Test intermittent network errors
- Test DNS resolution failures
- Test SSL certificate errors

**Database Error Scenarios**
- Test database lock handling
- Test constraint violation handling
- Test transaction rollback scenarios
- Test connection pool exhaustion

**Data Corruption Scenarios**
- Test malformed RSS/Atom XML handling
- Test invalid UTF-8 character handling
- Test extremely large article content
- Test missing required fields in feeds