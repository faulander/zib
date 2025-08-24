# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-24-reading-time-estimates/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Technical Requirements

- **Word counting algorithm** - Extract and count words from article content (both RSS content and full text if available)
- **Reading speed calculation** - Use configurable words-per-minute (WPM) rate with default of 200 WPM
- **Smart time formatting** - Display estimates in readable format (< 1 min, 2 min read, 15 min read)
- **Caching mechanism** - Cache calculated reading times to avoid recalculation on every page load
- **HTML content handling** - Strip HTML tags and count only readable text
- **Settings integration** - Store user's preferred reading speed in user settings

## Approach Options

**Option A: Frontend-Only Calculation**
- Pros: No backend changes, immediate calculation, works with existing data
- Cons: Calculation happens on every render, inconsistent across devices, no caching

**Option B: Backend Calculation with Caching** (Selected)
- Pros: Calculated once per article, cached results, consistent across devices
- Cons: Requires backend changes, database migration

**Option C: Hybrid Calculation**
- Pros: Backend for RSS content, frontend for full text, best of both worlds
- Cons: Complex logic, multiple calculation paths, harder to maintain

**Rationale:** Option B provides the best performance and consistency. Reading time estimates should be calculated once when articles are added and cached for all subsequent requests.

## External Dependencies

- **No new dependencies required** - Use existing text processing capabilities

## Implementation Architecture

### Backend Changes
- Add `reading_time_minutes` field to Article model
- Calculate reading time during article creation/update
- Provide reading time in all article API responses

### Word Counting Algorithm
```python
def calculate_reading_time(content: str, wpm: int = 200) -> int:
    # Strip HTML tags
    clean_text = strip_html_tags(content)
    # Count words (split by whitespace, filter empty strings)
    word_count = len([word for word in clean_text.split() if word.strip()])
    # Calculate minutes, minimum 1 minute
    minutes = max(1, round(word_count / wpm))
    return minutes
```

### Content Priority
1. Use full_text_content if available (from full-text extraction feature)
2. Fall back to RSS content if no full text available
3. Use title + summary if content is very short

### Time Display Formatting
- < 1 minute: "< 1 min"
- 1 minute: "1 min read"  
- 2-59 minutes: "X min read"
- 60+ minutes: "1+ hour read"

### Settings Integration
- Add `reading_speed_wpm` to user settings (default: 200)
- Recalculate all reading times when user changes setting
- Provide preset options: Slow (150), Average (200), Fast (250), Very Fast (300)

### Database Migration
```sql
ALTER TABLE articles ADD COLUMN reading_time_minutes INTEGER DEFAULT 1;

-- Update existing articles with calculated reading times
UPDATE articles SET reading_time_minutes = 
  CASE 
    WHEN length(content) > 0 THEN max(1, round(length(replace(content, ' ', '')) / 4 / 200))
    ELSE 1 
  END;
```