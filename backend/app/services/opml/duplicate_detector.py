'''Duplicate detection and handling service for OPML import'''

from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
from loguru import logger
from app.models.base import Feed, Category


class DuplicateDetectionError(Exception):
    '''Exception raised when duplicate detection fails'''
    pass


@dataclass
class DuplicateResolution:
    '''Resolution for handling a duplicate item'''
    action: str  # 'skip', 'merge', 'replace', 'create_new'
    existing_id: Optional[int] = None
    new_name: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class FeedDuplicate:
    '''Information about a duplicate feed'''
    opml_feed: Dict[str, Any]
    existing_feed: Feed
    normalized_url: str
    resolution: Optional[DuplicateResolution] = None


@dataclass
class CategoryDuplicate:
    '''Information about a duplicate category'''
    opml_category: Dict[str, Any]
    existing_category: Category
    path: str
    resolution: Optional[DuplicateResolution] = None


class DuplicateDetector:
    '''Detects and handles duplicates during OPML import'''
    
    def __init__(self, user_id: int, merge_categories: bool = True, 
                 skip_existing_feeds: bool = True):
        '''
        Initialize duplicate detector
        
        Args:
            user_id: ID of the user importing OPML
            merge_categories: Whether to merge categories with same name
            skip_existing_feeds: Whether to skip feeds that already exist
        '''
        self.user_id = user_id
        self.merge_categories = merge_categories
        self.skip_existing_feeds = skip_existing_feeds
        
        # Cache existing data
        self._existing_feeds: Dict[str, Feed] = {}
        self._existing_categories: Dict[str, Category] = {}
        self._normalized_urls: Dict[str, str] = {}
        self._category_paths: Dict[str, str] = {}
        
    async def load_existing_data(self):
        '''Load existing feeds and categories from database'''
        try:
            # Load existing feeds (all for now since we don't have user_id in current models)
            existing_feeds = Feed.select()
            for feed in existing_feeds:
                normalized_url = self._normalize_feed_url(feed.url)
                self._existing_feeds[normalized_url] = feed
                self._normalized_urls[feed.url] = normalized_url
            
            # Load existing categories (all for now since we don't have user_id in current models)
            existing_categories = Category.select()
            for category in existing_categories:
                # For now, just use category name as path since parent_id is not in current model
                path = category.name
                self._existing_categories[path] = category
                self._category_paths[category.name] = path
                
            logger.info(f'Loaded {len(self._existing_feeds)} existing feeds and '
                       f'{len(self._existing_categories)} existing categories')
                       
        except Exception as e:
            raise DuplicateDetectionError(f'Failed to load existing data: {str(e)}')
    
    def detect_feed_duplicates(self, feeds: List[Dict[str, Any]]) -> List[FeedDuplicate]:
        '''
        Detect duplicate feeds in OPML data
        
        Args:
            feeds: List of feed dictionaries from OPML parser
            
        Returns:
            List of FeedDuplicate objects
        '''
        duplicates = []
        
        for feed in feeds:
            feed_url = feed.get('xml_url')
            if not feed_url:
                continue
                
            normalized_url = self._normalize_feed_url(feed_url)
            
            # Check if feed already exists
            if normalized_url in self._existing_feeds:
                existing_feed = self._existing_feeds[normalized_url]
                
                duplicate = FeedDuplicate(
                    opml_feed=feed,
                    existing_feed=existing_feed,
                    normalized_url=normalized_url
                )
                
                # Determine resolution
                duplicate.resolution = self._resolve_feed_duplicate(duplicate)
                duplicates.append(duplicate)
        
        return duplicates
    
    def detect_category_duplicates(self, categories: List[Dict[str, Any]]) -> List[CategoryDuplicate]:
        '''
        Detect duplicate categories in OPML data
        
        Args:
            categories: List of category dictionaries from OPML parser
            
        Returns:
            List of CategoryDuplicate objects
        '''
        duplicates = []
        
        for category in categories:
            category_name = category.get('name')
            parent_path = category.get('parent_path')
            
            if not category_name:
                continue
                
            # Build full path for this category
            if parent_path:
                full_path = f'{parent_path}/{category_name}'
            else:
                full_path = category_name
            
            # Check if category already exists
            if full_path in self._existing_categories:
                existing_category = self._existing_categories[full_path]
                
                duplicate = CategoryDuplicate(
                    opml_category=category,
                    existing_category=existing_category,
                    path=full_path
                )
                
                # Determine resolution
                duplicate.resolution = self._resolve_category_duplicate(duplicate)
                duplicates.append(duplicate)
        
        return duplicates
    
    def get_unique_feeds(self, feeds: List[Dict[str, Any]], 
                        duplicates: List[FeedDuplicate]) -> List[Dict[str, Any]]:
        '''
        Get feeds that should be created (non-duplicates and resolved duplicates)
        
        Args:
            feeds: Original list of feeds from OPML
            duplicates: List of detected duplicates
            
        Returns:
            List of feeds to create
        '''
        # Create set of duplicate feed URLs for quick lookup
        duplicate_urls = {dup.normalized_url for dup in duplicates 
                         if dup.resolution and dup.resolution.action == 'skip'}
        
        unique_feeds = []
        for feed in feeds:
            feed_url = feed.get('xml_url')
            if not feed_url:
                continue
                
            normalized_url = self._normalize_feed_url(feed_url)
            
            # Skip if this is a duplicate that should be skipped
            if normalized_url not in duplicate_urls:
                unique_feeds.append(feed)
        
        return unique_feeds
    
    def get_unique_categories(self, categories: List[Dict[str, Any]], 
                            duplicates: List[CategoryDuplicate]) -> List[Dict[str, Any]]:
        '''
        Get categories that should be created (non-duplicates and resolved duplicates)
        
        Args:
            categories: Original list of categories from OPML
            duplicates: List of detected duplicates
            
        Returns:
            List of categories to create
        '''
        # Create set of duplicate category paths for quick lookup
        duplicate_paths = {dup.path for dup in duplicates 
                          if dup.resolution and dup.resolution.action in ['skip', 'merge']}
        
        unique_categories = []
        for category in categories:
            category_name = category.get('name')
            parent_path = category.get('parent_path')
            
            if not category_name:
                continue
                
            # Build full path
            if parent_path:
                full_path = f'{parent_path}/{category_name}'
            else:
                full_path = category_name
            
            # Skip if this is a duplicate that should be skipped/merged
            if full_path not in duplicate_paths:
                unique_categories.append(category)
        
        return unique_categories
    
    def _normalize_feed_url(self, url: str) -> str:
        '''
        Normalize a feed URL for duplicate detection
        
        Args:
            url: Feed URL to normalize
            
        Returns:
            Normalized URL
        '''
        if not url:
            return ''
            
        try:
            # Strip whitespace and convert to lowercase for comparison
            url = url.strip()
            
            # Parse URL
            parsed = urlparse(url)
            
            # If no scheme, assume https and reparse
            if not parsed.scheme:
                url = f'https://{url}'
                parsed = urlparse(url)
            
            # Normalize scheme to lowercase
            scheme = parsed.scheme.lower()
            
            # Normalize netloc (domain) to lowercase
            netloc = parsed.netloc.lower()
            
            # Normalize path - lowercase, remove trailing slash unless it's root, collapse multiple slashes
            path = parsed.path.lower() if parsed.path else ''
            if path:
                # Remove multiple consecutive slashes
                import re
                path = re.sub(r'/+', '/', path)
                # Remove trailing slash unless it's the root path
                if path != '/' and path.endswith('/'):
                    path = path.rstrip('/')
            
            # Rebuild normalized URL
            normalized = urlunparse((
                scheme,
                netloc,
                path,
                parsed.params,
                parsed.query,
                ''  # Remove fragment
            ))
            
            return normalized
            
        except Exception as e:
            logger.warning(f'Failed to normalize URL {url}: {e}')
            return url.strip().lower()
    
    def _build_category_path(self, category: Category) -> str:
        '''
        Build full path for a category including parent hierarchy
        
        Args:
            category: Category model instance
            
        Returns:
            Full category path (simplified for current model without parent_id)
        '''
        # Current model doesn't have parent_id, so just return the name
        # This will be enhanced when we add hierarchical category support
        return category.name
    
    def _resolve_feed_duplicate(self, duplicate: FeedDuplicate) -> DuplicateResolution:
        '''
        Determine how to resolve a feed duplicate
        
        Args:
            duplicate: FeedDuplicate object
            
        Returns:
            DuplicateResolution
        '''
        if self.skip_existing_feeds:
            return DuplicateResolution(
                action='skip',
                existing_id=duplicate.existing_feed.id,
                reason=f'Feed already exists: {duplicate.existing_feed.title}'
            )
        else:
            # Could implement other strategies like replace or merge
            return DuplicateResolution(
                action='replace',
                existing_id=duplicate.existing_feed.id,
                reason='Replacing existing feed with OPML data'
            )
    
    def _resolve_category_duplicate(self, duplicate: CategoryDuplicate) -> DuplicateResolution:
        '''
        Determine how to resolve a category duplicate
        
        Args:
            duplicate: CategoryDuplicate object
            
        Returns:
            DuplicateResolution
        '''
        if self.merge_categories:
            return DuplicateResolution(
                action='merge',
                existing_id=duplicate.existing_category.id,
                reason=f'Merging with existing category: {duplicate.existing_category.name}'
            )
        else:
            # Create with modified name
            base_name = duplicate.opml_category.get('name', 'Unnamed')
            counter = 1
            new_name = f'{base_name} (Imported {counter})'
            
            # Check if this name already exists
            while self._category_name_exists(new_name):
                counter += 1
                new_name = f'{base_name} (Imported {counter})'
            
            return DuplicateResolution(
                action='create_new',
                new_name=new_name,
                reason=f'Creating new category with modified name: {new_name}'
            )
    
    def _category_name_exists(self, name: str) -> bool:
        '''
        Check if a category name already exists
        
        Args:
            name: Category name to check
            
        Returns:
            True if name exists
        '''
        try:
            Category.select().where(Category.name == name).get()
            return True
        except Category.DoesNotExist:
            return False
    
    def get_import_summary(self, feeds: List[Dict[str, Any]], 
                          categories: List[Dict[str, Any]],
                          feed_duplicates: List[FeedDuplicate],
                          category_duplicates: List[CategoryDuplicate]) -> Dict[str, Any]:
        '''
        Generate a summary of the import operation
        
        Args:
            feeds: Original feeds from OPML
            categories: Original categories from OPML
            feed_duplicates: Detected feed duplicates
            category_duplicates: Detected category duplicates
            
        Returns:
            Summary dictionary
        '''
        unique_feeds = self.get_unique_feeds(feeds, feed_duplicates)
        unique_categories = self.get_unique_categories(categories, category_duplicates)
        
        summary = {
            'total_feeds': len(feeds),
            'total_categories': len(categories),
            'new_feeds': len(unique_feeds),
            'new_categories': len(unique_categories),
            'duplicate_feeds': len(feed_duplicates),
            'duplicate_categories': len(category_duplicates),
            'feed_duplicates': [
                {
                    'title': dup.opml_feed.get('title', 'Untitled'),
                    'url': dup.opml_feed.get('xml_url'),
                    'existing_title': dup.existing_feed.title,
                    'action': dup.resolution.action if dup.resolution else 'unknown',
                    'reason': dup.resolution.reason if dup.resolution else None
                }
                for dup in feed_duplicates
            ],
            'category_duplicates': [
                {
                    'name': dup.opml_category.get('name', 'Unnamed'),
                    'path': dup.path,
                    'existing_name': dup.existing_category.name,
                    'action': dup.resolution.action if dup.resolution else 'unknown',
                    'reason': dup.resolution.reason if dup.resolution else None
                }
                for dup in category_duplicates
            ]
        }
        
        return summary