# Spec Requirements Document

> Spec: Search Functionality Implementation and UI Fixes
> Created: 2025-08-24
> Status: Planning

## Overview

Implement complete search functionality by connecting existing search inputs to the backend API, fix search input positioning in the header, and provide a comprehensive search experience with features like search suggestions, recent searches, and advanced filtering.

## User Stories

### Article Search and Discovery

As an RSS reader user, I want to search for articles by title, content, or author, so that I can quickly find specific information across all my feeds without manually browsing through articles.

Users will be able to type search queries into the existing search inputs and see real-time filtered results. The search will work across article titles, content, and authors, and integrate seamlessly with existing category and feed filtering. This solves the current problem where search inputs exist but don't function.

### Improved Search Experience

As a user, I want search suggestions, recent search history, and the ability to clear searches easily, so that I can efficiently discover content and reuse previous searches.

The search system will provide autocomplete suggestions, maintain search history, and offer quick access to clear or modify searches. Advanced users can combine search with category/feed filters for precise content discovery.

## Spec Scope

1. **Connect search inputs to backend API** - Wire up existing search inputs to perform actual searches
2. **Fix header layout positioning** - Move desktop search input to right side of header for proper alignment
3. **Real-time search with debouncing** - Implement responsive search that updates results as user types
4. **Search state management** - Proper integration with existing filter and pagination systems  
5. **Search enhancements** - Add search suggestions, recent searches, and clear functionality

## Out of Scope

- Advanced search operators (Boolean logic, field-specific search)
- Full-text search indexing (use existing database search)
- Search result highlighting in article content
- Search analytics and popularity tracking

## Expected Deliverable

1. Search inputs function properly and return filtered article results
2. Header layout shows search input properly positioned on desktop
3. Search integrates seamlessly with existing filtering and pagination systems

## Current Implementation Analysis

The search infrastructure is partially implemented but disconnected:

### Backend Implementation (✅ Complete)

The backend in `/Users/haraldfauland/Projects/zib/backend/app/routes/article.py` already supports search:

```python
if params.search:
    # Use LIKE for case-insensitive search
    search_pattern = f'%{params.search}%'
    query = query.where(
        (Article.title ** search_pattern) |
        (Article.content ** search_pattern)
    )
```

**Features Already Working:**
- Search across article titles and content
- Case-insensitive search with LIKE patterns
- Integration with existing filtering (categories, read status)
- Search parameter in filtered counts endpoint

### Frontend Issues (❌ Needs Implementation)

1. **Search Inputs Not Connected**: In `/Users/haraldfauland/Projects/zib/frontend/src/lib/components/Header.svelte` (lines 44-72), search inputs exist but have no event handlers or store integration.

2. **Store Integration Missing**: `searchQuery` store exists but Header component doesn't use it.

3. **Layout Positioning Problem**: Desktop search input (lines 60-72) uses `flex-1 max-w-md ml-8` which positions it next to the logo instead of right-aligned.

4. **No Search Functionality**: Typing in search inputs doesn't trigger any search operations.

### Current CSS Layout Issue

```svelte
<!-- Desktop Search - CURRENT (WRONG POSITIONING) -->
<div class="flex-1 max-w-md ml-8">
  <div class="relative">
    <input type="text" placeholder="Search articles..." ... />
  </div>
</div>
```

**Problem**: `flex-1` expands from the logo position instead of right-aligning.

**Solution Needed**: Move search to right side with proper spacing from content.

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-24-search-functionality/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-24-search-functionality/sub-specs/technical-spec.md