import pytest
from pathlib import Path
from app.services.opml.parser import OPMLParser, OPMLParseError


class TestOPMLParser:
    '''Test OPML parser functionality'''
    
    @pytest.fixture
    def parser(self):
        '''Create an OPML parser instance'''
        return OPMLParser()
    
    @pytest.fixture
    def valid_opml_simple(self):
        '''Simple valid OPML with flat structure'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
            <head>
                <title>My RSS Feeds</title>
                <dateCreated>Thu, 15 Aug 2025 10:00:00 GMT</dateCreated>
            </head>
            <body>
                <outline text="TechCrunch" title="TechCrunch" type="rss" 
                         xmlUrl="https://techcrunch.com/feed/" 
                         htmlUrl="https://techcrunch.com/"/>
                <outline text="Hacker News" title="Hacker News" type="rss"
                         xmlUrl="https://news.ycombinator.com/rss"
                         htmlUrl="https://news.ycombinator.com/"/>
            </body>
        </opml>'''
    
    @pytest.fixture
    def valid_opml_with_categories(self):
        '''Valid OPML with nested category structure'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
            <head>
                <title>Categorized Feeds</title>
            </head>
            <body>
                <outline text="Technology" title="Technology">
                    <outline text="TechCrunch" type="rss" 
                             xmlUrl="https://techcrunch.com/feed/"
                             htmlUrl="https://techcrunch.com/"
                             description="Tech news"/>
                    <outline text="The Verge" type="rss"
                             xmlUrl="https://www.theverge.com/rss/index.xml"
                             htmlUrl="https://www.theverge.com/"/>
                </outline>
                <outline text="Science" title="Science">
                    <outline text="Nature" type="rss"
                             xmlUrl="https://www.nature.com/nature.rss"
                             htmlUrl="https://www.nature.com/"/>
                </outline>
            </body>
        </opml>'''
    
    @pytest.fixture
    def valid_opml_nested_categories(self):
        '''Valid OPML with deeply nested categories'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
            <head><title>Nested Categories</title></head>
            <body>
                <outline text="News" title="News">
                    <outline text="Technology" title="Technology">
                        <outline text="Startups" title="Startups">
                            <outline text="TechCrunch" type="rss"
                                     xmlUrl="https://techcrunch.com/feed/"/>
                        </outline>
                        <outline text="Gadgets" title="Gadgets">
                            <outline text="Engadget" type="rss"
                                     xmlUrl="https://www.engadget.com/rss.xml"/>
                        </outline>
                    </outline>
                </outline>
            </body>
        </opml>'''
    
    @pytest.fixture
    def invalid_opml_malformed_xml(self):
        '''Malformed XML that should fail parsing'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
            <head>
                <title>Broken XML</title>
            </head>
            <body>
                <outline text="Feed" xmlUrl="https://example.com/feed"
                <!-- Missing closing tag -->
            </body>'''
    
    @pytest.fixture
    def invalid_opml_no_body(self):
        '''OPML without body element'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
            <head>
                <title>No Body</title>
            </head>
        </opml>'''
    
    @pytest.fixture
    def opml_with_empty_outlines(self):
        '''OPML with empty outline elements'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="2.0">
            <head><title>Empty Outlines</title></head>
            <body>
                <outline />
                <outline text="Valid Feed" xmlUrl="https://example.com/feed"/>
                <outline text="" xmlUrl=""/>
            </body>
        </opml>'''
    
    def test_parse_simple_opml(self, parser, valid_opml_simple):
        '''Test parsing simple OPML without categories'''
        result = parser.parse(valid_opml_simple)
        
        assert result is not None
        assert result['title'] == 'My RSS Feeds'
        assert len(result['categories']) == 0
        assert len(result['feeds']) == 2
        
        # Check first feed
        feed1 = result['feeds'][0]
        assert feed1['title'] == 'TechCrunch'
        assert feed1['xml_url'] == 'https://techcrunch.com/feed/'
        assert feed1['html_url'] == 'https://techcrunch.com/'
        assert feed1['category_path'] is None
        
        # Check second feed
        feed2 = result['feeds'][1]
        assert feed2['title'] == 'Hacker News'
        assert feed2['xml_url'] == 'https://news.ycombinator.com/rss'
        assert feed2['html_url'] == 'https://news.ycombinator.com/'
    
    def test_parse_opml_with_categories(self, parser, valid_opml_with_categories):
        '''Test parsing OPML with category structure'''
        result = parser.parse(valid_opml_with_categories)
        
        assert result['title'] == 'Categorized Feeds'
        assert len(result['categories']) == 2
        assert len(result['feeds']) == 3
        
        # Check categories
        categories = {cat['name']: cat for cat in result['categories']}
        assert 'Technology' in categories
        assert 'Science' in categories
        assert categories['Technology']['parent_path'] is None
        assert categories['Science']['parent_path'] is None
        
        # Check feeds with categories
        feeds_by_title = {feed['title']: feed for feed in result['feeds']}
        assert feeds_by_title['TechCrunch']['category_path'] == 'Technology'
        assert feeds_by_title['The Verge']['category_path'] == 'Technology'
        assert feeds_by_title['Nature']['category_path'] == 'Science'
        assert feeds_by_title['TechCrunch']['description'] == 'Tech news'
    
    def test_parse_nested_categories(self, parser, valid_opml_nested_categories):
        '''Test parsing OPML with deeply nested categories'''
        result = parser.parse(valid_opml_nested_categories)
        
        assert len(result['categories']) == 4  # News, Technology, Startups, Gadgets
        
        # Check category hierarchy
        categories = {cat['name']: cat for cat in result['categories']}
        assert categories['News']['parent_path'] is None
        assert categories['Technology']['parent_path'] == 'News'
        assert categories['Startups']['parent_path'] == 'News/Technology'
        assert categories['Gadgets']['parent_path'] == 'News/Technology'
        
        # Check feed categories
        feeds_by_title = {feed['title']: feed for feed in result['feeds']}
        assert feeds_by_title['TechCrunch']['category_path'] == 'News/Technology/Startups'
        assert feeds_by_title['Engadget']['category_path'] == 'News/Technology/Gadgets'
    
    def test_parse_malformed_xml(self, parser, invalid_opml_malformed_xml):
        '''Test that malformed XML raises appropriate error'''
        with pytest.raises(OPMLParseError) as exc_info:
            parser.parse(invalid_opml_malformed_xml)
        
        assert 'Failed to parse OPML' in str(exc_info.value)
    
    def test_parse_empty_body(self, parser, invalid_opml_no_body):
        '''Test parsing OPML without body returns empty results'''
        result = parser.parse(invalid_opml_no_body)
        
        assert result['title'] == 'No Body'
        assert result['categories'] == []
        assert result['feeds'] == []
    
    def test_parse_empty_string(self, parser):
        '''Test that empty string raises error'''
        with pytest.raises(OPMLParseError) as exc_info:
            parser.parse('')
        
        assert 'Empty OPML content' in str(exc_info.value)
    
    def test_parse_none(self, parser):
        '''Test that None raises error'''
        with pytest.raises(OPMLParseError) as exc_info:
            parser.parse(None)
        
        assert 'Empty OPML content' in str(exc_info.value)
    
    def test_parse_invalid_xml_format(self, parser):
        '''Test that non-XML content raises error'''
        with pytest.raises(OPMLParseError) as exc_info:
            parser.parse('This is not XML')
        
        assert 'Failed to parse OPML' in str(exc_info.value)
    
    def test_parse_empty_outlines(self, parser, opml_with_empty_outlines):
        '''Test handling of empty outline elements'''
        result = parser.parse(opml_with_empty_outlines)
        
        # Should only include valid feed
        assert len(result['feeds']) == 1
        assert result['feeds'][0]['title'] == 'Valid Feed'
        assert result['feeds'][0]['xml_url'] == 'https://example.com/feed'
    
    def test_feed_url_normalization(self, parser):
        '''Test that feed URLs are normalized'''
        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline text="Feed 1" xmlUrl="  https://example.com/feed  "/>
                <outline text="Feed 2" xmlUrl="https://example.com//feed//"/>
                <outline text="Feed 3" xmlUrl="HTTPS://EXAMPLE.COM/FEED"/>
            </body>
        </opml>'''
        
        result = parser.parse(opml)
        
        # All feeds should have normalized URLs
        assert result['feeds'][0]['xml_url'] == 'https://example.com/feed'
        assert result['feeds'][1]['xml_url'] == 'https://example.com/feed/'
        # URL case should be preserved for path but not scheme
        assert result['feeds'][2]['xml_url'] == 'https://EXAMPLE.COM/FEED'
    
    def test_missing_required_attributes(self, parser):
        '''Test handling of feeds missing required xmlUrl'''
        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline text="No URL" type="rss"/>
                <outline text="Valid" xmlUrl="https://example.com/feed"/>
            </body>
        </opml>'''
        
        result = parser.parse(opml)
        
        # Should only include feed with URL
        assert len(result['feeds']) == 1
        assert result['feeds'][0]['title'] == 'Valid'
    
    def test_opml_version_1(self, parser):
        '''Test parsing OPML version 1.0'''
        opml = '''<?xml version="1.0"?>
        <opml version="1.0">
            <head><title>OPML 1.0</title></head>
            <body>
                <outline text="Feed" xmlUrl="https://example.com/feed"/>
            </body>
        </opml>'''
        
        result = parser.parse(opml)
        assert result['title'] == 'OPML 1.0'
        assert len(result['feeds']) == 1
    
    def test_preserve_feed_metadata(self, parser):
        '''Test that all feed metadata is preserved'''
        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline text="Complete Feed"
                         title="Feed Title"
                         type="rss"
                         xmlUrl="https://example.com/feed"
                         htmlUrl="https://example.com"
                         description="Feed description"
                         language="en-US"
                         version="RSS2"/>
            </body>
        </opml>'''
        
        result = parser.parse(opml)
        feed = result['feeds'][0]
        
        assert feed['title'] == 'Feed Title'  # title takes precedence over text
        assert feed['xml_url'] == 'https://example.com/feed'
        assert feed['html_url'] == 'https://example.com'
        assert feed['description'] == 'Feed description'
        assert feed['language'] == 'en-US'
        assert feed['version'] == 'RSS2'
    
    def test_category_with_attributes(self, parser):
        '''Test that category attributes are preserved'''
        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline text="Tech" title="Technology" description="Tech news">
                    <outline text="Feed" xmlUrl="https://example.com/feed"/>
                </outline>
            </body>
        </opml>'''
        
        result = parser.parse(opml)
        
        category = result['categories'][0]
        assert category['name'] == 'Technology'  # title takes precedence
        assert category['description'] == 'Tech news'
    
    def test_duplicate_category_names(self, parser):
        '''Test handling of duplicate category names at same level'''
        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline text="Tech">
                    <outline text="Feed1" xmlUrl="https://example.com/feed1"/>
                </outline>
                <outline text="Tech">
                    <outline text="Feed2" xmlUrl="https://example.com/feed2"/>
                </outline>
            </body>
        </opml>'''
        
        result = parser.parse(opml)
        
        # Should create two Tech categories with different paths
        assert len(result['categories']) == 2
        # Feeds should be in their respective categories
        assert len(result['feeds']) == 2
    
    def test_mixed_content_and_categories(self, parser):
        '''Test OPML with both categorized and uncategorized feeds'''
        opml = '''<?xml version="1.0"?>
        <opml version="2.0">
            <body>
                <outline text="Direct Feed" xmlUrl="https://example.com/direct"/>
                <outline text="Category">
                    <outline text="Categorized Feed" xmlUrl="https://example.com/cat"/>
                </outline>
            </body>
        </opml>'''
        
        result = parser.parse(opml)
        
        assert len(result['categories']) == 1
        assert len(result['feeds']) == 2
        
        feeds_by_title = {f['title']: f for f in result['feeds']}
        assert feeds_by_title['Direct Feed']['category_path'] is None
        assert feeds_by_title['Categorized Feed']['category_path'] == 'Category'