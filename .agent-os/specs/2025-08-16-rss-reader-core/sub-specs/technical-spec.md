# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-16-rss-reader-core/spec.md

> Created: 2025-08-16
> Version: 1.0.0

## Technical Requirements

- **Article Model**: Complete Peewee model with fields for URL, title, content, summary, published date, read status, and feed relationship
- **Feed Parser Service**: Service using existing feedparser library to fetch and parse RSS/Atom feeds
- **Background Task System**: Python-based scheduling system for automatic feed updates (using APScheduler or similar)
- **Article API Endpoints**: RESTful endpoints for article CRUD operations with filtering and pagination
- **Database Performance**: Proper indexing for efficient article queries by feed, category, read status, and date
- **Error Handling**: Robust error handling for feed fetch failures, parsing errors, and network timeouts
- **Duplicate Detection**: Prevent duplicate articles based on URL or GUID
- **Feed Health Monitoring**: Track failed fetches and provide feed status information

## Approach Options

**Option A:** Simple Cron-style Background Tasks
- Pros: Lightweight, easy to implement, works with existing FastAPI setup
- Cons: No persistence across application restarts, limited scheduling flexibility

**Option B:** APScheduler with SQLite Persistence (Selected)
- Pros: Persistent job scheduling, survives application restarts, flexible scheduling options
- Cons: Additional dependency, slightly more complex setup

**Option C:** External Job Queue (Celery/RQ)
- Pros: Most robust, scalable, separate worker processes
- Cons: Requires Redis/RabbitMQ, over-engineered for single-user application

**Rationale:** Option B provides the right balance of reliability and simplicity for a self-hosted RSS reader. APScheduler with SQLite persistence ensures feed updates continue working after application restarts while maintaining the simplicity appropriate for a single-user system.

## External Dependencies

- **APScheduler** - Advanced Python scheduler for background feed updates
- **Justification:** Provides persistent job scheduling that survives application restarts, essential for reliable feed updates

## Feed Update Strategy

**Update Frequency:**
- Default: Every 60 minutes per feed
- Configurable per feed based on feed characteristics
- Respect HTTP caching headers and conditional requests

**Error Handling:**
- Retry failed feeds with exponential backoff
- Track consecutive failures and adjust update frequency
- Log errors for monitoring and debugging

**Performance Optimization:**
- Batch feed updates to avoid overwhelming target servers
- Use conditional requests (If-Modified-Since, ETags) when supported
- Implement connection pooling for HTTP requests

## Article Storage Strategy

**Content Extraction:**
- Store both summary and full content when available
- Preserve original HTML formatting in content field
- Extract and store publication date, author, and tags

**Duplicate Prevention:**
- Primary key: combination of feed_id and article URL/GUID
- Check for existing articles before insertion
- Handle cases where feeds republish the same content

**Read Status Tracking:**
- Boolean field for read/unread status
- Timestamp for when article was marked as read
- API endpoints for bulk read status updates