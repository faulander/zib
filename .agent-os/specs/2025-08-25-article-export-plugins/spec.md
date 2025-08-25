# Spec Requirements Document

> Spec: Article Export Plugins
> Created: 2025-08-25
> Status: Planning

## Overview

Implement a plugin-based article export system that allows users to save articles to external services, starting with email and Instapaper integration. The system will use a modular plugin architecture to enable easy addition of new export destinations.

## User Stories

### Export to Read-Later Services

As a power RSS user, I want to export interesting articles to my preferred read-later service, so that I can save articles for deeper reading outside of my RSS workflow.

When browsing articles in the RSS reader, I see export buttons for my configured services next to each article. Clicking an export button immediately sends the article to that service with visual feedback. The export includes the article excerpt and a link to the original source, allowing me to continue reading in my preferred environment.

### Email Article Sharing

As an information professional, I want to email articles to colleagues or myself, so that I can share interesting content or create a personal archive.

When I find an article worth sharing, I click the email export button which opens my default email client with a pre-filled message containing the article title, excerpt, and link. I can then add recipients and any personal notes before sending.

### Configure Export Services

As a tech-savvy user, I want to enable and configure only the export services I use, so that my interface remains clean and relevant to my workflow.

In the settings page, I navigate to the Export section where I can enable/disable available export plugins and configure any required settings like API keys. Only enabled export options appear in the article interface, keeping the UI uncluttered.

## Spec Scope

1. **Plugin Architecture System** - Modular backend system for loading and managing export plugins from a dedicated directory
2. **Email Export Plugin** - Simple mailto-based export with article excerpt and link
3. **Instapaper Export Plugin** - Integration with official Instapaper API for saving articles
4. **Export Settings Management** - UI for enabling/disabling and configuring export plugins
5. **Frontend Export Controls** - Export buttons in article list and card views, showing only enabled services

## Out of Scope

- Export to PDF or other file formats (future enhancement)
- Bulk export of multiple articles
- Export history or tracking
- Custom email SMTP configuration
- Other read-later services (Pocket, Readwise, etc.) - will be added as separate plugins later

## Expected Deliverable

1. Working export functionality for email and Instapaper from both list and card article views
2. Plugin system that allows dropping new export plugins into a directory and having them automatically available
3. Settings page with Export section showing all available plugins with enable/disable toggles and configuration options

## Spec Documentation

- Tasks: @.agent-os/specs/2025-08-25-article-export-plugins/tasks.md
- Technical Specification: @.agent-os/specs/2025-08-25-article-export-plugins/sub-specs/technical-spec.md
- API Specification: @.agent-os/specs/2025-08-25-article-export-plugins/sub-specs/api-spec.md
- Database Schema: @.agent-os/specs/2025-08-25-article-export-plugins/sub-specs/database-schema.md
- Tests Specification: @.agent-os/specs/2025-08-25-article-export-plugins/sub-specs/tests.md