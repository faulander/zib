# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-20-broken-feed-cleaner/spec.md

> Created: 2025-08-20
> Status: Ready for Implementation

## Tasks

- [ ] 1. Database Schema Implementation
  - [ ] 1.1 Write tests for feed accessibility tracking fields
  - [ ] 1.2 Create migration to add last_checked, accessible, consecutive_failures columns to feeds table
  - [ ] 1.3 Create feed_check_logs table with proper indexes and foreign keys
  - [ ] 1.4 Create Peewee model for FeedCheckLog with appropriate relationships
  - [ ] 1.5 Verify all tests pass for database schema changes

- [ ] 2. Feed Health Service Implementation
  - [ ] 2.1 Write tests for feed connectivity checking logic
  - [ ] 2.2 Implement async feed accessibility checker using httpx
  - [ ] 2.3 Create FeedCheckSession class for progress tracking
  - [ ] 2.4 Implement feed status update logic with consecutive failure counting
  - [ ] 2.5 Create feed check logging service
  - [ ] 2.6 Verify all tests pass for feed health service

- [ ] 3. Backend API Endpoints
  - [ ] 3.1 Write tests for feed checking API endpoints
  - [ ] 3.2 Implement POST /api/feeds/check-category/{category_id} endpoint
  - [ ] 3.3 Implement GET /api/feeds/check-status/{session_id} endpoint
  - [ ] 3.4 Implement GET /api/feeds/broken/{category_id} endpoint
  - [ ] 3.5 Implement DELETE /api/feeds/bulk-delete endpoint
  - [ ] 3.6 Implement GET /api/feeds/{feed_id}/check-history endpoint
  - [ ] 3.7 Verify all tests pass for API endpoints

- [ ] 4. Frontend Settings Page Integration
  - [ ] 4.1 Write tests for Check Feeds button component
  - [ ] 4.2 Add "Check feeds" button next to category delete button
  - [ ] 4.3 Implement feed checking progress feedback UI
  - [ ] 4.4 Create check results summary display
  - [ ] 4.5 Add API client functions for feed health endpoints
  - [ ] 4.6 Verify all tests pass for settings page integration

- [ ] 5. Cleanup Modal Implementation  
  - [ ] 5.1 Write tests for broken feeds cleanup modal
  - [ ] 5.2 Create reusable modal component for broken feed cleanup
  - [ ] 5.3 Implement broken feeds list with selection checkboxes
  - [ ] 5.4 Add feed history details display (tooltip or expandable)
  - [ ] 5.5 Implement bulk delete confirmation and execution
  - [ ] 5.6 Add modal open/close integration with check feeds workflow
  - [ ] 5.7 Verify all tests pass for cleanup modal