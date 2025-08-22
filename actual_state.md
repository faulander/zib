# Zib RSS Reader - Refresh System State

**Date**: 2025-08-22  
**Session**: Backend-driven refresh system implementation

## Current System Status

### ✅ Completed Features
1. **Backend-driven refresh system** - Backend is the single source of truth for feed refreshing
2. **Auto-refresh service** - Runs in background, refreshes feeds every 5 minutes (configurable)
3. **Refresh status API** - Provides real-time status via `/api/settings/refresh-status`
4. **Frontend polling service** - Polls backend every 10 seconds for status updates
5. **Live countdown display** - Shows time remaining until next refresh
6. **Sidebar layout improvements** - Settings and refresh status moved to top
7. **Horizontal divider** - Added before "All Articles" button
8. **Content filter improvements** - Today's unread articles bypass harsh filtering
9. **Datetime serialization fixes** - Proper handling of datetime objects in API responses

### 🔧 Current Issue
- **Frontend reactivity problem**: The sidebar UI shows "Auto-refresh ready 5m" even though backend provides correct countdown data
- Console logs show: `UI should show: Next countdown - 55` but template doesn't update
- This is a Svelte 5 reactivity issue with nested object properties

## Key Files Modified

### Backend Files
1. **`/backend/app/services/auto_refresh_service.py`**
   - Main auto-refresh service with status tracking
   - Manages refresh loops per user
   - Tracks `is_refreshing`, `last_refresh_started/completed`, `next_refresh_at`

2. **`/backend/app/routes/settings.py`**
   - Added `/refresh-status` endpoint (lines 96-146)
   - Handles datetime serialization to ISO format
   - Returns refresh status with `seconds_until_refresh` calculation

3. **`/backend/app/services/filter_service.py`**
   - Enhanced `apply_filters()` method (lines 131-203)
   - Today's unread articles bypass content filters
   - Uses timezone-aware date comparison

4. **`/backend/app/main.py`**
   - Auto-refresh service startup in lifespan (lines 62-68)
   - Ensures service starts with application

### Frontend Files
1. **`/frontend/src/lib/services/refreshStatusService.js`**
   - Polls `/api/settings/refresh-status` every 10 seconds
   - Manages refresh status store updates
   - Detects backend refresh completion and triggers frontend data reload
   - Auto-starts 3 seconds after app initialization

2. **`/frontend/src/lib/components/Sidebar.svelte`**
   - **CURRENT ISSUE LOCATION**: Lines 237-248 (refresh status display)
   - Uses individual `$state()` variables for reactivity
   - Should show countdown but template not updating
   - Debug logs confirm correct data received

3. **`/frontend/src/lib/api.js`**
   - Added `getRefreshStatus()` API call
   - Maps to `/api/settings/refresh-status`

## API Endpoints

### `/api/settings/refresh-status` (GET)
Returns refresh status for current user:
```json
{
  "is_refreshing": false,
  "last_refresh_started": "2025-08-22T17:20:28.635996",
  "last_refresh_completed": "2025-08-22T17:22:46.636817", 
  "next_refresh_at": "2025-08-22T17:27:46.636810",
  "interval_minutes": 5,
  "auto_refresh_enabled": true,
  "seconds_until_refresh": 175
}
```

## Current Problem Analysis

### Backend Status: ✅ Working
- Auto-refresh service runs correctly
- API returns proper status data
- Countdown calculated correctly (`seconds_until_refresh`)

### Frontend Service: ✅ Working  
- Polling every 10 seconds
- Store updates with correct data
- Console shows: `"UI should show: Next countdown - 55"`

### Frontend UI: ❌ Broken
- Template shows "Auto-refresh ready 5m" instead of countdown
- Svelte reactivity issue with template not updating
- Individual `$state()` variables created but template still not reactive

## Next Session Tasks

### 1. Fix Frontend Reactivity (HIGH PRIORITY)
**Current approach**: Individual `$state()` variables
**File**: `/frontend/src/lib/components/Sidebar.svelte` lines 237-248

**Options to try**:
- Force template re-render with key binding
- Use `$derived()` instead of manual subscription
- Add explicit reactive statements `$:` 
- Use `tick()` to force updates
- Check if Svelte 5 runes syntax is correct

### 2. Clean Up Debug Logging
**Files to clean**:
- `/frontend/src/lib/services/refreshStatusService.js` - Remove remaining debug logs
- `/frontend/src/lib/components/Sidebar.svelte` - Remove "UI should show:" logs

### 3. Test Complete Flow
- Verify countdown displays correctly
- Test refresh cycle (shows "Refreshing..." → countdown)
- Test frontend data reload on refresh completion
- Verify all edge cases

## Configuration

### Settings
- **Refresh interval**: 5 minutes (configurable in UI)
- **Polling interval**: 10 seconds (hardcoded)
- **Service startup delay**: 3 seconds (prevents app loading issues)

### User Settings Location
- Backend: `User.auto_refresh_feeds`, `User.auto_refresh_interval_minutes`
- Frontend: Settings page at `/settings`

## Dependencies

### Backend
- FastAPI, Peewee ORM, SQLite
- Auto-refresh service uses asyncio
- No external dependencies added

### Frontend  
- SvelteKit with Svelte 5 runes syntax
- Svelte stores for state management
- TailwindCSS for styling

## Known Working Features

1. **Backend refresh scheduling** - Feeds refresh automatically
2. **Status API** - Returns real-time refresh information  
3. **Frontend polling** - Receives backend status updates
4. **Data reload** - Frontend refreshes articles after backend refresh
5. **Scroll tracking** - Temporarily disabled (working but needs proper fix)
6. **Content filtering** - Enhanced to allow today's articles
7. **Settings persistence** - Refresh intervals saved to database

## Issue Context

The reactivity problem appeared when transitioning from a simple status object to a more complex nested object. Svelte 5 runes might not be detecting changes to nested properties properly. The fix was attempted by breaking the object into individual `$state()` variables, but the template still doesn't update.

**Debug evidence**: Console shows correct logic execution but UI remains static, indicating a template reactivity problem, not a data problem.