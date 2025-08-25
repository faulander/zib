# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-25-article-export-plugins/spec.md

> Created: 2025-08-25
> Version: 1.0.0

## Technical Requirements

### Plugin System Architecture

- **Plugin Directory**: `/backend/app/plugins/export/` - Directory scanned on server startup
- **Plugin Interface**: Abstract base class `ExportPlugin` defining required methods
- **Dynamic Loading**: Use Python's importlib to dynamically load plugin modules
- **Plugin Registration**: Automatic registration of plugins found in the directory
- **Configuration Storage**: Plugin configurations stored in user settings as JSON

### Plugin Interface Design

```python
class ExportPlugin(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the plugin"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Display name for the plugin"""
        pass
    
    @property
    @abstractmethod
    def icon(self) -> str:
        """Lucide icon name for the plugin"""
        pass
    
    @property
    @abstractmethod
    def config_schema(self) -> dict:
        """JSON schema for plugin configuration"""
        pass
    
    @abstractmethod
    async def export(self, article: Article, config: dict) -> ExportResult:
        """Execute the export operation"""
        pass
    
    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        """Validate plugin configuration"""
        pass
```

### Email Plugin Implementation

- **Method**: Generate mailto: URL with article data
- **No server-side email sending**: Relies on client's default email application
- **URL encoding**: Proper encoding of subject and body for mailto: links
- **Content format**: Article title as subject, excerpt and link in body

### Instapaper Plugin Implementation

- **API Integration**: Use official Instapaper Simple API
- **Authentication**: OAuth 1.0a with user-provided consumer key and secret
- **Endpoint**: POST to `https://www.instapaper.com/api/add`
- **Error handling**: Graceful handling of API failures with user feedback

### Frontend Integration

- **Export buttons location**:
  - List view: Icon buttons after the timestamp
  - Card view: In the article action bar with star/read buttons
- **Dynamic button rendering**: Only show buttons for enabled plugins
- **Loading states**: Visual feedback during export operations
- **Success/error notifications**: Toast notifications for export results

## Approach Options

**Option A: Microservice Architecture**
- Pros: Complete isolation, could scale independently
- Cons: Over-engineering for this use case, complex deployment

**Option B: Integrated Plugin System** (Selected)
- Pros: Simple deployment, direct database access, easier configuration management
- Cons: Plugins run in same process as main application

**Rationale:** The integrated approach is more appropriate for a self-hosted single-user application. It simplifies deployment and maintenance while providing sufficient modularity for adding new export destinations.

## External Dependencies

- **httpx** - Already in use for async HTTP requests (Instapaper API calls)
- **Justification:** Existing dependency, no new packages needed for core functionality

## Plugin Discovery and Loading

### Startup Sequence

1. Create plugin directory if it doesn't exist
2. Scan directory for Python files containing ExportPlugin subclasses
3. Dynamically import and instantiate plugins
4. Register plugins in a global registry
5. Make registry available to API endpoints

### Plugin File Structure

```
backend/app/plugins/
└── export/
    ├── __init__.py
    ├── base.py          # ExportPlugin base class
    ├── email.py         # Email export plugin
    ├── instapaper.py    # Instapaper export plugin
    └── registry.py      # Plugin registry management
```

## Security Considerations

- **Configuration validation**: All plugin configs validated before storage
- **API key storage**: Encrypted storage for sensitive configuration like API keys
- **Rate limiting**: Implement rate limiting for export operations
- **Input sanitization**: Sanitize article content before including in mailto: URLs

## Performance Considerations

- **Lazy loading**: Plugins loaded only when needed, not all at startup
- **Async operations**: All export operations are async to prevent blocking
- **Caching**: Cache plugin registry to avoid repeated filesystem scans
- **Timeout handling**: Implement timeouts for external API calls (5 seconds default)

## Error Handling Strategy

- **Plugin load failures**: Log error, continue loading other plugins
- **Export failures**: Return specific error messages to frontend
- **Configuration errors**: Validate on save, prevent invalid configs
- **Network failures**: Retry logic with exponential backoff for API calls