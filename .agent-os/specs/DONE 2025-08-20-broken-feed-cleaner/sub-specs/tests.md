# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-08-20-broken-feed-cleaner/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Test Coverage

### Unit Tests

**FeedHealthController**
- test_check_category_feeds_creates_session
- test_check_category_feeds_invalid_category
- test_get_check_status_active_session
- test_get_check_status_nonexistent_session
- test_get_broken_feeds_with_7_day_threshold
- test_get_broken_feeds_empty_result
- test_bulk_delete_feeds_success
- test_bulk_delete_feeds_partial_failure
- test_get_feed_check_history_pagination

**FeedCheckService**
- test_check_feed_accessibility_success_200
- test_check_feed_accessibility_success_301_redirect
- test_check_feed_accessibility_failure_404
- test_check_feed_accessibility_timeout
- test_check_feed_accessibility_connection_error
- test_check_feed_accessibility_ssl_error
- test_update_feed_status_accessible_to_inaccessible
- test_update_feed_status_consecutive_failures_increment
- test_log_feed_check_result

**FeedCheckSession**
- test_session_creation_with_feed_ids
- test_session_progress_tracking
- test_session_completion_status
- test_session_concurrent_feed_checking
- test_session_error_handling

**Database Models**
- test_feed_check_log_creation
- test_feed_accessibility_fields
- test_foreign_key_cascade_deletion
- test_feed_broken_query_7_days
- test_feed_check_history_query

### Integration Tests

**Feed Checking Workflow**
- test_complete_category_feed_check_workflow
- test_check_feeds_updates_database_status
- test_broken_feeds_appear_in_cleanup_modal
- test_bulk_deletion_removes_feeds_and_articles

**API Endpoints**
- test_post_check_category_returns_session_id
- test_get_check_status_shows_progress
- test_get_broken_feeds_filtered_by_days
- test_delete_bulk_feeds_removes_from_database
- test_feed_check_history_includes_recent_attempts

**Database Operations**
- test_migration_adds_feed_health_columns
- test_feed_check_logs_table_creation
- test_indexes_created_for_performance
- test_cascade_deletion_cleanup

### Feature Tests

**Settings Page Integration**
- test_check_feeds_button_appears_next_to_delete
- test_check_feeds_button_click_starts_checking
- test_progress_feedback_during_checking
- test_completion_summary_shows_results

**Cleanup Modal**
- test_modal_opens_with_broken_feeds_list
- test_feed_selection_checkboxes_work
- test_delete_selected_feeds_confirmation
- test_keep_all_feeds_closes_modal
- test_feed_history_tooltip_details

**Error Handling**
- test_network_timeout_marks_feed_inaccessible
- test_dns_error_marks_feed_inaccessible
- test_http_error_codes_mark_feed_inaccessible
- test_ssl_certificate_error_handling
- test_malformed_url_error_handling

## Mocking Requirements

**HTTP Requests**
- Mock httpx.AsyncClient for feed connectivity tests
- Simulate various HTTP response codes (200, 301, 404, 500, timeout)
- Mock network exceptions (ConnectionError, TimeoutError, SSLError)

**Database Operations**
- Mock Peewee model operations for unit tests
- Use in-memory SQLite database for integration tests
- Mock migration operations for schema tests

**Time-based Tests**
- Mock datetime.now() for testing 7-day thresholds
- Mock time.time() for response time measurements
- Use freezegun for time-sensitive test scenarios

**Background Tasks**
- Mock asyncio task creation and execution
- Simulate concurrent feed checking scenarios
- Mock session storage and cleanup operations

## Test Data Setup

### Feed Test Data
```python
# Accessible feed
accessible_feed = {
    "id": 1,
    "title": "Working Feed",
    "url": "https://example.com/working-rss.xml",
    "accessible": True,
    "last_checked": datetime.now() - timedelta(hours=1),
    "consecutive_failures": 0
}

# Broken feed (7+ days)
broken_feed = {
    "id": 2,
    "title": "Broken Feed",
    "url": "https://broken.example.com/rss.xml",
    "accessible": False,
    "last_checked": datetime.now() - timedelta(days=8),
    "consecutive_failures": 15
}
```

### Check Log Test Data
```python
# Successful check log
success_log = {
    "feed_id": 1,
    "checked_at": datetime.now(),
    "status_code": 200,
    "is_success": True,
    "response_time_ms": 850
}

# Failed check log
failure_log = {
    "feed_id": 2,
    "checked_at": datetime.now(),
    "error_message": "Connection timeout",
    "is_success": False,
    "response_time_ms": 10000
}
```

## Performance Tests

**Concurrent Feed Checking**
- Test checking 50+ feeds simultaneously
- Measure response times and memory usage
- Verify no database connection exhaustion

**Large Dataset Handling**
- Test with categories containing 100+ feeds
- Test broken feeds query with large check log history
- Verify pagination performance for check history

**Session Management**
- Test multiple simultaneous check sessions
- Verify session cleanup after expiration
- Test memory usage with long-running sessions