# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-08-22-opml-import-export-improvements/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Test Coverage

### Unit Tests

**ImportProcessor Performance Tests**
- Test batch feed creation with 200+ feeds completes under 2 minutes
- Test concurrent feed validation with configurable semaphore limits
- Test optimized duplicate detection with pre-loaded data structures
- Test progress update batching reduces database calls
- Test memory usage stays reasonable during large imports

**OPMLExporter Tests** 
- Test OPML XML generation produces valid OPML 2.0 format
- Test category hierarchy is properly nested in XML structure
- Test export filtering by category IDs works correctly
- Test large dataset export uses streaming without memory issues
- Test XML encoding handles special characters properly

**WebSocket Progress Tests**
- Test WebSocket connection establishment and authentication
- Test progress message format matches API specification
- Test connection cleanup on job completion/failure
- Test multiple concurrent WebSocket connections for different jobs
- Test WebSocket message ordering and delivery guarantees

**Database Optimization Tests**
- Test new indexes improve query performance for duplicate detection
- Test batch operations significantly faster than individual operations  
- Test transaction management ensures data consistency during imports
- Test SQLite PRAGMA settings improve import performance
- Test foreign key constraints maintain referential integrity

### Integration Tests

**End-to-End Import Performance**
- Test complete import workflow with 200 feeds completes under 2 minutes
- Test progress updates are delivered via WebSocket in real-time
- Test import can be cancelled mid-process with proper cleanup
- Test database rollback works correctly on import failures
- Test import job status accurately reflects progress and completion

**Export Workflow Integration**
- Test OPML export endpoint generates valid downloadable file
- Test export options endpoint returns correct feed/category counts
- Test exported OPML can be re-imported successfully
- Test export filtering produces correct subset of feeds
- Test export filename generation includes timestamp

**Frontend-Backend Integration**
- Test progress modal displays real-time updates from WebSocket
- Test cancel button properly terminates import job and closes WebSocket
- Test export button triggers download of correctly formatted OPML file
- Test error states display user-friendly messages
- Test import summary shows detailed results after completion

**API Endpoint Integration**
- Test enhanced import job status endpoint returns all new fields
- Test WebSocket endpoint requires proper authentication
- Test export endpoint handles large datasets without timeout
- Test concurrent import jobs don't interfere with each other
- Test API error responses provide actionable information

### Feature Tests

**Large OPML Import Scenarios**
- Test importing 200+ feeds with nested categories
- Test handling OPML files with various encoding formats (UTF-8, UTF-16)
- Test importing OPML with malformed XML recovers gracefully
- Test importing OPML with duplicate feeds/categories handles correctly
- Test importing OPML with invalid feed URLs continues processing

**Progress Tracking Scenarios**  
- Test progress modal shows all phases: parsing, validating, creating, importing
- Test progress percentage calculation is accurate throughout process
- Test ETA calculation updates dynamically based on current performance
- Test current item name displays correctly for feeds and categories
- Test phase transitions update UI indicators properly

**Export Functionality Scenarios**
- Test exporting all feeds produces complete OPML with all categories
- Test exporting specific categories includes only selected feeds
- Test exporting feeds without categories creates proper OPML structure
- Test export with empty category produces valid but minimal OPML
- Test export download triggers browser save dialog

**Error Handling Scenarios**
- Test network timeout during feed validation doesn't stop import
- Test database connection issues during import provide clear errors  
- Test WebSocket connection drop gracefully degrades to polling
- Test cancelled import properly cleans up partial data
- Test export failure provides detailed error message

## Mocking Requirements

**External HTTP Requests**
- **Feed Validation Service**: Mock HTTP requests to feed URLs for validation testing
- **Mock Strategy**: Use `httpx` mock adapter to simulate various feed response scenarios:
  - Valid RSS/Atom feeds returning 200 OK
  - Invalid feeds returning 404 Not Found  
  - Timeout scenarios for slow feeds
  - Malformed XML responses
  - Redirected feeds (301/302 responses)

**WebSocket Connections**
- **WebSocket Client**: Mock WebSocket connections for testing progress updates
- **Mock Strategy**: Use `pytest-asyncio` with mock WebSocket client to simulate:
  - Connection establishment and authentication
  - Message sending and receiving
  - Connection drops and reconnections
  - Multiple concurrent connections

**Database Operations**
- **SQLite Database**: Use in-memory SQLite database for unit tests
- **Mock Strategy**: Use `pytest` fixtures to create/teardown test database:
  - Pre-populate with test data for duplicate detection tests
  - Create clean database for import workflow tests
  - Test both empty and populated database scenarios

**File System Operations**  
- **OPML File Upload**: Mock file upload for import testing
- **Mock Strategy**: Use `pytest` `tmp_path` fixture for temporary files:
  - Create test OPML files with various structures
  - Test file size limits and validation
  - Test various file encodings

**Time-Based Operations**
- **Import Duration**: Mock time for performance testing
- **Mock Strategy**: Use `pytest` `freezegun` or manual time mocking:
  - Control time progression during import tests
  - Test ETA calculations with predictable timing
  - Test timeout scenarios

## Test Data Requirements

**Sample OPML Files**
- Small OPML (10 feeds, 3 categories) for basic functionality tests
- Large OPML (200+ feeds, 20+ categories) for performance tests  
- Malformed OPML with XML errors for error handling tests
- OPML with duplicate feeds/categories for duplicate detection tests
- OPML with various encodings (UTF-8, UTF-16) for encoding tests

**Database Test Data**
- Pre-populated database with existing feeds/categories for duplicate testing
- Empty database for clean import testing
- Database with broken foreign key references for integrity testing
- Large dataset for export performance testing

**WebSocket Test Messages**
- Sample progress update messages in correct JSON format
- Error message samples for various failure scenarios
- Completion message samples with summary data
- Authentication failure messages for security testing

## Performance Test Thresholds

**Import Performance Targets**
- 200 feeds import must complete in under 120 seconds
- Memory usage must stay under 256MB during import
- Database connections must not exceed 10 concurrent connections
- Progress updates must be delivered within 1 second of actual progress

**Export Performance Targets**  
- Export of 200 feeds must complete in under 30 seconds
- Export file generation must not exceed 128MB memory usage
- Large exports must use streaming to avoid memory spikes
- Export API response time must be under 5 seconds for file generation

**WebSocket Performance Targets**
- WebSocket connection establishment under 1 second
- Progress message delivery latency under 500ms
- WebSocket memory overhead under 10MB per connection
- Connection cleanup must complete within 5 seconds

## Test Environment Setup

**Backend Test Configuration**
```python
# pytest configuration for backend tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
TESTING = True
DISABLE_AUTH = True  # For unit tests only
WEBSOCKET_TEST_MODE = True
CONCURRENT_LIMIT = 2  # Reduce for test stability
```

**Frontend Test Configuration**
```javascript
// Vitest configuration for frontend tests
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    globals: true
  }
});
```

**Mock Service Configuration**
- Mock feed validation service responds within 100ms
- Mock WebSocket server accepts all connections
- Mock database returns predictable test data
- Mock file system allows all reasonable file operations

The test specification ensures comprehensive coverage of performance improvements, new functionality, and integration points while providing realistic test scenarios that validate the system works correctly under various conditions.