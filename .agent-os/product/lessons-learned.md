# Lessons Learned

> Last Updated: 2025-08-20
> Version: 1.1.0

## Development Workflow

### Development Server
- **Never run the development server** - Dev server is already running in another terminal
- Always assume the dev environment is active and accessible
- Focus on code changes rather than server management

### Code Quality
- **Never mention AI involvement** in commits, comments, or documentation
- Write code and commit messages as if written by a human developer
- Focus on technical implementation details, not the development process

## Database Management

### SQLite Operations
- **Always check the SQLite database for structural questions**
- Use database inspection before making schema assumptions
- Verify existing tables, columns, and relationships before modifications
- Query the database directly to understand current data structure

### Migration System
- **NEVER manually create or delete database tables** - This breaks production deployments
- Always use the proper migration system (`uv run python -m app.core.migrations`) 
- The system must work automatically without user intervention in production
- Debug migration issues by fixing the migration files, not by manual table operations
- If tables are missing, the issue is in the migration system that needs to be fixed

## Frontend Development

### Svelte 5 Syntax
- **Always use Svelte 5 runes syntax** for reactive state management
- Use `$state()`, `$derived()`, `$effect()` instead of legacy reactive statements
- Prefer the new runes API over stores when possible

### Derived State
- **Use `derived.by` instead of `derived`** for derived state calculations
- `derived.by` is the preferred pattern for computed values
- This provides better performance and cleaner syntax

### Icons
- **Use Lucide Svelte for all icons** - Already installed and ready to use
- Import icons directly: `import { IconName } from '@lucide/svelte'`
- Package: `@lucide/svelte` (for Svelte 5), not `lucide-svelte` (Svelte 4)
- Icons are tree-shakable inline SVG components
- Customizable props: `size`, `color`, `strokeWidth`, `absoluteStrokeWidth`
- Default values: `size=24`, `color="currentColor"`, `strokeWidth=2`
- Replace custom SVG icons with Lucide components for consistency

## Code Patterns

### State Management
- Use `$state()` for component-level reactive variables
- Use `$derived.by()` for computed values based on other state
- Use `$effect()` for side effects and cleanup

### Database Queries
- Always verify table structure before writing queries
- Check existing column names and types
- Use proper SQLite syntax and constraints

### DateTime Handling
- **ALWAYS use pendulum, never datetime** - Throughout the codebase, use `pendulum.now('UTC').to_datetime_string()` for timestamps
- **Import pendulum, not datetime** - Any datetime operations should use pendulum for consistency
- **Model save() methods must use pendulum** - When overriding save() methods, use pendulum for `updated_at` fields
- **API serialization**: Use `str(field)` not `field.isoformat()` - Pendulum's `to_datetime_string()` returns strings, not datetime objects
- **Common mistakes**: 
  - Using `datetime.now()` causes "name 'datetime' is not defined" errors if datetime isn't imported
  - Using `.isoformat()` on pendulum strings causes "'str' object has no attribute 'isoformat'" errors

## Content Filtering & Pagination Architecture

### The Problem: Post-Query Content Filtering Breaks Pagination

**Issue Discovered**: Content filter rules (like Sport and PREMIUM filters) are applied **after** database queries in Python using `FilterService.apply_filters()`, not during SQL queries. This creates a fundamental pagination problem:

1. Backend fetches 50 articles from database
2. Content filters reduce them to ~10-15 articles  
3. Frontend receives fewer articles than expected
4. Infinite scroll stops working (`has_more: false`)
5. Users see only 22 articles instead of hundreds of available filtered articles

### The Solution: Smart Backend Pagination

**Implemented**: `fetch_filtered_articles_with_pagination()` function that:

1. **Iteratively fetches and filters** until reaching requested article count
2. **Adaptive batch sizing** - increases batch size when filters are aggressive (< 10% pass rate)
3. **Safety limits** - maximum 5 database queries per request to prevent infinite loops
4. **Accurate `has_more` calculation** - only false when truly no more articles exist
5. **Proper cursor management** - maintains pagination positions through filter iterations

### Key Technical Implementation

```python
# Smart pagination handles content filtering properly
articles_data, has_more, next_cursor = fetch_filtered_articles_with_pagination(
    query=query,
    user=current_user,
    category_id=params.category_id,
    requested_limit=params.limit,
    cursor=params.since_id
)
```

### Counter Accuracy Solution

**Problem**: Sidebar counters showed raw database counts (905) instead of filtered counts (34)
**Solution**: Created dedicated `/api/articles/filtered-counts` endpoint that applies content filters to count calculations

### Lessons for Future Development

1. **Content filters must be considered during pagination design** - Post-query filtering breaks cursor pagination
2. **Backend should handle filtering complexity** - Don't push filtering logic to frontend
3. **Always test with realistic filter scenarios** - Empty or minimal filters may not reveal pagination issues
4. **Performance vs accuracy tradeoff** - Smart pagination requires more database queries but ensures user experience
5. **Route ordering matters in FastAPI** - Specific routes (`/filtered-counts`) must come before parametric routes (`/{article_id}`)

### Performance Characteristics

- **Without content filters**: 1 database query per pagination request
- **With content filters**: 1-5 database queries per pagination request (adaptive)
- **Filter efficiency tracking**: Automatically adjusts batch sizes based on filter pass-through rates
- **Memory efficient**: Processes articles in batches rather than loading all at once

### Duplicate Article Prevention

**Issue**: Smart pagination can cause duplicate articles in Svelte `{#each}` blocks, leading to "each_key_duplicate" errors
**Solution**: Added duplicate detection in `fetch_filtered_articles_with_pagination()` to prevent articles from being added twice
**Root Cause**: Complex cursor logic in iterative fetching could theoretically create overlapping results

## Production Deployment

### SSH Access
- **Production server**: `ssh -i ~/.ssh/zib_deploy_key hf@192.168.42.167`
- **Backend container**: `zib-backend`
- **Frontend container**: `zib-frontend`

### Auto Refresh Service Debugging

**Issue Found (2025-08-21)**: Auto refresh service wasn't working in production despite being enabled in settings.

**Root Cause**: 
1. **Sleep-first logic**: Service would sleep for 5 minutes BEFORE doing first refresh, causing no immediate activity
2. **Stale user settings**: Async task held static user object, not reflecting UI setting changes
3. **Database connection issues**: Long-running async tasks might lose database connection

**Solution Implemented**:
- Changed to refresh-first, then sleep pattern for immediate activity
- Added dynamic user settings refresh in the loop using `User.get_by_id()`  
- Added database connection check and reconnection logic
- Improved logging to track refresh cycles and user setting updates

**Key Commands for Debugging**:
```bash
# Check container status
ssh -i ~/.ssh/zib_deploy_key hf@192.168.42.167 "docker ps | grep zib"

# Check backend logs for auto refresh activity
ssh -i ~/.ssh/zib_deploy_key hf@192.168.42.167 "docker logs zib-backend | grep -i 'auto-refresh'"

# Check current settings via API
ssh -i ~/.ssh/zib_deploy_key hf@192.168.42.167 "curl -s http://localhost:8000/api/settings/"
```

**Testing Pattern**: With 5-minute interval, expect to see refresh logs every 5 minutes after initial startup refresh.

### Auto-Refresh and Mark-as-Read-on-Scroll Integration

**Issue Found (2025-08-23)**: Auto-refresh was breaking the unread view by showing read articles and causing page jumps to the top.

**Root Causes**:
1. **Cursor reset during refresh**: `loadArticles()` was resetting `nextCursor` even during auto-refresh, causing complete page reloads
2. **Missing auto-refresh flag**: Some refresh calls weren't passing `isAutoRefresh=true`, so smart merging wasn't happening
3. **Filter-unaware merging**: `mergeArticlesForRefresh()` wasn't respecting current filter state, allowing read articles into unread view

**Solution Implemented**:
- Modified `refreshAllFeeds()` to pass `isAutoRefresh=true` to `loadArticles()`
- Updated `loadArticles()` to preserve cursor during auto-refresh (no reset when `isAutoRefresh=true`)
- Enhanced `mergeArticlesForRefresh()` to respect current filter:
  - For unread view: skip articles that became read
  - For unread view: don't add new read articles
  - Preserve existing article object references for DOM stability

**Key Technical Changes**:
```javascript
// Auto-refresh now preserves pagination cursor
if (!isAutoRefresh) {
  nextCursor.set(null);
}

// Smart merging respects filter state
const currentFilter = get(selectedFilter);
if (currentFilter === 'unread' && newArticle.read_status?.is_read) {
  continue; // Skip read articles in unread view
}
```

**Result**: Auto-refresh now maintains scroll position, doesn't show inappropriate articles, and preserves user's reading context.

**Critical Development Rule**: When making ANY changes to the frontend article management, pagination, or DOM manipulation code, you MUST verify that both feed refresh and auto-mark-read-on-scroll continue to work correctly. These are core features that users depend on and breaking them creates a poor user experience. Always test both features after making changes to:
- Article loading and pagination
- DOM element handling in article lists
- Svelte store updates and reactivity
- Auto-refresh and smart merging logic

### Mark-as-Read Infinite Scroll Bug Fix

**Issue Found (2025-08-23)**: Mark-as-read functionality was breaking infinite scroll pagination by removing articles from the local list, causing the list length to shrink and trigger premature "load more" requests.

**Root Cause**: When articles were marked as read in unread view, they were being **removed from the articlesStore** (line 435 in api.js). This caused:
1. Load 50 articles → user scrolls → 20 articles marked as read and **removed from list**
2. List now has 30 articles instead of 50
3. Infinite scroll triggers at position 25-30 instead of position 40-50 
4. System tries to load more articles prematurely, breaking pagination logic

**Solution Implemented**:
- **Never remove articles from articlesStore** when marking as read
- Always update read status in place: `articlesStore.update(current => current.map(...))`
- Add **frontend filtering** with derived stores to show appropriate articles based on current filter
- Backend continues to filter at API level, frontend adds complementary filtering for locally modified articles

**Key Technical Changes**:
```javascript
// OLD - Removed articles from store (WRONG)
if (shouldRemove) {
  articlesStore.update(current => current.filter(article => article.id !== articleId));
}

// NEW - Always update in place, never remove (CORRECT)  
articlesStore.update(current => 
  current.map(article => 
    article.id === articleId ? { ...article, read_status: { ...article.read_status, is_read: isRead } } : article
  )
);

// NEW - Frontend filtering with derived stores
let articles = $derived.by(() => {
  if (currentFilter === 'unread') {
    return allArticles.filter(article => !article.read_status?.is_read);
  }
  return allArticles;
});
```

**Result**: Infinite scroll now works correctly with mark-as-read functionality. Articles maintain stable list positions while being filtered appropriately for each view.

### Mark-as-Read-on-Scroll Implementation Success

**Final Implementation (2025-08-23)**: After debugging and testing, the simplified mark-as-read-on-scroll functionality is working perfectly with these key insights:

**Optimal Settings (No User Configuration Needed)**:
- **Batch Size**: 3 articles (responsive batching)  
- **Scroll Delay**: 800ms (comfortable reading pace)
- **Batch Timeout**: 3 seconds (processes incomplete batches)
- **Threshold**: 170px (adaptive for mobile and desktop layouts)

**Critical Layout Discovery**: Articles don't scroll completely out of viewport due to fixed headers. Instead, they stop at around `bottom: 153-159px`. The threshold must be set higher than this "stuck" position to trigger properly.

**Mobile Compatibility**: The system works identically on mobile and desktop using the same 170px threshold, as both platforms have similar header heights in this application.

**Technical Architecture**:
```javascript
// Simple intersection observer with adaptive threshold
if (rect.bottom < threshold) {  // 170px threshold
  this.scheduleMarkAsRead(article.id);  // 800ms delay
  this.untrackArticle(element);
}

// Frontend filtering preserves infinite scroll
let articles = $derived.by(() => {
  if (currentFilter === 'unread') {
    return allArticles.filter(article => !article.read_status?.is_read);
  }
  return allArticles;
});
```

**User Experience Result**: Articles are marked as read smoothly when scrolling past them, counts update immediately, articles disappear from unread view, and infinite scroll continues working perfectly. No user configuration required.