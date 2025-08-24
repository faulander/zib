# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-24-full-text-extraction/spec.md

> Created: 2025-08-24
> Status: Ready for Implementation

## Tasks

- [ ] 1. Database Schema and Migration Implementation
  - [ ] 1.1 Write tests for new Article model fields and ExtractionJob model
  - [ ] 1.2 Create migration script for article extraction fields
  - [ ] 1.3 Create extraction_jobs table with proper indexes
  - [ ] 1.4 Update Article model with new extraction fields and enums
  - [ ] 1.5 Create ExtractionJob model with relationships and validation
  - [ ] 1.6 Verify all tests pass and migration works correctly

- [ ] 2. Newspaper4k Integration and Extraction Service
  - [ ] 2.1 Write tests for ExtractorService class with mocked newspaper4k
  - [ ] 2.2 Install and configure newspaper4k dependency
  - [ ] 2.3 Implement ExtractorService with URL validation and text extraction
  - [ ] 2.4 Add rate limiting, timeout handling, and User-Agent management
  - [ ] 2.5 Implement content validation and quality checks
  - [ ] 2.6 Verify extraction works with various article types and handles failures gracefully

- [ ] 3. Background Job Processing System
  - [ ] 3.1 Write tests for ExtractionJobManager and background worker
  - [ ] 3.2 Implement job queue management with priority and retry logic
  - [ ] 3.3 Create background worker with asyncio for non-blocking processing
  - [ ] 3.4 Add exponential backoff retry mechanism for failed extractions
  - [ ] 3.5 Implement worker start/stop controls and graceful shutdown
  - [ ] 3.6 Verify background processing works without blocking RSS feed updates

- [ ] 4. API Endpoints Implementation
  - [ ] 4.1 Write tests for all new extraction-related API endpoints
  - [ ] 4.2 Implement GET /api/articles/{article_id}/full-text endpoint
  - [ ] 4.3 Implement POST /api/articles/{article_id}/extract endpoint with rate limiting
  - [ ] 4.4 Implement extraction status and job management endpoints
  - [ ] 4.5 Enhance existing article endpoints to include extraction information
  - [ ] 4.6 Verify all endpoints work correctly and handle errors gracefully

- [ ] 5. RSS Feed Integration and Automatic Job Creation
  - [ ] 5.1 Write tests for automatic extraction job creation during RSS processing
  - [ ] 5.2 Integrate job creation into existing RSS feed update workflow
  - [ ] 5.3 Ensure RSS processing remains fast and non-blocking
  - [ ] 5.4 Add extraction job creation for OPML import articles
  - [ ] 5.5 Test that extraction failures do not affect RSS functionality
  - [ ] 5.6 Verify complete integration with existing RSS reader features