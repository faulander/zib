# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-22-opml-import-export-improvements/spec.md

> Created: 2025-08-22
> Version: 1.0.0

## Technical Requirements

### Performance Optimizations

- **Batch Database Operations**: Replace individual CREATE operations with batch inserts using SQLite executemany() 
- **Concurrent Feed Validation**: Implement async semaphore-controlled feed validation with configurable concurrency limit
- **Optimized Duplicate Detection**: Pre-load existing feeds/categories into memory structures for O(1) lookup
- **Database Connection Pooling**: Ensure efficient connection reuse during bulk operations
- **Progress Update Batching**: Update progress every 10-20 items instead of per item to reduce overhead

### Frontend Progress Modal

- **Real-time WebSocket Updates**: Establish WebSocket connection for live progress updates
- **Progress Visualization**: Progress bar with percentage, current phase indicator, and items processed counter
- **Cancel Functionality**: Cancel button that sends abort signal to backend with cleanup
- **Phase Indicators**: Visual representation of current phase (Parsing → Validating → Creating Categories → Importing Feeds)
- **Responsive Design**: Modal works on mobile and desktop with proper touch interactions

### OPML Export System

- **Export Service**: New service class to generate OPML XML from database feeds and categories
- **Category Hierarchy**: Properly nested OPML outline elements respecting category relationships
- **Export Options**: Filter by categories, include/exclude specific feeds, export format options
- **Large Dataset Handling**: Stream generation for large OPML exports without memory issues
- **Proper XML Formatting**: Valid OPML 2.0 format with proper encoding and structure

## Approach Options

**Option A:** WebSocket-based Progress Updates (Selected)
- Pros: Real-time updates, low latency, better user experience, standard for progress tracking
- Cons: Additional infrastructure complexity, connection management required

**Option B:** Polling-based Progress Updates
- Pros: Simpler implementation, works with existing REST API
- Cons: Higher latency, more server requests, less smooth user experience

**Rationale:** WebSocket approach provides the best user experience for real-time progress tracking and is standard for long-running operations in modern web applications.

## External Dependencies

**No new external dependencies required** - All functionality can be implemented using existing Python and JavaScript libraries:
- Python: Built-in `xml.etree.ElementTree` for OPML generation
- FastAPI: Built-in WebSocket support
- SQLite: Built-in executemany() for batch operations
- SvelteKit: Built-in WebSocket support in browser

**Justification:** Avoiding new dependencies keeps the application lightweight and reduces potential security/maintenance overhead while still achieving all technical requirements.

## Implementation Details

### Backend Performance Improvements

1. **Batch Feed Creation**: 
   ```python
   # Replace individual Feed.create() calls with:
   feed_data = [(title, url, site_url, description, category_id) for feed in feeds]
   cursor.executemany("INSERT INTO feed (...) VALUES (?, ?, ?, ?, ?)", feed_data)
   ```

2. **Concurrent Feed Validation**:
   ```python
   semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
   tasks = [validate_with_semaphore(semaphore, url) for url in urls]
   results = await asyncio.gather(*tasks, return_exceptions=True)
   ```

3. **Optimized Duplicate Detection**:
   ```python
   # Pre-load into sets for O(1) lookup
   existing_urls = {feed.url for feed in Feed.select(Feed.url)}
   existing_categories = {cat.name for cat in Category.select(Category.name)}
   ```

### Frontend Progress Modal Implementation

1. **WebSocket Connection**:
   ```javascript
   const ws = new WebSocket(`ws://localhost:8000/ws/import/${jobId}`);
   ws.onmessage = (event) => {
     const progress = JSON.parse(event.data);
     updateProgressUI(progress);
   };
   ```

2. **Progress UI Components**:
   - Progress bar with percentage
   - Phase indicator (text + icons)
   - Current item counter (e.g., "Processing feed 45 of 200")
   - Cancel button with confirmation

3. **Cancel Functionality**:
   ```javascript
   async function cancelImport() {
     await fetch(`/api/import/jobs/${jobId}`, { method: 'DELETE' });
     ws.close();
     closeModal();
   }
   ```

### OPML Export Service

1. **Export Service Class**:
   ```python
   class OPMLExporter:
       def export_feeds(self, filters: ExportFilters) -> str:
           # Generate OPML XML with proper hierarchy
           # Support category filtering and feed selection
   ```

2. **XML Generation**:
   ```python
   root = ET.Element("opml", version="2.0")
   head = ET.SubElement(root, "head")
   body = ET.SubElement(root, "body")
   # Add nested outline elements for categories and feeds
   ```

3. **Streaming for Large Exports**:
   ```python
   def stream_opml_export():
       yield '<?xml version="1.0" encoding="UTF-8"?>'
       yield '<opml version="2.0"><head>...</head><body>'
       for category in categories:
           yield generate_category_xml(category)
       yield '</body></opml>'
   ```

## Database Optimizations

- **Indexes**: Ensure proper indexes on feed.url and category.name for duplicate detection
- **Transaction Management**: Use database transactions for batch operations to ensure consistency
- **Connection Management**: Reuse connections during import process to avoid connection overhead

## Error Handling Enhancements

- **Granular Error Reporting**: Track and report errors per feed/category with specific reasons
- **Recovery Mechanisms**: Continue import process despite individual feed failures
- **User-Friendly Messages**: Convert technical errors into actionable user guidance
- **Import Summary**: Detailed report showing successes, failures, and suggestions for manual fixes