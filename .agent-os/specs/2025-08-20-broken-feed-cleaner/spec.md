# Spec Requirements Document

> Spec: Broken Feed Cleaner
> Created: 2025-08-20
> Status: Planning

## Overview

Implement an automated broken feed detection and cleanup system that allows users to identify and remove inaccessible RSS feeds. This feature will help maintain a healthy feed collection by tracking feed accessibility over time and providing a user-friendly interface for managing problematic feeds.

## User Stories

### Feed Health Monitoring

As a RSS reader user, I want to check which of my feeds are no longer accessible, so that I can maintain a clean and functional feed collection without manual testing.

**Detailed Workflow**: User clicks "Check feeds" button next to a category title in settings. System attempts to fetch all accessible feeds in that category, marks unresponsive feeds as inaccessible, and provides immediate feedback on feed health status.

### Automated Cleanup Recommendations

As a RSS reader user, I want to receive recommendations for feeds that have been broken for an extended period, so that I can decide whether to delete them or keep them for potential future recovery.

**Detailed Workflow**: When checking feeds, system identifies feeds that have been inaccessible for 7+ days and presents them in a modal dialog with deletion options. User can review each feed's history and choose to delete or keep individual feeds.

### Feed Accessibility Tracking

As a RSS reader user, I want to see the accessibility history of my feeds, so that I can understand patterns and make informed decisions about feed management.

**Detailed Workflow**: System maintains a log of feed check attempts, success/failure status, and timestamps. This data is displayed in the cleanup modal to help users make deletion decisions.

## Spec Scope

1. **"Check feeds" UI button** - Add button next to category delete button in settings
2. **Feed accessibility checker** - Background service that tests feed URLs for accessibility
3. **Database schema updates** - Add accessibility tracking and feed check history tables
4. **Feed status management** - Update feed accessibility status based on check results
5. **Cleanup modal interface** - Present long-term broken feeds with deletion options
6. **Feed check history tracking** - Log all check attempts with timestamps and results

## Out of Scope

- Automatic feed deletion without user consent
- Feed content quality analysis (only accessibility checking)
- Network timeout configuration (will use reasonable defaults)
- Bulk category checking (only per-category checking)
- Email notifications for broken feeds

## Expected Deliverable

1. **Functional "Check feeds" button** - Users can test all feeds in a category with single click
2. **Accurate feed status tracking** - Feeds marked as accessible/inaccessible based on real connectivity
3. **Cleanup recommendations modal** - Users see feeds broken for 7+ days with deletion options

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-20-broken-feed-cleaner/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-20-broken-feed-cleaner/sub-specs/technical-spec.md
- Database Schema: @.agent-os/specs/2025-08-20-broken-feed-cleaner/sub-specs/database-schema.md
- API Specification: @.agent-os/specs/2025-08-20-broken-feed-cleaner/sub-specs/api-spec.md
- Tests Specification: @.agent-os/specs/2025-08-20-broken-feed-cleaner/sub-specs/tests.md