# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-08-24-full-text-extraction/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Test Coverage

### Unit Tests

**ExtractorService**
- Test newspaper4k integration with valid article URLs
- Test extraction with malformed HTML content
- Test timeout handling for slow-responding websites
- Test User-Agent rotation and header management
- Test content validation and quality checks
- Test rate limiting enforcement between requests

**ExtractionJobManager**
- Test job creation and queuing functionality
- Test priority-based job scheduling
- Test retry logic with exponential backoff
- Test job status updates and state transitions
- Test cleanup of completed and failed jobs

**Article Model Extensions**
- Test new extraction-related fields and defaults
- Test extraction status enum validation
- Test timestamp handling with pendulum
- Test database constraints and foreign keys

### Integration Tests

**Background Extraction Worker**
- Test complete extraction pipeline from job creation to completion
- Test worker start/stop functionality
- Test concurrent extraction limits
- Test graceful shutdown with pending jobs
- Test error recovery and job rescheduling

**RSS Feed Integration**
- Test automatic job creation during RSS feed processing
- Test that RSS updates are not blocked by extraction jobs
- Test handling of new articles with duplicate URLs
- Test extraction jobs for articles added via OPML import

**API Endpoint Integration**
- Test full-text retrieval API with successful extractions
- Test manual extraction trigger with various article states
- Test extraction queue status and statistics endpoints
- Test rate limiting on manual extraction requests
- Test authentication and authorization for extraction endpoints

### Feature Tests

**End-to-End Extraction Workflow**
- Given: A new RSS article is added to the system
- When: The background worker processes the extraction job
- Then: Article has full text content available via API

**Manual Extraction Trigger**
- Given: An article with failed extraction status
- When: User triggers manual re-extraction via API
- Then: New extraction job is created and processed successfully

**Extraction Failure Recovery**
- Given: An article extraction fails due to network error
- When: The retry mechanism attempts extraction again
- Then: Article extraction succeeds on retry or marks as permanently failed

### Mocking Requirements

**Newspaper4k Library**
- Mock successful text extraction with sample content
- Mock network timeouts and connection errors
- Mock parsing failures with malformed HTML
- Mock rate limiting responses (HTTP 429)

**External Website Responses**
- Mock various HTML structures for extraction testing
- Mock slow-responding servers for timeout testing  
- Mock different content types (articles, PDFs, images)
- Mock websites with anti-scraping measures

**Background Job Processing**
- Mock asyncio task scheduling and execution
- Mock database transaction failures during job updates
- Mock worker shutdown scenarios with pending jobs

## Test Data

### Sample Articles for Testing
- Tech article with standard HTML structure
- News article with complex multimedia content
- Blog post with unusual formatting
- Paywall-protected article (should fail gracefully)
- PDF link (should be skipped)
- Invalid/broken URL (should fail with proper error)

### Test Database States
- Articles with all extraction status values
- Extraction jobs in various states (pending, running, failed)
- Articles with and without full text content
- Jobs with different retry counts and error messages

## Performance Testing

**Extraction Throughput**
- Test processing speed with batch of 100 articles
- Measure memory usage during concurrent extractions
- Test system behavior under high job queue load

**Database Performance**
- Test query performance with large numbers of extracted articles
- Measure index effectiveness for extraction job queries
- Test concurrent read/write operations on article updates

**Rate Limiting Effectiveness**
- Verify extraction delays are properly enforced
- Test behavior when multiple domains are being processed
- Measure compliance with configured rate limits