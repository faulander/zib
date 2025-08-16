'''Feed validation service for OPML import'''

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import aiohttp
import feedparser
from loguru import logger
from app.models.base import ImportFeedValidation
from app.core.database import db


class FeedValidationError(Exception):
    '''Exception raised when feed validation fails'''
    pass


@dataclass
class FeedValidationResult:
    '''Result of feed validation'''
    feed_url: str
    is_valid: bool
    final_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    feed_type: Optional[str] = None  # rss, atom, unknown
    language: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    cached: bool = False


class FeedValidator:
    '''Validates RSS/Atom feed URLs and extracts metadata'''
    
    def __init__(self, cache_ttl: int = 3600):
        '''
        Initialize feed validator
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        '''
        self.cache_ttl = cache_ttl
        self.user_agent = 'Zib RSS Reader/1.0 (+https://github.com/zib-reader)'
    
    async def validate_feed(self, 
                           feed_url: str,
                           session: Optional[aiohttp.ClientSession] = None,
                           use_cache: bool = True,
                           max_retries: int = 3) -> FeedValidationResult:
        '''
        Validate a single feed URL
        
        Args:
            feed_url: URL of the feed to validate
            session: Optional aiohttp session to reuse
            use_cache: Whether to use cached results
            max_retries: Maximum number of retry attempts
            
        Returns:
            FeedValidationResult with validation details
        '''
        # Check cache first if enabled
        if use_cache:
            cached_result = self.get_cached_validation(feed_url)
            if cached_result:
                return cached_result
        
        # Create session if not provided
        close_session = False
        if not session:
            session = aiohttp.ClientSession()
            close_session = True
        
        try:
            result = await self._validate_with_retry(
                feed_url, session, max_retries
            )
            
            # Cache the result if caching is enabled
            if use_cache:
                self.save_to_cache(result)
            
            return result
            
        finally:
            if close_session:
                await session.close()
    
    async def validate_batch(self,
                            feed_urls: List[str],
                            session: Optional[aiohttp.ClientSession] = None,
                            max_concurrent: int = 10,
                            use_cache: bool = True) -> List[FeedValidationResult]:
        '''
        Validate multiple feed URLs concurrently
        
        Args:
            feed_urls: List of feed URLs to validate
            session: Optional aiohttp session to reuse
            max_concurrent: Maximum concurrent validations
            use_cache: Whether to use cached results
            
        Returns:
            List of FeedValidationResult objects
        '''
        # Create session if not provided
        close_session = False
        if not session:
            session = aiohttp.ClientSession()
            close_session = True
        
        try:
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def validate_with_semaphore(url):
                async with semaphore:
                    return await self.validate_feed(url, session, use_cache)
            
            # Validate all feeds concurrently
            tasks = [validate_with_semaphore(url) for url in feed_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result for exception
                    final_results.append(FeedValidationResult(
                        feed_url=feed_urls[i],
                        is_valid=False,
                        error_message=str(result),
                        error_code='exception'
                    ))
                else:
                    final_results.append(result)
            
            return final_results
            
        finally:
            if close_session:
                await session.close()
    
    async def _validate_with_retry(self,
                                  feed_url: str,
                                  session: aiohttp.ClientSession,
                                  max_retries: int) -> FeedValidationResult:
        '''
        Validate feed with retry logic
        
        Args:
            feed_url: Feed URL to validate
            session: aiohttp session
            max_retries: Maximum retry attempts
            
        Returns:
            FeedValidationResult
        '''
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Add exponential backoff for retries
                if attempt > 0:
                    await asyncio.sleep(2 ** attempt)
                
                return await self._perform_validation(feed_url, session)
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                logger.debug(f'Validation attempt {attempt + 1} failed for {feed_url}: {e}')
                continue
        
        # All retries failed
        error_code = 'timeout' if isinstance(last_error, asyncio.TimeoutError) else 'network_error'
        return FeedValidationResult(
            feed_url=feed_url,
            is_valid=False,
            error_message=str(last_error),
            error_code=error_code
        )
    
    async def _perform_validation(self,
                                 feed_url: str,
                                 session: aiohttp.ClientSession) -> FeedValidationResult:
        '''
        Perform actual feed validation
        
        Args:
            feed_url: Feed URL to validate
            session: aiohttp session
            
        Returns:
            FeedValidationResult
        '''
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml'
        }
        
        try:
            # Make HTTP request with timeout
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.get(feed_url, headers=headers, timeout=timeout) as response:
                # Handle HTTP errors
                if response.status >= 400:
                    return FeedValidationResult(
                        feed_url=feed_url,
                        is_valid=False,
                        error_message=f'HTTP {response.status}: {response.reason}',
                        error_code=str(response.status)
                    )
                
                # Get final URL after redirects
                final_url = str(response.url)
                
                # Read feed content
                content = await response.text()
                
                # Parse feed with feedparser
                parsed = feedparser.parse(content)
                
                # Check if parsing succeeded
                if parsed.bozo:
                    # Feed has errors
                    error_msg = str(parsed.bozo_exception) if hasattr(parsed, 'bozo_exception') else 'Invalid feed format'
                    return FeedValidationResult(
                        feed_url=feed_url,
                        is_valid=False,
                        final_url=final_url,
                        error_message=error_msg,
                        error_code='invalid_feed'
                    )
                
                # Extract feed metadata
                feed = parsed.feed if hasattr(parsed, 'feed') else {}
                
                # Determine feed type
                feed_type = 'unknown'
                if hasattr(parsed, 'version'):
                    version = parsed.version.lower()
                    if 'rss' in version:
                        feed_type = 'rss'
                    elif 'atom' in version:
                        feed_type = 'atom'
                
                # Build successful result
                return FeedValidationResult(
                    feed_url=feed_url,
                    is_valid=True,
                    final_url=final_url,
                    title=feed.get('title'),
                    description=feed.get('subtitle') or feed.get('description'),
                    feed_type=feed_type,
                    language=feed.get('language'),
                    cached=False
                )
                
        except asyncio.TimeoutError:
            return FeedValidationResult(
                feed_url=feed_url,
                is_valid=False,
                error_message='Request timeout',
                error_code='timeout'
            )
        except aiohttp.ClientError as e:
            return FeedValidationResult(
                feed_url=feed_url,
                is_valid=False,
                error_message=str(e),
                error_code='network_error'
            )
        except Exception as e:
            logger.error(f'Unexpected error validating {feed_url}: {e}')
            return FeedValidationResult(
                feed_url=feed_url,
                is_valid=False,
                error_message=str(e),
                error_code='unknown_error'
            )
    
    def get_cached_validation(self, feed_url: str) -> Optional[FeedValidationResult]:
        '''
        Get cached validation result from database
        
        Args:
            feed_url: Feed URL to look up
            
        Returns:
            Cached FeedValidationResult or None if not found/expired
        '''
        try:
            # Query database for cached result
            cached = ImportFeedValidation.select().where(
                ImportFeedValidation.feed_url == feed_url,
                ImportFeedValidation.expires_at > datetime.now()
            ).first()
            
            if cached:
                return FeedValidationResult(
                    feed_url=cached.feed_url,
                    is_valid=cached.is_valid,
                    final_url=cached.final_url,
                    title=cached.title,
                    description=cached.description,
                    feed_type=cached.feed_type,
                    language=None,  # Not stored in cache
                    error_message=cached.error_message,
                    error_code=cached.error_code,
                    cached=True
                )
            
        except Exception as e:
            logger.debug(f'Cache lookup failed for {feed_url}: {e}')
        
        return None
    
    def save_to_cache(self, result: FeedValidationResult):
        '''
        Save validation result to cache
        
        Args:
            result: FeedValidationResult to cache
        '''
        try:
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(seconds=self.cache_ttl)
            
            # Save or update cache entry
            ImportFeedValidation.insert(
                feed_url=result.feed_url,
                is_valid=result.is_valid,
                final_url=result.final_url,
                title=result.title,
                description=result.description,
                feed_type=result.feed_type,
                error_message=result.error_message,
                error_code=result.error_code,
                validated_at=datetime.now(),
                expires_at=expires_at
            ).on_conflict(
                conflict_target=[ImportFeedValidation.feed_url],
                preserve=[
                    ImportFeedValidation.is_valid,
                    ImportFeedValidation.final_url,
                    ImportFeedValidation.title,
                    ImportFeedValidation.description,
                    ImportFeedValidation.feed_type,
                    ImportFeedValidation.error_message,
                    ImportFeedValidation.error_code,
                    ImportFeedValidation.validated_at,
                    ImportFeedValidation.expires_at
                ]
            ).execute()
            
        except Exception as e:
            logger.debug(f'Failed to cache validation result for {result.feed_url}: {e}')
    
    async def clear_expired_cache(self):
        '''
        Clear expired validation cache entries
        '''
        try:
            deleted = ImportFeedValidation.delete().where(
                ImportFeedValidation.expires_at < datetime.now()
            ).execute()
            logger.info(f'Cleared {deleted} expired validation cache entries')
        except Exception as e:
            logger.error(f'Failed to clear expired cache: {e}')