# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-20-broken-feed-cleaner/spec.md

> Created: 2025-08-20
> Version: 1.0.0

## Technical Requirements

- **Feed connectivity testing** - HTTP HEAD requests to feed URLs with 10-second timeout
- **Database accessibility tracking** - Update existing feeds table with last_checked and accessible fields
- **Feed check history logging** - New table to store check attempts, timestamps, and results
- **Asynchronous feed checking** - Non-blocking requests that don't freeze the UI during checks
- **7-day broken feed detection** - Query logic to identify feeds inaccessible for ≥7 days
- **Modal UI component** - Reusable modal for displaying broken feed cleanup options
- **Category-scoped checking** - Only check feeds within the selected category
- **Real-time status updates** - WebSocket or polling to show check progress in UI

## Approach Options

**Option A:** Synchronous Feed Checking
- Pros: Simple implementation, immediate results
- Cons: UI blocking, poor user experience with many feeds, timeout issues

**Option B:** Asynchronous Feed Checking with Progress Updates (Selected)
- Pros: Non-blocking UI, progress feedback, better error handling, scalable
- Cons: More complex implementation, requires progress tracking

**Option C:** Background Job Queue System
- Pros: Complete separation from UI, retry logic, job persistence
- Cons: Over-engineered for this use case, complex setup, delayed feedback

**Rationale:** Option B provides the best balance of user experience and implementation complexity. Users get immediate feedback without UI blocking, and the async approach scales well with feed count.

## External Dependencies

- **httpx** - Already used in the project for HTTP requests with async support
- **asyncio** - Built-in Python library for asynchronous operations
- **Peewee ORM** - Already used for database operations

**Justification:** All dependencies are already present in the project, no new libraries needed.

## Database Schema Design

**Approach:** Extend existing feeds table + add new feed_check_logs table

### Feed Table Extensions
- Add `last_checked: datetime` field to track last check attempt
- Add `accessible: boolean` field to track current accessibility status
- Add `consecutive_failures: integer` field to track failure streak

### New Feed Check Logs Table
- Primary key for log entries
- Foreign key to feeds table
- Timestamp of check attempt
- HTTP status code or error message
- Response time measurement
- Check result (success/failure)

## API Endpoint Design

### POST /api/feeds/check-category/{category_id}
- Initiates feed checking for all feeds in category
- Returns check session ID for progress tracking
- Asynchronous processing with immediate response

### GET /api/feeds/check-status/{session_id}
- Returns progress of ongoing feed check operation
- JSON response with completed/total counts and current status

### GET /api/feeds/broken/{category_id}
- Returns list of feeds broken for 7+ days in category
- Includes feed details and failure history
- Used to populate cleanup modal

### DELETE /api/feeds/bulk-delete
- Accepts array of feed IDs for deletion
- Returns success/failure status for each deletion
- Used by cleanup modal for bulk operations

## Frontend Implementation

### Check Feeds Button
- Add button next to category delete button in settings
- Show loading state during check operation
- Display check results summary after completion

### Progress Feedback
- Show progress bar or spinner during checking
- Update with "Checking feed X of Y" messages
- Display final summary of accessible/inaccessible feeds

### Cleanup Modal Component
- Table view of broken feeds with details
- Checkboxes for selecting feeds to delete
- "Delete Selected" and "Keep All" action buttons
- Feed history details on hover or expand

## Error Handling Strategy

- Network timeout: 10-second timeout per feed, mark as inaccessible
- HTTP errors: Status codes 400+ marked as inaccessible
- DNS resolution failures: Mark as inaccessible
- SSL/TLS errors: Mark as inaccessible, log specific error
- Unexpected exceptions: Log error, continue with next feed