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