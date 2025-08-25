# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-25-article-export-plugins/spec.md

> Created: 2025-08-25
> Status: Ready for Implementation

## Tasks

- [ ] 1. Backend Plugin Infrastructure
  - [ ] 1.1 Write tests for plugin base class and registry
  - [ ] 1.2 Create plugin base class (ExportPlugin) with abstract methods
  - [ ] 1.3 Implement plugin registry for loading and managing plugins
  - [ ] 1.4 Create plugin directory structure under backend/app/plugins/export/
  - [ ] 1.5 Add plugin loading to server startup sequence
  - [ ] 1.6 Verify all tests pass

- [ ] 2. Database and Models
  - [ ] 2.1 Write tests for ExportPluginConfig model
  - [ ] 2.2 Create database migration for export_plugin_configs table
  - [ ] 2.3 Implement ExportPluginConfig Peewee model
  - [ ] 2.4 Run migration and verify database structure
  - [ ] 2.5 Verify all tests pass

- [ ] 3. Email Export Plugin
  - [ ] 3.1 Write tests for email export plugin
  - [ ] 3.2 Implement EmailPlugin class with mailto URL generation
  - [ ] 3.3 Add proper URL encoding for special characters
  - [ ] 3.4 Test with various article formats and edge cases
  - [ ] 3.5 Verify all tests pass

- [ ] 4. Instapaper Export Plugin
  - [ ] 4.1 Write tests for Instapaper API integration
  - [ ] 4.2 Implement InstapaperPlugin class with OAuth 1.0a
  - [ ] 4.3 Add configuration schema for API credentials
  - [ ] 4.4 Implement error handling for API failures
  - [ ] 4.5 Test with mock Instapaper API responses
  - [ ] 4.6 Verify all tests pass

- [ ] 5. Export API Endpoints
  - [ ] 5.1 Write tests for export API endpoints
  - [ ] 5.2 Implement GET /api/export/plugins endpoint
  - [ ] 5.3 Implement PUT /api/export/plugins/{id}/config endpoint
  - [ ] 5.4 Implement POST /api/articles/{id}/export/{plugin_id} endpoint
  - [ ] 5.5 Add special handling for email export endpoint
  - [ ] 5.6 Verify all API tests pass

- [ ] 6. Frontend Settings Integration
  - [ ] 6.1 Write tests for export settings component
  - [ ] 6.2 Add Export section to settings page
  - [ ] 6.3 Create plugin configuration forms with dynamic schema rendering
  - [ ] 6.4 Implement enable/disable toggles for each plugin
  - [ ] 6.5 Add configuration save with validation feedback
  - [ ] 6.6 Verify all frontend tests pass

- [ ] 7. Frontend Export Controls
  - [ ] 7.1 Write tests for export button components
  - [ ] 7.2 Add export buttons to article list view (after timestamp)
  - [ ] 7.3 Add export buttons to article card view (in action bar)
  - [ ] 7.4 Implement loading states and notifications
  - [ ] 7.5 Handle email export with mailto redirect
  - [ ] 7.6 Test responsive behavior on mobile
  - [ ] 7.7 Verify all UI tests pass

- [ ] 8. Integration Testing and Polish
  - [ ] 8.1 Test complete email export flow end-to-end
  - [ ] 8.2 Test complete Instapaper export flow end-to-end
  - [ ] 8.3 Verify plugin enable/disable properly controls UI visibility
  - [ ] 8.4 Test error scenarios and user feedback
  - [ ] 8.5 Add proper logging for debugging
  - [ ] 8.6 Update documentation if needed
  - [ ] 8.7 Run all tests and ensure 100% pass rate