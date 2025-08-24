# Spec Requirements Document

> Spec: Full Text Extraction from RSS Sources
> Created: 2025-08-24
> Status: Planning

## Overview

Implement full-text extraction from RSS feed sources using newspaper4k to provide complete article content when RSS feeds only contain summaries or partial text. This feature will enhance the reading experience by giving users access to full articles without leaving the RSS reader.

## User Stories

### Enhanced Article Reading

As a RSS reader user, I want to read complete articles within the application, so that I can consume full content without navigating to external websites.

The system will automatically attempt to extract full text from article URLs when RSS feeds only provide summaries. Users will see a "Full Text" indicator when extraction is available, and can toggle between RSS content and extracted full text. This solves the common problem of RSS feeds that only provide article summaries, forcing users to click through to read complete content.

## Spec Scope

1. **Automatic full-text extraction** - Extract complete article text from RSS article URLs using newspaper4k
2. **Background processing** - Process extraction jobs asynchronously without blocking RSS feed updates
3. **Storage system** - Store extracted full text with metadata and extraction status
4. **Fallback handling** - Gracefully handle extraction failures while preserving original RSS content
5. **API integration** - Provide endpoints to access extracted content and trigger manual extraction

## Out of Scope

- Frontend UI changes for displaying full text (separate implementation)
- Text summarization or AI processing of extracted content
- Custom scraping rules for specific websites
- User configuration for extraction preferences
- Bulk re-extraction of existing articles

## Expected Deliverable

1. Articles have extracted full text available when extraction succeeds
2. RSS feed processing continues normally even when extraction fails
3. API endpoints provide access to both RSS content and extracted full text

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-24-full-text-extraction/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-24-full-text-extraction/sub-specs/technical-spec.md
- API Specification: @.agent-os/specs/2025-08-24-full-text-extraction/sub-specs/api-spec.md
- Database Schema: @.agent-os/specs/2025-08-24-full-text-extraction/sub-specs/database-schema.md
- Tests Specification: @.agent-os/specs/2025-08-24-full-text-extraction/sub-specs/tests.md