# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-24-reading-time-estimates/spec.md

> Created: 2025-08-24
> Status: Ready for Implementation

## Tasks

- [ ] 1. Backend Reading Time Calculation
  - [ ] 1.1 Write tests for reading time calculation functions
  - [ ] 1.2 Create migration to add reading_time_minutes field to articles table
  - [ ] 1.3 Implement word counting algorithm with HTML tag stripping
  - [ ] 1.4 Add reading time calculation to article creation and update processes
  - [ ] 1.5 Update existing articles with calculated reading times
  - [ ] 1.6 Verify reading time calculations are accurate and performant

- [ ] 2. User Settings Integration
  - [ ] 2.1 Write tests for reading speed settings functionality
  - [ ] 2.2 Add reading_speed_wpm field to user settings model
  - [ ] 2.3 Create settings API endpoints for reading speed preferences
  - [ ] 2.4 Implement recalculation of reading times when user changes speed
  - [ ] 2.5 Add preset reading speed options (slow, average, fast, very fast)
  - [ ] 2.6 Verify settings changes properly update all article reading times

- [ ] 3. API Response Enhancement
  - [ ] 3.1 Write tests for reading time in API responses
  - [ ] 3.2 Add reading_time_minutes to all article API endpoints
  - [ ] 3.3 Include formatted reading time display strings in responses
  - [ ] 3.4 Handle edge cases (very short articles, missing content)
  - [ ] 3.5 Add reading time to search and filtered article responses
  - [ ] 3.6 Verify reading times appear correctly in all API responses

- [ ] 4. Frontend Display Implementation
  - [ ] 4.1 Write tests for reading time display components
  - [ ] 4.2 Add reading time display to article cards in main feed view
  - [ ] 4.3 Include reading time in article modal header
  - [ ] 4.4 Implement smart formatting for different time ranges
  - [ ] 4.5 Add reading speed settings to user preferences page
  - [ ] 4.6 Verify reading times display consistently across all views

- [ ] 5. Content Priority and Full-Text Integration
  - [ ] 5.1 Write tests for reading time with different content sources
  - [ ] 5.2 Update reading time calculation to prioritize full_text_content
  - [ ] 5.3 Handle cases where full text extraction provides different word counts
  - [ ] 5.4 Recalculate reading times when full text extraction completes
  - [ ] 5.5 Add logic to update reading times for articles with new full text
  - [ ] 5.6 Verify reading times are most accurate based on available content