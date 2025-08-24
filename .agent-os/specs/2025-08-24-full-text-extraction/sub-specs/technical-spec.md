# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-24-full-text-extraction/spec.md

> Created: 2025-08-24
> Version: 1.0.0

## Technical Requirements

- **Newspaper4k Integration** - Use newspaper4k library for HTML parsing and text extraction with proper error handling
- **Asynchronous Processing** - Extract full text in background jobs to avoid blocking RSS feed updates
- **Database Storage** - Store extracted content with metadata including extraction timestamp, success status, and failure reasons
- **Retry Logic** - Implement exponential backoff for failed extractions with maximum retry limits
- **Content Validation** - Verify extracted text quality and length before storage
- **Rate Limiting** - Respect website rate limits and implement delays between extractions
- **User Agent Management** - Use appropriate User-Agent headers to avoid blocking
- **Timeout Handling** - Set reasonable timeouts for extraction requests (30 seconds)

## Approach Options

**Option A: Immediate Extraction During RSS Processing**
- Pros: Articles have full text immediately when added
- Cons: Slows down RSS feed updates, can cause timeouts, blocking operation

**Option B: Background Job Queue with Separate Worker** (Selected)
- Pros: Non-blocking RSS updates, can retry failures, scalable
- Cons: Slight complexity increase, requires job queue management

**Option C: On-Demand Extraction When User Requests**
- Pros: Only extracts when needed, saves resources
- Cons: User must wait for extraction, poor user experience

**Rationale:** Option B provides the best balance of performance and user experience. RSS feeds can update quickly while full-text extraction happens in the background. Failed extractions can be retried without affecting core functionality.

## External Dependencies

- **newspaper4k** - Modern Python library for article extraction and parsing
- **Justification:** Actively maintained fork of newspaper3k with Python 3.12 support, better handling of modern websites, and improved text extraction quality compared to alternatives like BeautifulSoup or custom scrapers

## Implementation Architecture

### Database Schema
- Add `full_text_content` field to Article model for extracted text
- Add `extraction_status` field with values: pending, success, failed, skipped
- Add `extraction_attempted_at` timestamp for retry logic
- Add `extraction_error` field for storing failure reasons

### Background Processing
- Use asyncio background tasks for non-blocking extraction
- Process articles in batches during low-activity periods
- Implement queue system for failed extractions requiring retry

### Extraction Pipeline
1. **URL Validation** - Check if URL is extractable (not PDF, image, etc.)
2. **Website Fetching** - Use newspaper4k to download article HTML
3. **Text Extraction** - Parse and extract clean article text
4. **Quality Validation** - Ensure extracted text meets minimum quality standards
5. **Storage** - Save extracted content to database with metadata

### Rate Limiting Strategy
- 2-second delay between extractions from the same domain
- Maximum 10 concurrent extractions
- Respect robots.txt when possible
- Use rotating User-Agent strings to appear as regular browser traffic