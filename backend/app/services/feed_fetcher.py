import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import aiohttp
import feedparser
from loguru import logger
from app.models.base import Feed
from app.models.article import Article


class FeedFetchError(Exception):
    '''Base exception for feed fetching errors'''
    pass


class FeedParseError(Exception):
    '''Exception for feed parsing errors'''
    pass


@dataclass
class FeedFetchResult:
    '''Result of a feed fetch operation'''
    success: bool
    feed_url: str
    final_url: Optional[str] = None
    content: Optional[str] = None
    last_modified: Optional[str] = None
    etag: Optional[str] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    fetch_time: float = 0.0


@dataclass
class FeedUpdateResult:
    '''Result of a feed update operation'''
    success: bool
    feed: Feed
    articles_added: int = 0
    articles_updated: int = 0
    articles_failed: int = 0
    fetch_result: Optional[FeedFetchResult] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0


class FeedFetcher:
    '''Service for fetching and parsing RSS/Atom feeds'''
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: str = 'Zib RSS Reader/1.0 (https://github.com/yourusername/zib)'
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        
        # Configure aiohttp session
        self.session_timeout = aiohttp.ClientTimeout(total=timeout)
        self.session_headers = {
            'User-Agent': user_agent,
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
            'Accept-Encoding': 'gzip, deflate',
        }
    
    async def fetch_feed(
        self,
        feed_url: str,
        last_modified: Optional[str] = None,
        etag: Optional[str] = None
    ) -> FeedFetchResult:
        '''
        Fetch feed content from URL with conditional requests support
        
        Args:
            feed_url: URL of the feed to fetch
            last_modified: Last-Modified header value for conditional requests
            etag: ETag header value for conditional requests
            
        Returns:
            FeedFetchResult with fetch details and content
        '''
        start_time = time.time()
        
        # Prepare headers for conditional requests
        headers = self.session_headers.copy()
        if last_modified:
            headers['If-Modified-Since'] = last_modified
        if etag:
            headers['If-None-Match'] = etag
        
        async with aiohttp.ClientSession(
            timeout=self.session_timeout,
            headers=headers
        ) as session:
            
            for attempt in range(self.max_retries):
                try:
                    logger.debug(f'Fetching feed: {feed_url} (attempt {attempt + 1})')
                    
                    async with session.get(feed_url) as response:
                        fetch_time = time.time() - start_time
                        
                        # Handle different status codes
                        if response.status == 304:
                            # Not modified - no new content
                            logger.debug(f'Feed not modified: {feed_url}')
                            return FeedFetchResult(
                                success=True,
                                feed_url=feed_url,
                                final_url=str(response.url),
                                status_code=304,
                                fetch_time=fetch_time
                            )
                        
                        elif response.status == 200:
                            # Success - get content
                            content = await response.text()
                            
                            return FeedFetchResult(
                                success=True,
                                feed_url=feed_url,
                                final_url=str(response.url),
                                content=content,
                                last_modified=response.headers.get('Last-Modified'),
                                etag=response.headers.get('ETag'),
                                status_code=200,
                                fetch_time=fetch_time
                            )
                        
                        else:
                            # HTTP error
                            error_msg = f'HTTP {response.status}: {response.reason}'
                            logger.warning(f'Feed fetch failed: {feed_url} - {error_msg}')
                            
                            return FeedFetchResult(
                                success=False,
                                feed_url=feed_url,
                                final_url=str(response.url),
                                status_code=response.status,
                                error_message=error_msg,
                                fetch_time=fetch_time
                            )
                
                except asyncio.TimeoutError:
                    error_msg = f'Request timeout after {self.timeout} seconds'
                    logger.warning(f'Feed fetch timeout: {feed_url}')
                    
                    if attempt == self.max_retries - 1:
                        return FeedFetchResult(
                            success=False,
                            feed_url=feed_url,
                            error_message=error_msg,
                            fetch_time=time.time() - start_time
                        )
                    
                    # Wait before retry
                    await asyncio.sleep(2 ** attempt)
                
                except aiohttp.ClientError as e:
                    error_msg = f'Connection error: {str(e)}'
                    logger.warning(f'Feed fetch connection error: {feed_url} - {error_msg}')
                    
                    if attempt == self.max_retries - 1:
                        return FeedFetchResult(
                            success=False,
                            feed_url=feed_url,
                            error_message=error_msg,
                            fetch_time=time.time() - start_time
                        )
                    
                    # Wait before retry
                    await asyncio.sleep(2 ** attempt)
                
                except Exception as e:
                    error_msg = f'Unexpected error: {str(e)}'
                    logger.error(f'Feed fetch unexpected error: {feed_url} - {error_msg}')
                    
                    return FeedFetchResult(
                        success=False,
                        feed_url=feed_url,
                        error_message=error_msg,
                        fetch_time=time.time() - start_time
                    )
        
        # Should not reach here
        return FeedFetchResult(
            success=False,
            feed_url=feed_url,
            error_message='Max retries exceeded',
            fetch_time=time.time() - start_time
        )
    
    async def parse_feed_content(self, content: str) -> feedparser.FeedParserDict:
        '''
        Parse feed content using feedparser
        
        Args:
            content: Raw feed content (RSS/Atom XML)
            
        Returns:
            Parsed feed data
            
        Raises:
            FeedParseError: If content cannot be parsed
        '''
        if not content or not content.strip():
            raise FeedParseError('Empty feed content')
        
        try:
            # Parse with feedparser
            parsed = feedparser.parse(content)
            
            # Check if parsing was successful
            if parsed.bozo and not parsed.entries:
                # Parsing failed and no entries found
                error_msg = f'Feed parsing failed: {parsed.bozo_exception}'
                raise FeedParseError(error_msg)
            
            # Check if we have a valid feed
            if not hasattr(parsed, 'feed') or not parsed.feed:
                raise FeedParseError('No valid feed data found')
            
            logger.debug(f'Parsed feed: {len(parsed.entries)} entries found')
            return parsed
            
        except Exception as e:
            if isinstance(e, FeedParseError):
                raise
            
            error_msg = f'Feed parsing error: {str(e)}'
            logger.error(error_msg)
            raise FeedParseError(error_msg)
    
    def should_update_feed(self, feed: Feed, force: bool = False) -> bool:
        '''
        Check if a feed should be updated based on its fetch interval
        
        Args:
            feed: Feed to check
            force: Force update regardless of interval
            
        Returns:
            True if feed should be updated
        '''
        if force:
            return True
        
        if not feed.last_fetched:
            # Never fetched before
            return True
        
        # Check if enough time has passed
        time_since_last_fetch = datetime.now() - feed.last_fetched
        fetch_interval = timedelta(seconds=feed.fetch_interval)
        
        return time_since_last_fetch >= fetch_interval
    
    def update_feed_last_fetched(self, feed: Feed):
        '''Update feed's last_fetched timestamp'''
        feed.last_fetched = datetime.now()
        feed.save()
        logger.debug(f'Updated last_fetched for feed: {feed.url}')
    
    async def extract_articles_from_parsed_feed(
        self,
        feed: Feed,
        parsed_feed: feedparser.FeedParserDict
    ) -> List[Dict[str, Any]]:
        '''
        Extract article data from parsed feed entries
        
        Args:
            feed: Feed model instance
            parsed_feed: Parsed feed data from feedparser
            
        Returns:
            List of article data dictionaries
        '''
        articles = []
        
        for entry in parsed_feed.entries:
            try:
                # Extract basic article data
                article_data = {
                    'title': getattr(entry, 'title', None),
                    'link': getattr(entry, 'link', None),
                    'summary': getattr(entry, 'summary', None),
                    'id': getattr(entry, 'id', None) or getattr(entry, 'guid', None),
                    'author': self._extract_author(entry),
                    'published_parsed': getattr(entry, 'published_parsed', None),
                    'tags': self._extract_tags(entry),
                    # Include media fields for image extraction
                    'media_content': getattr(entry, 'media_content', None),
                    'media_thumbnail': getattr(entry, 'media_thumbnail', None),
                    'enclosures': getattr(entry, 'enclosures', None),
                    'links': getattr(entry, 'links', None),
                }
                
                # Extract content (prefer content over description)
                content = self._extract_content(entry)
                if content:
                    article_data['content'] = content
                elif hasattr(entry, 'description'):
                    article_data['content'] = entry.description
                
                # Only add if we have minimum required fields
                if article_data['link'] and (article_data['title'] or article_data['content']):
                    articles.append(article_data)
                else:
                    logger.warning(f'Skipping entry with missing required fields: {article_data}')
            
            except Exception as e:
                logger.warning(f'Error extracting article from entry: {str(e)}')
                continue
        
        logger.debug(f'Extracted {len(articles)} articles from feed: {feed.url}')
        return articles
    
    def _extract_author(self, entry) -> Optional[str]:
        '''Extract author from feed entry'''
        if hasattr(entry, 'author'):
            return entry.author
        
        if hasattr(entry, 'author_detail') and entry.author_detail:
            if hasattr(entry.author_detail, 'name'):
                return entry.author_detail.name
            if hasattr(entry.author_detail, 'email'):
                return entry.author_detail.email
        
        return None
    
    def _extract_tags(self, entry) -> List[str]:
        '''Extract tags/categories from feed entry'''
        tags = []
        
        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                if hasattr(tag, 'term') and tag.term:
                    tags.append(tag.term)
                elif isinstance(tag, str):
                    tags.append(tag)
        
        return tags
    
    def _extract_content(self, entry) -> Optional[str]:
        '''Extract content from feed entry'''
        # Try content field first (Atom)
        if hasattr(entry, 'content') and entry.content:
            for content in entry.content:
                if hasattr(content, 'value'):
                    return content.value
        
        # Try description field (RSS)
        if hasattr(entry, 'description'):
            return entry.description
        
        # Try summary field
        if hasattr(entry, 'summary'):
            return entry.summary
        
        return None
    
    async def update_feed(self, feed: Feed, force: bool = False) -> FeedUpdateResult:
        '''
        Update a feed by fetching and parsing its content
        
        Args:
            feed: Feed to update
            force: Force update regardless of interval
            
        Returns:
            FeedUpdateResult with update details
        '''
        start_time = time.time()
        
        try:
            # Check if update is needed
            if not self.should_update_feed(feed, force):
                logger.debug(f'Feed update skipped (interval not elapsed): {feed.url}')
                return FeedUpdateResult(
                    success=True,
                    feed=feed,
                    processing_time=time.time() - start_time
                )
            
            logger.info(f'Updating feed: {feed.url}')
            
            # Fetch feed content
            fetch_result = await self.fetch_feed(feed.url)
            
            if not fetch_result.success:
                self.update_feed_last_fetched(feed)  # Update timestamp even on failure
                return FeedUpdateResult(
                    success=False,
                    feed=feed,
                    fetch_result=fetch_result,
                    error_message=fetch_result.error_message,
                    processing_time=time.time() - start_time
                )
            
            # Handle 304 Not Modified
            if fetch_result.status_code == 304:
                self.update_feed_last_fetched(feed)
                logger.debug(f'Feed not modified: {feed.url}')
                return FeedUpdateResult(
                    success=True,
                    feed=feed,
                    fetch_result=fetch_result,
                    processing_time=time.time() - start_time
                )
            
            # Parse feed content
            parsed_feed = await self.parse_feed_content(fetch_result.content)
            
            # Extract articles
            article_data_list = await self.extract_articles_from_parsed_feed(feed, parsed_feed)
            
            # Process and store articles
            articles_added = 0
            articles_updated = 0
            articles_failed = 0
            articles_skipped_old = 0
            
            # Get the timestamp of the last refresh for filtering
            last_refresh_time = feed.last_fetched
            
            for article_data in article_data_list:
                try:
                    # Check for duplicates
                    existing_article = Article.find_duplicate(
                        feed=feed,
                        url=article_data['link'],
                        guid=article_data['id'] or article_data['link']
                    )
                    
                    if existing_article:
                        # Article already exists - could update if needed
                        articles_updated += 1
                        logger.debug(f'Article already exists: {article_data["link"]}')
                    else:
                        # Parse published date to check if article is newer than last refresh
                        article_published_date = None
                        if article_data.get('published_parsed'):
                            try:
                                import calendar
                                from datetime import timezone
                                # Convert time struct to UTC timestamp using calendar.timegm (treats as UTC)
                                utc_timestamp = calendar.timegm(article_data['published_parsed'])
                                # Parse as UTC datetime, then convert to naive (to match database storage)
                                article_published_date = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc).replace(tzinfo=None)
                            except (ValueError, TypeError, OverflowError):
                                pass
                        
                        # Skip articles that are older than the last refresh time
                        # BUT always allow articles from today (even if published before last refresh)
                        # Only apply this filter if we have both timestamps and this is not the first fetch
                        if last_refresh_time and article_published_date:
                            # Get today's date at midnight (UTC)
                            from datetime import timezone
                            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
                            
                            # Skip only if article is both:
                            # 1. Older than last refresh time AND
                            # 2. Not from today
                            if article_published_date < last_refresh_time and article_published_date < today_start:
                                articles_skipped_old += 1
                                logger.debug(
                                    f'Skipping old article: "{article_data.get("title", "Unknown")}" '
                                    f'(published: {article_published_date}, last refresh: {last_refresh_time}, today: {today_start})'
                                )
                                continue
                        
                        # Create new article
                        article = Article.create_from_feed_entry(feed, article_data)
                        articles_added += 1
                        logger.debug(f'Added new article: {article.title}')
                
                except Exception as e:
                    articles_failed += 1
                    logger.warning(f'Failed to process article: {str(e)}')
                    continue
            
            # Update feed metadata
            self.update_feed_last_fetched(feed)
            
            # Update feed title/description if available
            if hasattr(parsed_feed.feed, 'title') and parsed_feed.feed.title:
                if not feed.title or feed.title != parsed_feed.feed.title:
                    feed.title = parsed_feed.feed.title
            
            if hasattr(parsed_feed.feed, 'description') and parsed_feed.feed.description:
                if not feed.description or feed.description != parsed_feed.feed.description:
                    feed.description = parsed_feed.feed.description
            
            feed.save()
            
            logger.info(
                f'Feed updated: {feed.url} - '
                f'Added: {articles_added}, Updated: {articles_updated}, Failed: {articles_failed}, '
                f'Skipped (old): {articles_skipped_old}'
            )
            
            return FeedUpdateResult(
                success=True,
                feed=feed,
                articles_added=articles_added,
                articles_updated=articles_updated,
                articles_failed=articles_failed,
                fetch_result=fetch_result,
                processing_time=time.time() - start_time
            )
        
        except Exception as e:
            error_msg = f'Feed update failed: {str(e)}'
            logger.error(f'Error updating feed {feed.url}: {error_msg}')
            
            # Still update last_fetched to prevent continuous retries
            self.update_feed_last_fetched(feed)
            
            return FeedUpdateResult(
                success=False,
                feed=feed,
                error_message=error_msg,
                processing_time=time.time() - start_time
            )
    
    async def update_multiple_feeds(
        self,
        feeds: List[Feed],
        force: bool = False,
        max_concurrent: int = 10
    ) -> List[FeedUpdateResult]:
        '''
        Update multiple feeds concurrently
        
        Args:
            feeds: List of feeds to update
            force: Force update regardless of intervals
            max_concurrent: Maximum concurrent updates
            
        Returns:
            List of FeedUpdateResult objects
        '''
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def update_with_semaphore(feed: Feed) -> FeedUpdateResult:
            async with semaphore:
                return await self.update_feed(feed, force)
        
        logger.info(f'Updating {len(feeds)} feeds (max concurrent: {max_concurrent})')
        
        tasks = [update_with_semaphore(feed) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = FeedUpdateResult(
                    success=False,
                    feed=feeds[i],
                    error_message=f'Update failed: {str(result)}'
                )
                final_results.append(error_result)
            else:
                final_results.append(result)
        
        # Log summary
        successful = sum(1 for r in final_results if r.success)
        failed = len(final_results) - successful
        total_added = sum(r.articles_added for r in final_results if r.success)
        
        logger.info(
            f'Feed update batch complete: {successful} successful, {failed} failed, '
            f'{total_added} articles added'
        )
        
        return final_results


# Global feed fetcher instance
feed_fetcher = FeedFetcher()