# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2025-08-25-article-export-plugins/spec.md

> Created: 2025-08-25
> Version: 1.0.0

## Test Coverage

### Unit Tests

**ExportPlugin Base Class**
- Test abstract method enforcement
- Test plugin interface contract
- Test config validation method signature

**EmailPlugin**
- Test mailto URL generation with proper encoding
- Test handling of articles with special characters
- Test excerpt truncation for long articles
- Test empty/missing article fields handling

**InstapaperPlugin**
- Test API request formation
- Test OAuth signature generation
- Test successful export response handling
- Test API error handling (401, 403, 500)
- Test network timeout handling
- Test config validation for missing keys

**PluginRegistry**
- Test plugin discovery from directory
- Test plugin loading and instantiation
- Test handling of invalid plugin files
- Test plugin registration and retrieval
- Test duplicate plugin ID handling

**ExportPluginConfig Model**
- Test model creation and save
- Test JSON config serialization/deserialization
- Test unique constraint on user_id + plugin_id
- Test cascade deletion with user
- Test updated_at timestamp updates

### Integration Tests

**Plugin Loading System**
- Test startup plugin discovery and loading
- Test plugin directory creation if missing
- Test handling of malformed plugin files
- Test plugin registry availability to API

**Export API Endpoints**
- Test GET /api/export/plugins returns all plugins
- Test GET /api/export/plugins/{id} returns specific plugin
- Test PUT /api/export/plugins/{id}/config updates configuration
- Test POST /api/articles/{id}/export/{plugin_id} triggers export
- Test POST /api/articles/{id}/export/email returns mailto URL

**Configuration Management**
- Test saving plugin configuration to database
- Test retrieving user-specific plugin configs
- Test enabling/disabling plugins
- Test config validation against schema
- Test handling invalid configuration data

**Export Workflow**
- Test end-to-end email export flow
- Test end-to-end Instapaper export flow
- Test export with disabled plugin (should fail)
- Test export with missing configuration (should fail)
- Test concurrent exports

### Feature Tests

**Settings Page Export Section**
- Test rendering of available plugins
- Test enable/disable toggle functionality
- Test configuration form rendering based on schema
- Test configuration save with validation
- Test error display for invalid configuration

**Article List Export Buttons**
- Test export button visibility for enabled plugins only
- Test export button placement after timestamp
- Test loading state during export
- Test success notification on successful export
- Test error notification on failed export

**Article Card Export Buttons**
- Test export button visibility in action bar
- Test button ordering with existing actions
- Test responsive behavior on mobile
- Test keyboard accessibility

### Mocking Requirements

**Instapaper API**
- Mock successful POST response (200)
- Mock authentication failure (401)
- Mock rate limit response (403)
- Mock server error (500)
- Mock network timeout

**Email Client**
- Mock window.location.href assignment for mailto
- Verify correct URL encoding in mailto link

**File System**
- Mock plugin directory reading
- Mock plugin file imports

## Test Data

### Sample Articles
```python
test_articles = [
    {
        "id": 1,
        "title": "Test Article",
        "excerpt": "This is a test article excerpt.",
        "link": "https://example.com/article1",
        "author": "Test Author"
    },
    {
        "id": 2,
        "title": "Article with Special Characters: & < > \" '",
        "excerpt": "Excerpt with special chars: & < > \" '",
        "link": "https://example.com/article2?param=value&other=123"
    },
    {
        "id": 3,
        "title": "Long Article " + "x" * 200,
        "excerpt": "Very long excerpt " + "content " * 100,
        "link": "https://example.com/article3"
    }
]
```

### Sample Plugin Configurations
```python
test_configs = {
    "email": {
        "enabled": True,
        "config": {}
    },
    "instapaper": {
        "enabled": True,
        "config": {
            "consumer_key": "test_key",
            "consumer_secret": "test_secret"
        }
    },
    "invalid": {
        "enabled": True,
        "config": {
            "consumer_key": "missing_secret"
        }
    }
}
```

## Performance Tests

**Plugin Loading Performance**
- Test startup time with 0, 5, 10, 20 plugins
- Ensure plugin loading doesn't block server startup
- Test memory usage with multiple plugins loaded

**Export Operation Performance**
- Test export response time (should be < 1s for email)
- Test concurrent export handling (10+ simultaneous exports)
- Test export timeout handling (5s timeout)

## Security Tests

**Configuration Security**
- Test that API keys are not exposed in GET responses
- Test that configs are user-isolated
- Test SQL injection attempts in plugin_id parameter
- Test XSS prevention in mailto URL generation

**Plugin Isolation**
- Test that plugin errors don't crash the server
- Test that plugins can't access other plugins' configs
- Test that plugins can't modify core application state

## Accessibility Tests

**Export Controls**
- Test keyboard navigation to export buttons
- Test screen reader announcements for export actions
- Test focus management after export completion
- Test color contrast for export buttons

## Error Scenarios

**Plugin Loading Errors**
- Plugin file with syntax errors
- Plugin missing required methods
- Plugin with duplicate ID
- Plugin directory permissions issue

**Configuration Errors**
- Invalid JSON in config field
- Config doesn't match schema
- Required fields missing
- Invalid data types

**Export Errors**
- Network timeout
- API authentication failure
- Article not found
- Plugin not enabled
- Invalid article data

**Frontend Errors**
- Export button click with network offline
- Export during page navigation
- Export with stale article data
- Multiple rapid export clicks