'''OPML parser implementation for importing RSS feed collections'''

import xmltodict
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urlunparse
from loguru import logger


class OPMLParseError(Exception):
    '''Exception raised when OPML parsing fails'''
    pass


class OPMLParser:
    '''Parser for OPML (Outline Processor Markup Language) files'''
    
    def __init__(self):
        '''Initialize the OPML parser'''
        self.categories = []
        self.feeds = []
        self.category_paths = {}
    
    def parse(self, opml_content: str) -> Dict[str, Any]:
        '''
        Parse OPML content and extract categories and feeds
        
        Args:
            opml_content: OPML XML content as string
            
        Returns:
            Dictionary containing:
                - title: OPML title
                - categories: List of category dictionaries
                - feeds: List of feed dictionaries
                
        Raises:
            OPMLParseError: If parsing fails
        '''
        if not opml_content:
            raise OPMLParseError('Empty OPML content')
        
        # Reset state for new parse
        self.categories = []
        self.feeds = []
        self.category_paths = {}
        
        try:
            # Parse XML to dictionary
            doc = xmltodict.parse(opml_content)
        except Exception as e:
            raise OPMLParseError(f'Failed to parse OPML: {str(e)}')
        
        # Extract OPML structure
        if 'opml' not in doc:
            raise OPMLParseError('Invalid OPML structure: missing opml element')
        
        opml = doc['opml']
        
        # Extract title from head
        title = None
        if 'head' in opml and opml['head']:
            head = opml['head']
            if isinstance(head, dict):
                title = head.get('title', 'Untitled')
        
        # Process body if it exists
        if 'body' in opml and opml['body']:
            body = opml['body']
            if 'outline' in body:
                outlines = body['outline']
                # Ensure outlines is a list
                if not isinstance(outlines, list):
                    outlines = [outlines]
                
                # Process each outline
                for outline in outlines:
                    if outline:  # Skip None or empty outlines
                        self._process_outline(outline, parent_path=None)
        
        return {
            'title': title or 'Untitled',
            'categories': self.categories,
            'feeds': self.feeds
        }
    
    def _process_outline(self, outline: Dict[str, Any], parent_path: Optional[str]):
        '''
        Process an outline element recursively
        
        Args:
            outline: Outline dictionary from xmltodict
            parent_path: Parent category path (e.g., "News/Technology")
        '''
        if not isinstance(outline, dict):
            return
        
        # Skip empty outlines
        if not outline:
            return
        
        # Get outline attributes with @ prefix (xmltodict convention)
        attrs = self._extract_attributes(outline)
        
        # Check if this is a feed (has xmlUrl) or category
        if attrs.get('xmlUrl'):
            # It's a feed - process and add to feeds list
            self._process_feed(attrs, parent_path)
        elif attrs.get('text') or attrs.get('title'):
            # It's a category - process recursively
            self._process_category(outline, attrs, parent_path)
    
    def _extract_attributes(self, outline: Dict[str, Any]) -> Dict[str, str]:
        '''
        Extract attributes from outline element
        
        Args:
            outline: Outline dictionary
            
        Returns:
            Dictionary of attributes without @ prefix
        '''
        attrs = {}
        
        # Handle attributes with @ prefix (xmltodict convention)
        for key, value in outline.items():
            if key.startswith('@'):
                # Remove @ prefix and store attribute
                clean_key = key[1:]
                attrs[clean_key] = value
        
        return attrs
    
    def _process_feed(self, attrs: Dict[str, str], parent_path: Optional[str]):
        '''
        Process a feed outline and add to feeds list
        
        Args:
            attrs: Feed attributes
            parent_path: Parent category path
        '''
        # Skip feeds without URL
        xml_url = attrs.get('xmlUrl', '').strip()
        if not xml_url:
            return
        
        # Skip feeds with empty URL
        if not xml_url or xml_url == '':
            return
        
        # Normalize URL
        xml_url = self._normalize_url(xml_url)
        
        # Get feed title (prefer title over text)
        title = attrs.get('title') or attrs.get('text') or xml_url
        
        # Build feed dictionary
        feed = {
            'title': title,
            'xml_url': xml_url,
            'html_url': attrs.get('htmlUrl'),
            'description': attrs.get('description'),
            'category_path': parent_path,
            'language': attrs.get('language'),
            'version': attrs.get('version'),
            'type': attrs.get('type', 'rss')
        }
        
        self.feeds.append(feed)
    
    def _process_category(self, outline: Dict[str, Any], attrs: Dict[str, str], 
                         parent_path: Optional[str]):
        '''
        Process a category outline and its children
        
        Args:
            outline: Category outline dictionary
            attrs: Category attributes
            parent_path: Parent category path
        '''
        # Get category name (prefer title over text)
        name = attrs.get('title') or attrs.get('text') or 'Unnamed'
        
        # Build category path
        if parent_path:
            category_path = f'{parent_path}/{name}'
        else:
            category_path = name
        
        # Check for duplicate category at same path
        category_key = category_path
        counter = 1
        while category_key in self.category_paths:
            category_key = f'{category_path}_{counter}'
            counter += 1
        
        # Store category path for duplicate detection
        self.category_paths[category_key] = True
        
        # Add category to list
        category = {
            'name': name,
            'parent_path': parent_path,
            'full_path': category_key,
            'description': attrs.get('description')
        }
        self.categories.append(category)
        
        # Process child outlines if they exist
        if 'outline' in outline:
            children = outline['outline']
            # Ensure children is a list
            if not isinstance(children, list):
                children = [children]
            
            # Process each child outline
            for child in children:
                if child:  # Skip None or empty children
                    self._process_outline(child, category_key)
    
    def _normalize_url(self, url: str) -> str:
        '''
        Normalize a URL by cleaning up formatting
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        '''
        # Strip whitespace
        url = url.strip()
        
        # Parse URL
        parsed = urlparse(url)
        
        # Normalize scheme to lowercase
        scheme = parsed.scheme.lower() if parsed.scheme else 'https'
        
        # Clean up path - remove double slashes
        path = parsed.path
        if path:
            # Replace multiple slashes with single slash
            import re
            path = re.sub(r'/+', '/', path)
        
        # Rebuild URL with normalized components
        normalized = urlunparse((
            scheme,
            parsed.netloc,
            path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return normalized