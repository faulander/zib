# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-08-16-opml-import-feature/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Test Coverage

### Unit Tests

**OPMLParser**
- Parse valid OPML 1.0 and 2.0 formats with various structures
- Handle malformed XML gracefully with appropriate error messages
- Extract feed metadata (title, description, xmlUrl, htmlUrl) correctly
- Parse nested category hierarchies with unlimited depth
- Handle missing or invalid attributes without crashing
- Preserve custom OPML attributes for future compatibility

**FeedValidator**
- Validate RSS and Atom feed URLs with successful responses
- Handle HTTP redirects and return final feed URLs
- Detect invalid URLs and network errors appropriately
- Extract feed metadata (title, description, type) during validation
- Handle timeout scenarios and connection failures
- Respect rate limiting and implement backoff strategies

**DuplicateHandler**
- Detect duplicate feeds based on normalized URLs
- Detect duplicate categories based on name and path
- Apply skip strategy correctly without modifying existing data
- Apply update strategy by replacing metadata appropriately
- Apply merge strategy by combining data intelligently
- Handle edge cases like circular category references

**ImportJobManager**
- Create import jobs with unique IDs and proper initialization
- Track progress accurately across different import phases
- Update job status transitions correctly (pending → processing → completed)
- Handle job cancellation and cleanup appropriately
- Calculate progress percentages and estimates accurately
- Store and retrieve job results with proper error handling

### Integration Tests

**OPML Upload Flow**
- Upload valid OPML files through multipart/form-data API
- Reject oversized files with appropriate error messages
- Reject invalid file formats with detailed error information
- Handle authentication and authorization correctly
- Create import jobs and return proper job IDs
- Apply duplicate strategies as specified in upload parameters

**Import Processing Workflow**
- Process complete OPML import from start to finish
- Create category hierarchies matching OPML structure
- Import feeds with validation and metadata extraction
- Handle network failures during feed validation gracefully
- Apply duplicate handling strategies consistently
- Generate comprehensive import results and statistics

**Progress Tracking System**
- Track import progress through all phases accurately
- Update progress in real-time during processing
- Handle concurrent progress updates without race conditions
- Provide accurate time estimates for completion
- Clean up completed jobs after expiration period
- Handle job cancellation during processing

**API Endpoint Integration**
- Test all OPML import API endpoints with valid requests
- Verify proper error responses for invalid requests
- Test authentication and authorization on all endpoints
- Verify proper status codes and response formats
- Test pagination and filtering on import history endpoint
- Handle edge cases like expired import jobs

### Feature Tests

**Complete OPML Migration Scenario**
- User uploads large OPML file with hierarchical structure
- System processes import with category creation and feed validation
- User monitors progress through status API calls
- System completes import with detailed success/failure report
- User reviews import results and resolves any failed feeds
- Verify all imported feeds are functional and properly categorized

**Duplicate Handling Workflow**
- User imports OPML containing feeds already in their collection
- System detects duplicates and applies specified strategy
- User receives detailed report on duplicate handling decisions
- Verify data integrity maintained throughout duplicate processing
- Test all duplicate strategies (skip, update, merge) thoroughly

**Large Import Performance Test**
- Import OPML files with 500+ feeds and 50+ categories
- Verify system handles large imports without memory issues
- Monitor processing time and optimize for reasonable performance
- Test concurrent imports from multiple users
- Verify database performance under load

**Error Recovery Scenarios**
- Import OPML with mix of valid and invalid feeds
- Handle network interruptions during feed validation
- Process imports with malformed category structures
- Recover gracefully from database connection issues
- Continue processing after encountering invalid feeds

## Mocking Requirements

### External HTTP Requests
- **Mock aiohttp responses** for feed URL validation
  - Mock successful RSS/Atom feed responses with various content types
  - Mock HTTP redirects (301, 302) to test URL following
  - Mock network errors (timeout, connection refused, DNS failures)
  - Mock HTTP error responses (404, 500, invalid content)
  - Mock slow responses to test timeout handling

### Feed Content Parsing
- **Mock feedparser responses** for feed metadata extraction
  - Mock valid RSS feeds with complete metadata
  - Mock valid Atom feeds with different structures
  - Mock feeds with missing or invalid metadata
  - Mock feeds with unusual encoding or character sets
  - Mock feeds with large content to test parsing limits

### File System Operations
- **Mock file upload handling** for OPML file processing
  - Mock successful file uploads with various OPML structures
  - Mock oversized file uploads to test size limits
  - Mock corrupted file uploads to test error handling
  - Mock file reading errors during processing

### Database Operations
- **Mock database transactions** for atomic import operations
  - Mock successful database operations for happy path testing
  - Mock database constraint violations for duplicate handling
  - Mock database connection failures for error recovery testing
  - Mock transaction rollback scenarios for data integrity testing

### Time-Based Operations
- **Mock datetime functions** for timestamp and expiration testing
  - Mock current time for consistent test results
  - Mock time progression for progress tracking tests
  - Mock timeout scenarios for long-running operations
  - Mock expiration logic for import job cleanup

### Background Job Processing
- **Mock async task execution** for import job processing
  - Mock successful job completion for integration tests
  - Mock job failure scenarios for error handling tests
  - Mock job cancellation for user-initiated cancellation tests
  - Mock concurrent job processing for load testing

### Authentication Context
- **Mock user authentication** for API endpoint testing
  - Mock authenticated user sessions for authorized operations
  - Mock unauthenticated requests for security testing
  - Mock different user contexts for multi-user scenarios
  - Mock invalid authentication tokens for error scenarios