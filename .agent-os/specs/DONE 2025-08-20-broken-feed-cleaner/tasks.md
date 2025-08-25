# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-20-broken-feed-cleaner/spec.md

> Created: 2025-08-20
> Status: Ready for Implementation

## Tasks

- [x] 1. Database Schema Implementation
  - [x] 1.1 Write tests for feed accessibility tracking fields
  - [x] 1.2 Create migration to add last_checked, accessible, consecutive_failures columns to feeds table
  - [x] 1.3 Create feed_check_logs table with proper indexes and foreign keys
  - [x] 1.4 Create Peewee model for FeedCheckLog with appropriate relationships
  - [x] 1.5 Verify all tests pass for database schema changes

- [x] 2. Feed Health Service Implementation
  - [x] 2.1 Write tests for feed connectivity checking logic
  - [x] 2.2 Implement async feed accessibility checker using httpx
  - [x] 2.3 Create FeedCheckSession class for progress tracking
  - [x] 2.4 Implement feed status update logic with consecutive failure counting
  - [x] 2.5 Create feed check logging service
  - [x] 2.6 Verify all tests pass for feed health service

- [x] 3. Backend API Endpoints
  - [x] 3.1 Write tests for feed checking API endpoints
  - [x] 3.2 Implement POST /api/feeds/check-category/{category_id} endpoint
  - [x] 3.3 Implement GET /api/feeds/check-status/{session_id} endpoint
  - [x] 3.4 Implement GET /api/feeds/broken/{category_id} endpoint
  - [x] 3.5 Implement DELETE /api/feeds/bulk-delete endpoint
  - [x] 3.6 Implement GET /api/feeds/{feed_id}/check-history endpoint
  - [x] 3.7 Verify all tests pass for API endpoints

- [x] 4. Frontend Settings Page Integration
  - [ ] 4.1 Write tests for Check Feeds button component
  - [x] 4.2 Add "Check feeds" button next to category delete button
  - [x] 4.3 Implement feed checking progress feedback UI
  - [x] 4.4 Create check results summary display
  - [x] 4.5 Add API client functions for feed health endpoints
  - [ ] 4.6 Verify all tests pass for settings page integration

- [x] 5. Cleanup Modal Implementation  
  - [ ] 5.1 Write tests for broken feeds cleanup modal
  - [x] 5.2 Create reusable modal component for broken feed cleanup
  - [x] 5.3 Implement broken feeds list with selection checkboxes
  - [x] 5.4 Add feed history details display (tooltip or expandable)
  - [x] 5.5 Implement bulk delete confirmation and execution
  - [x] 5.6 Add modal open/close integration with check feeds workflow
  - [ ] 5.7 Verify all tests pass for cleanup modal