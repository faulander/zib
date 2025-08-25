# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-25-article-export-plugins/spec.md

> Created: 2025-08-25
> Version: 1.0.0

## Endpoints

### GET /api/export/plugins

**Purpose:** Retrieve list of available export plugins with their configuration schemas
**Parameters:** None
**Response:** 
```json
{
  "plugins": [
    {
      "id": "email",
      "name": "Email",
      "icon": "Mail",
      "enabled": false,
      "config_schema": {},
      "config": {}
    },
    {
      "id": "instapaper",
      "name": "Instapaper",
      "icon": "Bookmark",
      "enabled": false,
      "config_schema": {
        "type": "object",
        "properties": {
          "consumer_key": {
            "type": "string",
            "title": "Consumer Key",
            "description": "Instapaper API consumer key"
          },
          "consumer_secret": {
            "type": "string",
            "title": "Consumer Secret",
            "description": "Instapaper API consumer secret",
            "format": "password"
          }
        },
        "required": ["consumer_key", "consumer_secret"]
      },
      "config": {}
    }
  ]
}
```
**Errors:** 
- 500: Server error loading plugins

### GET /api/export/plugins/{plugin_id}

**Purpose:** Get details of a specific export plugin
**Parameters:** 
- `plugin_id` (path): The plugin identifier
**Response:** 
```json
{
  "id": "instapaper",
  "name": "Instapaper",
  "icon": "Bookmark",
  "enabled": true,
  "config_schema": { ... },
  "config": {
    "consumer_key": "your_key_here"
  }
}
```
**Errors:** 
- 404: Plugin not found
- 500: Server error

### PUT /api/export/plugins/{plugin_id}/config

**Purpose:** Update plugin configuration and enable/disable status
**Parameters:** 
- `plugin_id` (path): The plugin identifier
- Request body:
```json
{
  "enabled": true,
  "config": {
    "consumer_key": "key",
    "consumer_secret": "secret"
  }
}
```
**Response:** 
```json
{
  "success": true,
  "message": "Plugin configuration updated"
}
```
**Errors:** 
- 400: Invalid configuration
- 404: Plugin not found
- 500: Server error

### POST /api/articles/{article_id}/export/{plugin_id}

**Purpose:** Export an article using the specified plugin
**Parameters:** 
- `article_id` (path): The article ID to export
- `plugin_id` (path): The plugin to use for export
**Response:** 
```json
{
  "success": true,
  "message": "Article exported successfully",
  "result": {
    "plugin_id": "instapaper",
    "article_id": 123,
    "export_url": "https://www.instapaper.com/read/123456789"
  }
}
```
**Errors:** 
- 400: Plugin not enabled or not configured
- 404: Article or plugin not found
- 500: Export failed

### POST /api/articles/{article_id}/export/email

**Purpose:** Special endpoint for email export that returns mailto URL
**Parameters:** 
- `article_id` (path): The article ID to export
**Response:** 
```json
{
  "success": true,
  "mailto_url": "mailto:?subject=Article%20Title&body=Article%20excerpt...%0A%0ARead%20more%3A%20https%3A%2F%2Fexample.com%2Farticle"
}
```
**Errors:** 
- 404: Article not found
- 500: Server error

## Controllers

### ExportController

**Actions:**
- `list_plugins()` - Enumerate available plugins with configurations
- `get_plugin()` - Retrieve specific plugin details
- `update_plugin_config()` - Save plugin configuration and status
- `export_article()` - Execute export operation for an article

**Business Logic:**
- Load plugins from registry on first request
- Validate configuration against plugin schema
- Check plugin enabled status before export
- Handle export errors gracefully with specific messages

**Error Handling:**
- Plugin not found: Return 404 with helpful message
- Configuration validation: Return 400 with validation errors
- Export failures: Return 500 with plugin-specific error message
- Network timeouts: Return 504 with timeout message

## Request/Response Models

### PluginConfigUpdate (Request)
```python
class PluginConfigUpdate(BaseModel):
    enabled: bool
    config: dict = {}
```

### PluginInfo (Response)
```python
class PluginInfo(BaseModel):
    id: str
    name: str
    icon: str
    enabled: bool
    config_schema: dict
    config: dict
```

### ExportResult (Response)
```python
class ExportResult(BaseModel):
    success: bool
    message: str
    result: Optional[dict] = None
    error: Optional[str] = None
```

## Integration with Frontend

### Frontend API Client Methods

```javascript
// Get all export plugins
async function getExportPlugins() {
  return await api.get('/api/export/plugins');
}

// Update plugin configuration
async function updatePluginConfig(pluginId, enabled, config) {
  return await api.put(`/api/export/plugins/${pluginId}/config`, {
    enabled,
    config
  });
}

// Export article
async function exportArticle(articleId, pluginId) {
  if (pluginId === 'email') {
    // Special handling for email - get mailto URL
    const response = await api.post(`/api/articles/${articleId}/export/email`);
    window.location.href = response.mailto_url;
  } else {
    return await api.post(`/api/articles/${articleId}/export/${pluginId}`);
  }
}
```