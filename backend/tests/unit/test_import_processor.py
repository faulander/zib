import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from datetime import datetime
import asyncio
from app.services.opml.import_processor import (
    ImportProcessor,
    ImportProcessorError,
    ImportProcessorResult
)
from app.services.opml import (
    ImportStatus,
    ImportPhase,
    ImportResults,
    FeedDuplicate,
    CategoryDuplicate,
    DuplicateResolution,
    FeedValidationResult
)
from app.models.base import Feed, Category


class TestImportProcessor:
    '''Test end-to-end OPML import processing'''
    
    @pytest.fixture
    def processor(self):
        '''Create an import processor instance'''
        return ImportProcessor()
    
    @pytest.fixture
    def user_id(self):
        '''User ID for testing'''
        return 123
    
    @pytest.fixture
    def sample_opml_content(self):
        '''Sample OPML content for testing'''
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="1.0">
            <head>
                <title>Test Subscriptions</title>
            </head>
            <body>
                <outline text="Technology">
                    <outline text="TechCrunch" xmlUrl="https://techcrunch.com/feed/" htmlUrl="https://techcrunch.com/"/>
                    <outline text="Hacker News" xmlUrl="https://news.ycombinator.com/rss" htmlUrl="https://news.ycombinator.com/"/>
                </outline>
                <outline text="News">
                    <outline text="BBC" xmlUrl="https://feeds.bbci.co.uk/news/rss.xml" htmlUrl="https://www.bbc.com/news"/>
                </outline>
            </body>
        </opml>'''
    
    @pytest.fixture
    def sample_import_options(self):
        '''Sample import options'''
        return {
            'duplicate_strategy': 'skip',
            'validate_feeds': True,
            'category_parent_id': None,
            'merge_categories': True,
            'skip_existing_feeds': True
        }
    
    @pytest.fixture
    def mock_parsed_opml(self):
        '''Mock parsed OPML data'''
        return {
            'categories': [
                {
                    'name': 'Technology',
                    'parent_path': None,
                    'full_path': 'Technology',
                    'description': 'Tech news'
                },
                {
                    'name': 'News',
                    'parent_path': None,
                    'full_path': 'News',
                    'description': 'General news'
                }
            ],
            'feeds': [
                {
                    'title': 'TechCrunch',
                    'xml_url': 'https://techcrunch.com/feed/',
                    'html_url': 'https://techcrunch.com/',
                    'category_path': 'Technology'
                },
                {
                    'title': 'Hacker News',
                    'xml_url': 'https://news.ycombinator.com/rss',
                    'html_url': 'https://news.ycombinator.com/',
                    'category_path': 'Technology'
                },
                {
                    'title': 'BBC',
                    'xml_url': 'https://feeds.bbci.co.uk/news/rss.xml',
                    'html_url': 'https://www.bbc.com/news',
                    'category_path': 'News'
                }
            ]
        }
    
    @pytest.fixture
    def mock_validation_results(self):
        '''Mock feed validation results'''
        return [
            FeedValidationResult(
                feed_url='https://techcrunch.com/feed/',
                is_valid=True,
                title='TechCrunch',
                description='Latest tech news',
                error_message=None
            ),
            FeedValidationResult(
                feed_url='https://news.ycombinator.com/rss',
                is_valid=True,
                title='Hacker News',
                description='News and discussions',
                error_message=None
            ),
            FeedValidationResult(
                feed_url='https://feeds.bbci.co.uk/news/rss.xml',
                is_valid=False,
                title=None,
                description=None,
                error_message='Connection timeout'
            )
        ]
    
    @pytest.mark.asyncio
    async def test_process_import_success(self, processor, user_id, sample_opml_content, 
                                        sample_import_options, mock_parsed_opml, 
                                        mock_validation_results):
        '''Test successful end-to-end import process'''
        with patch('app.services.opml.import_processor.import_manager') as mock_manager:
            with patch('app.services.opml.import_processor.OPMLParser') as mock_parser:
                with patch('app.services.opml.import_processor.FeedValidator') as mock_validator:
                    with patch('app.services.opml.import_processor.DuplicateDetector') as mock_detector:
                        with patch('app.services.opml.import_processor.Feed') as mock_feed_model:
                            with patch('app.services.opml.import_processor.Category') as mock_category_model:
                                
                                # Setup mocks
                                job_id = 'imp_test123'
                                mock_manager.create_job.return_value = job_id
                                mock_manager.start_job.return_value = True
                                mock_manager.update_progress.return_value = True
                                mock_manager.complete_job.return_value = True
                                
                                # Mock parser
                                parser_instance = Mock()
                                parser_instance.parse.return_value = mock_parsed_opml
                                mock_parser.return_value = parser_instance
                                
                                # Mock validator
                                validator_instance = AsyncMock()
                                validator_instance.validate_batch.return_value = mock_validation_results
                                mock_validator.return_value = validator_instance
                                
                                # Mock duplicate detector
                                detector_instance = Mock()
                                detector_instance.load_existing_data = AsyncMock()
                                detector_instance.detect_feed_duplicates.return_value = []
                                detector_instance.detect_category_duplicates.return_value = []
                                detector_instance.get_unique_feeds.return_value = mock_parsed_opml['feeds']  # All feeds, validation filters them
                                detector_instance.get_unique_categories.return_value = mock_parsed_opml['categories']
                                mock_detector.return_value = detector_instance
                                
                                # Mock database models
                                mock_category_model.create.side_effect = [
                                    Mock(id=1, name='Technology'),
                                    Mock(id=2, name='News')
                                ]
                                mock_feed_model.create.side_effect = [
                                    Mock(id=1, title='TechCrunch'),
                                    Mock(id=2, title='Hacker News')
                                ]
                                
                                # Execute import
                                result = await processor.process_import(
                                    user_id=user_id,
                                    opml_content=sample_opml_content,
                                    filename='subscriptions.opml',
                                    options=sample_import_options
                                )
                                
                                # Verify result
                                assert isinstance(result, ImportProcessorResult)
                                assert result.job_id == job_id
                                assert result.success is True
                                assert result.categories_created == 2
                                # Only valid feeds should be imported (2 valid out of 3 total)
                                assert result.feeds_imported == 2
                                # Validation should filter out invalid feeds (1 invalid)
                                assert result.feeds_failed == 1
                                assert result.duplicates_found == 0
                                assert result.error_message is None
                                
                                # Verify job manager calls
                                mock_manager.create_job.assert_called_once_with(
                                    user_id=user_id,
                                    filename='subscriptions.opml',
                                    file_size=len(sample_opml_content.encode('utf-8')),
                                    duplicate_strategy='skip',
                                    validate_feeds=True,
                                    category_parent_id=None
                                )
                                mock_manager.start_job.assert_called_once()
                                mock_manager.complete_job.assert_called_once()
                                
                                # Verify progress updates were made
                                assert mock_manager.update_progress.call_count >= 4  # At least one per phase
    
    @pytest.mark.asyncio
    async def test_process_import_with_duplicates(self, processor, user_id, sample_opml_content,
                                                sample_import_options, mock_parsed_opml):
        '''Test import with duplicate feeds and categories'''
        with patch('app.services.opml.import_processor.import_manager') as mock_manager:
            with patch('app.services.opml.import_processor.OPMLParser') as mock_parser:
                with patch('app.services.opml.import_processor.FeedValidator') as mock_validator:
                    with patch('app.services.opml.import_processor.DuplicateDetector') as mock_detector:
                        
                        # Setup basic mocks
                        job_id = 'imp_test123'
                        mock_manager.create_job.return_value = job_id
                        mock_manager.start_job.return_value = True
                        mock_manager.update_progress.return_value = True
                        mock_manager.complete_job.return_value = True
                        
                        parser_instance = Mock()
                        parser_instance.parse.return_value = mock_parsed_opml
                        mock_parser.return_value = parser_instance
                        
                        validator_instance = AsyncMock()
                        validator_instance.validate_batch.return_value = []
                        mock_validator.return_value = validator_instance
                        
                        # Mock duplicate detector with duplicates
                        detector_instance = Mock()
                        detector_instance.load_existing_data = AsyncMock()
                        
                        # Create mock duplicates
                        feed_duplicate = FeedDuplicate(
                            opml_feed=mock_parsed_opml['feeds'][0],
                            existing_feed=Mock(id=1, title='Existing TechCrunch'),
                            normalized_url='https://techcrunch.com/feed/',
                            resolution=DuplicateResolution(action='skip', existing_id=1)
                        )
                        
                        category_duplicate = CategoryDuplicate(
                            opml_category=mock_parsed_opml['categories'][0],
                            existing_category=Mock(id=1, name='Technology'),
                            path='Technology',
                            resolution=DuplicateResolution(action='merge', existing_id=1)
                        )
                        
                        detector_instance.detect_feed_duplicates.return_value = [feed_duplicate]
                        detector_instance.detect_category_duplicates.return_value = [category_duplicate]
                        detector_instance.get_unique_feeds.return_value = mock_parsed_opml['feeds'][1:]  # Skip duplicate
                        detector_instance.get_unique_categories.return_value = mock_parsed_opml['categories'][1:]  # Skip duplicate
                        mock_detector.return_value = detector_instance
                        
                        # Execute import
                        result = await processor.process_import(
                            user_id=user_id,
                            opml_content=sample_opml_content,
                            filename='subscriptions.opml',
                            options=sample_import_options
                        )
                        
                        # Verify duplicates were handled
                        assert result.duplicates_found == 2
                        assert result.feeds_imported < len(mock_parsed_opml['feeds'])  # Some were skipped
                        assert result.categories_created < len(mock_parsed_opml['categories'])  # Some were merged
    
    @pytest.mark.asyncio
    async def test_process_import_parsing_error(self, processor, user_id, sample_import_options):
        '''Test import with OPML parsing error'''
        invalid_opml = '<invalid>xml</content>'
        
        with patch('app.services.opml.import_processor.import_manager') as mock_manager:
            with patch('app.services.opml.import_processor.OPMLParser') as mock_parser:
                
                job_id = 'imp_test123'
                mock_manager.create_job.return_value = job_id
                mock_manager.start_job.return_value = True
                mock_manager.fail_job.return_value = True
                
                # Mock parser to raise exception
                parser_instance = Mock()
                parser_instance.parse.side_effect = Exception('Invalid XML format')
                mock_parser.return_value = parser_instance
                
                # Execute import
                result = await processor.process_import(
                    user_id=user_id,
                    opml_content=invalid_opml,
                    filename='invalid.opml',
                    options=sample_import_options
                )
                
                # Verify failure handling
                assert result.success is False
                assert 'OPML parsing failed' in result.error_message
                mock_manager.fail_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_import_validation_disabled(self, processor, user_id, sample_opml_content,
                                                    mock_parsed_opml):
        '''Test import with feed validation disabled'''
        options = {
            'duplicate_strategy': 'skip',
            'validate_feeds': False,  # Validation disabled
            'category_parent_id': None,
            'merge_categories': True,
            'skip_existing_feeds': True
        }
        
        with patch('app.services.opml.import_processor.import_manager') as mock_manager:
            with patch('app.services.opml.import_processor.OPMLParser') as mock_parser:
                with patch('app.services.opml.import_processor.DuplicateDetector') as mock_detector:
                    with patch('app.services.opml.import_processor.Feed') as mock_feed_model:
                        with patch('app.services.opml.import_processor.Category') as mock_category_model:
                            
                            # Setup mocks
                            job_id = 'imp_test123'
                            mock_manager.create_job.return_value = job_id
                            mock_manager.start_job.return_value = True
                            mock_manager.update_progress.return_value = True
                            mock_manager.complete_job.return_value = True
                            
                            parser_instance = Mock()
                            parser_instance.parse.return_value = mock_parsed_opml
                            mock_parser.return_value = parser_instance
                            
                            detector_instance = Mock()
                            detector_instance.load_existing_data = AsyncMock()
                            detector_instance.detect_feed_duplicates.return_value = []
                            detector_instance.detect_category_duplicates.return_value = []
                            detector_instance.get_unique_feeds.return_value = mock_parsed_opml['feeds']
                            detector_instance.get_unique_categories.return_value = mock_parsed_opml['categories']
                            mock_detector.return_value = detector_instance
                            
                            # Mock database models
                            mock_category_model.create.side_effect = [Mock(id=i) for i in range(1, 3)]
                            mock_feed_model.create.side_effect = [Mock(id=i) for i in range(1, 4)]
                            
                            # Execute import
                            result = await processor.process_import(
                                user_id=user_id,
                                opml_content=sample_opml_content,
                                filename='subscriptions.opml',
                                options=options
                            )
                            
                            # Verify all feeds were imported (no validation failures)
                            assert result.feeds_imported == 3
                            assert result.feeds_failed == 0
    
    @pytest.mark.asyncio
    async def test_process_import_job_creation_failure(self, processor, user_id, sample_opml_content,
                                                     sample_import_options):
        '''Test import with job creation failure'''
        with patch('app.services.opml.import_processor.import_manager') as mock_manager:
            
            # Mock job creation failure
            mock_manager.create_job.side_effect = Exception('Database connection failed')
            
            # Execute import and expect exception
            with pytest.raises(ImportProcessorError) as exc_info:
                await processor.process_import(
                    user_id=user_id,
                    opml_content=sample_opml_content,
                    filename='subscriptions.opml',
                    options=sample_import_options
                )
            
            assert 'Failed to create import job' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_process_import_database_error_during_creation(self, processor, user_id, 
                                                               sample_opml_content, sample_import_options,
                                                               mock_parsed_opml):
        '''Test import with database error during feed/category creation'''
        with patch('app.services.opml.import_processor.import_manager') as mock_manager:
            with patch('app.services.opml.import_processor.OPMLParser') as mock_parser:
                with patch('app.services.opml.import_processor.DuplicateDetector') as mock_detector:
                    with patch('app.services.opml.import_processor.Category') as mock_category_model:
                        
                        # Setup mocks
                        job_id = 'imp_test123'
                        mock_manager.create_job.return_value = job_id
                        mock_manager.start_job.return_value = True
                        mock_manager.fail_job.return_value = True
                        
                        parser_instance = Mock()
                        parser_instance.parse.return_value = mock_parsed_opml
                        mock_parser.return_value = parser_instance
                        
                        detector_instance = Mock()
                        detector_instance.load_existing_data = AsyncMock()
                        detector_instance.detect_feed_duplicates.return_value = []
                        detector_instance.detect_category_duplicates.return_value = []
                        detector_instance.get_unique_feeds.return_value = mock_parsed_opml['feeds']
                        detector_instance.get_unique_categories.return_value = mock_parsed_opml['categories']
                        mock_detector.return_value = detector_instance
                        
                        # Mock database error
                        mock_category_model.create.side_effect = Exception('Database constraint violation')
                        
                        # Execute import
                        result = await processor.process_import(
                            user_id=user_id,
                            opml_content=sample_opml_content,
                            filename='subscriptions.opml',
                            options=sample_import_options
                        )
                        
                        # Verify that import completed but with errors
                        # Database errors should be logged but not fail the whole import
                        assert result.success is True  # Import should complete
                        assert result.categories_created == 0  # No categories created due to errors
                        # Database models might fail, but process should continue
                        mock_manager.complete_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_import_cancellation(self, processor, user_id, sample_opml_content,
                                             sample_import_options):
        '''Test import cancellation handling'''
        with patch('app.services.opml.import_processor.import_manager') as mock_manager:
            
            job_id = 'imp_test123'
            mock_manager.create_job.return_value = job_id
            mock_manager.start_job.return_value = True
            mock_manager.cancel_job.return_value = True
            
            # Test that a CancelledError during processing gets handled
            with patch.object(processor.parser, 'parse', side_effect=asyncio.CancelledError('Import was cancelled')):
                # Execute import and expect cancellation
                with pytest.raises(asyncio.CancelledError):
                    await processor.process_import(
                        user_id=user_id,
                        opml_content=sample_opml_content,
                        filename='subscriptions.opml',
                        options=sample_import_options
                    )
    
    def test_calculate_total_steps(self, processor):
        '''Test calculation of total import steps'''
        parsed_data = {
            'categories': [{'name': 'Tech'}, {'name': 'News'}],
            'feeds': [{'title': 'Feed1'}, {'title': 'Feed2'}, {'title': 'Feed3'}]
        }
        
        # With validation
        total_steps = processor._calculate_total_steps(parsed_data, validate_feeds=True)
        expected = 1 + 2 + 3 + 3 + 1  # parsing + categories + validation + feeds + cleanup
        assert total_steps == expected
        
        # Without validation
        total_steps = processor._calculate_total_steps(parsed_data, validate_feeds=False)
        expected = 1 + 2 + 3 + 1  # parsing + categories + feeds + cleanup
        assert total_steps == expected
    
    def test_build_import_results(self, processor):
        '''Test building import results summary'''
        start_time = datetime.now()
        
        results = processor._build_import_results(
            categories_created=5,
            feeds_imported=25,
            feeds_failed=2,
            duplicates_found=3,
            total_feeds=30,
            total_categories=5,
            start_time=start_time
        )
        
        assert isinstance(results, ImportResults)
        assert results.categories_created == 5
        assert results.feeds_imported == 25
        assert results.feeds_failed == 2
        assert results.duplicates_found == 3
        assert results.total_feeds == 30
        assert results.total_categories == 5
        assert results.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_processor_with_large_opml_file(self, processor, user_id, sample_import_options):
        '''Test processor with large OPML file (stress test)'''
        # Generate large OPML content
        large_opml = '''<?xml version="1.0" encoding="UTF-8"?>
        <opml version="1.0">
            <head><title>Large Import</title></head>
            <body>'''
        
        # Add 100 categories with 10 feeds each
        for i in range(100):
            large_opml += f'<outline text="Category{i}">'
            for j in range(10):
                large_opml += f'<outline text="Feed{i}_{j}" xmlUrl="https://example{i}.com/feed{j}.xml"/>'
            large_opml += '</outline>'
        
        large_opml += '</body></opml>'
        
        # Mock a successful but simplified import
        with patch('app.services.opml.import_processor.import_manager') as mock_manager:
            with patch('app.services.opml.import_processor.OPMLParser') as mock_parser:
                
                job_id = 'imp_large123'
                mock_manager.create_job.return_value = job_id
                mock_manager.start_job.return_value = True
                mock_manager.update_progress.return_value = True
                mock_manager.complete_job.return_value = True
                
                # Mock parser to return large dataset
                parser_instance = Mock()
                parser_instance.parse.return_value = {
                    'categories': [{'name': f'Category{i}'} for i in range(100)],
                    'feeds': [{'title': f'Feed{i}_{j}', 'xml_url': f'https://example{i}.com/feed{j}.xml'} 
                             for i in range(100) for j in range(10)]
                }
                mock_parser.return_value = parser_instance
                
                # Execute import
                result = await processor.process_import(
                    user_id=user_id,
                    opml_content=large_opml,
                    filename='large_subscriptions.opml',
                    options=sample_import_options
                )
                
                # Verify the processor can handle large imports
                assert result.job_id == job_id
                # The exact counts depend on mocking, but we verify no crashes
                assert isinstance(result.categories_created, int)
                assert isinstance(result.feeds_imported, int)