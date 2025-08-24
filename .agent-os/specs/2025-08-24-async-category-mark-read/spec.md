# Spec Requirements Document

> Spec: Asynchronous Category Mark-as-Read Operations
> Created: 2025-08-24
> Status: Planning

## Overview

Implement asynchronous processing for bulk mark-as-read operations, particularly when marking entire categories as read, to improve user experience by preventing long-running requests that block the interface.

## User Stories

### Fast Category Mark-as-Read

As an RSS reader user with many articles in categories, I want marking a category as read to be fast and non-blocking, so that I can continue using the interface while the operation completes in the background.

Users will initiate a mark-as-read operation and receive immediate feedback that the process has started. The system will process the articles in the background and update the UI as articles are marked as read. This solves the current problem where marking large categories as read takes several seconds and blocks the interface.

## Spec Scope

1. **Asynchronous job processing** - Convert bulk mark-as-read operations to background jobs that don't block API requests
2. **Immediate response system** - Return job status immediately and allow tracking of progress
3. **Real-time UI updates** - Update article counts and status in the UI as articles are processed
4. **Batch processing optimization** - Use efficient database operations to mark articles in batches
5. **Progress tracking** - Show users progress of large mark-as-read operations

## Out of Scope

- Complex distributed job queue systems (Redis, Celery)
- Mark-as-read operations for individual articles (keep synchronous)
- Bulk operations for feeds (focus on categories first)
- Persistent job storage across application restarts

## Expected Deliverable

1. Category mark-as-read operations return immediately with job tracking information
2. Large categories are marked as read efficiently in the background without blocking the UI
3. Users receive real-time feedback about the progress of bulk operations

## Current Implementation Analysis

The current implementation in `/Users/haraldfauland/Projects/zib/backend/app/routes/article.py` (lines 414-451) has these performance issues:

### Current Problems

1. **Synchronous Processing**: The endpoint processes articles in a sequential for loop:
   ```python
   for article in articles:
       ReadStatus.mark_read(current_user, article, True)
       updated_count += 1
   ```

2. **Blocking Request**: Large categories with hundreds of articles take several seconds, blocking the HTTP request and frontend UI.

3. **Inefficient Database Operations**: Each article requires individual database operations instead of batch processing.

4. **No Progress Feedback**: Users have no indication of progress during long operations.

### Performance Impact

- Categories with 100+ articles take 3-5 seconds
- Categories with 500+ articles take 10-20 seconds  
- Frontend shows loading spinner during entire operation
- No ability to cancel or track progress of operation

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-24-async-category-mark-read/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-24-async-category-mark-read/sub-specs/technical-spec.md
- API Specification: @.agent-os/specs/2025-08-24-async-category-mark-read/sub-specs/api-spec.md
- Database Schema: @.agent-os/specs/2025-08-24-async-category-mark-read/sub-specs/database-schema.md