'''Main OPML import processor that coordinates all import components'''

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

from .parser import OPMLParser
from .validator import FeedValidator
from .duplicate_detector import DuplicateDetector
from .import_manager import import_manager, ImportStatus, ImportPhase, ImportResults
from app.models.base import Feed, Category
from app.core.database import db


class ImportProcessorError(Exception):
    '''Exception raised for import processor errors'''
    pass


@dataclass
class ImportProcessorResult:
    '''Result of an import processing operation'''
    job_id: str
    success: bool
    categories_created: int
    feeds_imported: int
    feeds_failed: int
    duplicates_found: int
    total_processing_time: float
    error_message: Optional[str] = None


class ImportProcessor:
    '''Main processor for OPML import operations'''
    
    def __init__(self):
        '''Initialize import processor'''
        self.parser = OPMLParser()
        self.validator = FeedValidator()
    
    async def process_import(self, user_id: int, opml_content: str, filename: str,
                           options: Dict[str, Any]) -> ImportProcessorResult:
        '''
        Process a complete OPML import operation
        
        Args:
            user_id: ID of the user importing OPML
            opml_content: Raw OPML content string
            filename: Name of the OPML file
            options: Import options dictionary containing:
                - duplicate_strategy: How to handle duplicates
                - validate_feeds: Whether to validate feed URLs
                - category_parent_id: Optional parent category
                - merge_categories: Whether to merge duplicate categories
                - skip_existing_feeds: Whether to skip existing feeds
                
        Returns:
            ImportProcessorResult with operation details
        '''
        start_time = datetime.now()
        job_id = None
        
        try:
            # Calculate file size
            file_size = len(opml_content.encode('utf-8'))
            
            # Create import job
            try:
                job_id = import_manager.create_job(
                    user_id=user_id,
                    filename=filename,
                    file_size=file_size,
                    duplicate_strategy=options.get('duplicate_strategy', 'skip'),
                    validate_feeds=options.get('validate_feeds', True),
                    category_parent_id=options.get('category_parent_id')
                )
                logger.info(f'Created import job {job_id} for user {user_id}')
            except Exception as e:
                raise ImportProcessorError(f'Failed to create import job: {str(e)}')
            
            # Phase 1: Parse OPML content
            logger.info(f'Job {job_id}: Starting OPML parsing')
            import_manager.update_progress(job_id, 0, ImportPhase.PARSING, 'Parsing OPML content')
            
            try:
                parsed_data = self.parser.parse(opml_content)
                logger.info(f'Job {job_id}: Parsed {len(parsed_data["feeds"])} feeds and '
                           f'{len(parsed_data["categories"])} categories')
            except Exception as e:
                error_msg = f'OPML parsing failed: {str(e)}'
                import_manager.fail_job(job_id, error_msg, str(e))
                return ImportProcessorResult(
                    job_id=job_id,
                    success=False,
                    categories_created=0,
                    feeds_imported=0,
                    feeds_failed=0,
                    duplicates_found=0,
                    total_processing_time=(datetime.now() - start_time).total_seconds(),
                    error_message=error_msg
                )
            
            # Calculate total steps and start job
            total_steps = self._calculate_total_steps(parsed_data, options.get('validate_feeds', True))
            import_manager.start_job(job_id, total_steps)
            current_step = 1
            
            # Phase 2: Load existing data and detect duplicates
            logger.info(f'Job {job_id}: Loading existing data and detecting duplicates')
            import_manager.update_progress(job_id, current_step, ImportPhase.PARSING, 
                                         'Loading existing data')
            
            try:
                # Initialize duplicate detector
                duplicate_detector = DuplicateDetector(
                    user_id=user_id,
                    merge_categories=options.get('merge_categories', True),
                    skip_existing_feeds=options.get('skip_existing_feeds', True)
                )
                
                await duplicate_detector.load_existing_data()
                current_step += 1
                
                # Detect duplicates
                feed_duplicates = duplicate_detector.detect_feed_duplicates(parsed_data['feeds'])
                category_duplicates = duplicate_detector.detect_category_duplicates(parsed_data['categories'])
                
                duplicates_found = len(feed_duplicates) + len(category_duplicates)
                logger.info(f'Job {job_id}: Found {len(feed_duplicates)} feed duplicates and '
                           f'{len(category_duplicates)} category duplicates')
                
                # Get unique items to process
                unique_feeds = duplicate_detector.get_unique_feeds(parsed_data['feeds'], feed_duplicates)
                unique_categories = duplicate_detector.get_unique_categories(parsed_data['categories'], category_duplicates)
                
            except Exception as e:
                error_msg = f'Duplicate detection failed: {str(e)}'
                import_manager.fail_job(job_id, error_msg, str(e))
                return ImportProcessorResult(
                    job_id=job_id,
                    success=False,
                    categories_created=0,
                    feeds_imported=0,
                    feeds_failed=0,
                    duplicates_found=0,
                    total_processing_time=(datetime.now() - start_time).total_seconds(),
                    error_message=error_msg
                )
            
            # Phase 3: Validate feeds (if enabled)
            feeds_failed = 0
            valid_feeds = unique_feeds
            
            if options.get('validate_feeds', True):
                logger.info(f'Job {job_id}: Validating {len(unique_feeds)} feeds')
                import_manager.update_progress(job_id, current_step, ImportPhase.VALIDATING_FEEDS,
                                             f'Validating {len(unique_feeds)} feeds')
                
                try:
                    # Extract URLs for validation
                    feed_urls = [feed.get('xml_url') for feed in unique_feeds if feed.get('xml_url')]
                    
                    if feed_urls:
                        validation_results = await self.validator.validate_batch(feed_urls)
                        
                        # Filter out invalid feeds
                        valid_urls = {result.feed_url for result in validation_results if result.is_valid}
                        valid_feeds = [feed for feed in unique_feeds 
                                     if feed.get('xml_url') in valid_urls]
                        feeds_failed = len(unique_feeds) - len(valid_feeds)
                        
                        logger.info(f'Job {job_id}: {len(valid_feeds)} feeds validated successfully, '
                                   f'{feeds_failed} failed validation')
                    
                    current_step += len(unique_feeds)
                    
                except Exception as e:
                    logger.warning(f'Job {job_id}: Feed validation failed: {e}')
                    # Continue with unvalidated feeds
                    feeds_failed = 0
                    current_step += len(unique_feeds)
            
            # Phase 4: Create categories
            logger.info(f'Job {job_id}: Creating {len(unique_categories)} categories')
            import_manager.update_progress(job_id, current_step, ImportPhase.CREATING_CATEGORIES,
                                         f'Creating {len(unique_categories)} categories')
            
            categories_created = 0
            category_mapping = {}  # Map category paths to IDs
            
            try:
                # Sort categories by depth (parents first)
                sorted_categories = sorted(unique_categories, 
                                         key=lambda c: len(c.get('parent_path', '').split('/')) if c.get('parent_path') else 0)
                
                for category in sorted_categories:
                    try:
                        # For now, create simple categories (current model doesn't support hierarchy)
                        category_obj = Category.create(
                            name=category['name'],
                            description=category.get('description', '')
                        )
                        
                        category_mapping[category.get('full_path', category['name'])] = category_obj.id
                        categories_created += 1
                        current_step += 1
                        
                        if current_step % 10 == 0:  # Update progress every 10 items
                            import_manager.update_progress(job_id, current_step, ImportPhase.CREATING_CATEGORIES,
                                                         f'Created {categories_created} categories')
                        
                    except Exception as e:
                        logger.warning(f'Job {job_id}: Failed to create category {category["name"]}: {e}')
                        continue
                
                logger.info(f'Job {job_id}: Created {categories_created} categories')
                
            except Exception as e:
                error_msg = f'Category creation failed: {str(e)}'
                import_manager.fail_job(job_id, error_msg, str(e))
                return ImportProcessorResult(
                    job_id=job_id,
                    success=False,
                    categories_created=categories_created,
                    feeds_imported=0,
                    feeds_failed=feeds_failed,
                    duplicates_found=duplicates_found,
                    total_processing_time=(datetime.now() - start_time).total_seconds(),
                    error_message=error_msg
                )
            
            # Phase 5: Create feeds
            logger.info(f'Job {job_id}: Creating {len(valid_feeds)} feeds')
            import_manager.update_progress(job_id, current_step, ImportPhase.IMPORTING_FEEDS,
                                         f'Creating {len(valid_feeds)} feeds')
            
            feeds_imported = 0
            
            try:
                for feed in valid_feeds:
                    try:
                        # Find category ID
                        category_id = None
                        category_path = feed.get('category_path')
                        if category_path and category_path in category_mapping:
                            category_id = category_mapping[category_path]
                        
                        # Create feed
                        feed_obj = Feed.create(
                            title=feed.get('title', 'Untitled Feed'),
                            url=feed.get('xml_url'),
                            site_url=feed.get('html_url'),
                            description=feed.get('description', ''),
                            category_id=category_id
                        )
                        
                        feeds_imported += 1
                        current_step += 1
                        
                        if current_step % 10 == 0:  # Update progress every 10 items
                            import_manager.update_progress(job_id, current_step, ImportPhase.IMPORTING_FEEDS,
                                                         f'Imported {feeds_imported} feeds')
                        
                    except Exception as e:
                        logger.warning(f'Job {job_id}: Failed to create feed {feed.get("title", "Unknown")}: {e}')
                        feeds_failed += 1
                        continue
                
                logger.info(f'Job {job_id}: Imported {feeds_imported} feeds')
                
            except Exception as e:
                error_msg = f'Feed creation failed: {str(e)}'
                import_manager.fail_job(job_id, error_msg, str(e))
                return ImportProcessorResult(
                    job_id=job_id,
                    success=False,
                    categories_created=categories_created,
                    feeds_imported=feeds_imported,
                    feeds_failed=feeds_failed,
                    duplicates_found=duplicates_found,
                    total_processing_time=(datetime.now() - start_time).total_seconds(),
                    error_message=error_msg
                )
            
            # Phase 6: Cleanup and complete
            logger.info(f'Job {job_id}: Completing import')
            import_manager.update_progress(job_id, current_step, ImportPhase.CLEANUP, 'Finalizing import')
            
            # Build results
            results = self._build_import_results(
                categories_created=categories_created,
                feeds_imported=feeds_imported,
                feeds_failed=feeds_failed,
                duplicates_found=duplicates_found,
                total_feeds=len(parsed_data['feeds']),
                total_categories=len(parsed_data['categories']),
                start_time=start_time
            )
            
            # Complete job
            import_manager.complete_job(job_id, results)
            
            logger.info(f'Job {job_id}: Import completed successfully - '
                       f'{feeds_imported} feeds, {categories_created} categories, '
                       f'{duplicates_found} duplicates found')
            
            return ImportProcessorResult(
                job_id=job_id,
                success=True,
                categories_created=categories_created,
                feeds_imported=feeds_imported,
                feeds_failed=feeds_failed,
                duplicates_found=duplicates_found,
                total_processing_time=(datetime.now() - start_time).total_seconds()
            )
            
        except ImportProcessorError:
            # Re-raise ImportProcessorError to let it bubble up
            raise
        except asyncio.CancelledError:
            # Re-raise CancelledError to let it bubble up
            raise
        except Exception as e:
            error_msg = f'Import processing failed: {str(e)}'
            logger.error(f'Job {job_id}: {error_msg}', exc_info=True)
            
            if job_id:
                import_manager.fail_job(job_id, error_msg, str(e))
            
            return ImportProcessorResult(
                job_id=job_id or 'unknown',
                success=False,
                categories_created=0,
                feeds_imported=0,
                feeds_failed=0,
                duplicates_found=0,
                total_processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=error_msg
            )
    
    def _calculate_total_steps(self, parsed_data: Dict[str, Any], validate_feeds: bool) -> int:
        '''
        Calculate total number of steps for progress tracking
        
        Args:
            parsed_data: Parsed OPML data
            validate_feeds: Whether feed validation is enabled
            
        Returns:
            Total number of steps
        '''
        num_categories = len(parsed_data.get('categories', []))
        num_feeds = len(parsed_data.get('feeds', []))
        
        steps = 1  # Parsing
        steps += num_categories  # Category creation
        
        if validate_feeds:
            steps += num_feeds  # Feed validation
        
        steps += num_feeds  # Feed creation
        steps += 1  # Cleanup
        
        return steps
    
    def _build_import_results(self, categories_created: int, feeds_imported: int,
                            feeds_failed: int, duplicates_found: int,
                            total_feeds: int, total_categories: int,
                            start_time: datetime) -> ImportResults:
        '''
        Build ImportResults object for job completion
        
        Args:
            categories_created: Number of categories created
            feeds_imported: Number of feeds imported
            feeds_failed: Number of feeds that failed
            duplicates_found: Number of duplicates found
            total_feeds: Total feeds in OPML
            total_categories: Total categories in OPML
            start_time: Import start time
            
        Returns:
            ImportResults object
        '''
        duration = (datetime.now() - start_time).total_seconds()
        
        return ImportResults(
            categories_created=categories_created,
            feeds_imported=feeds_imported,
            feeds_failed=feeds_failed,
            duplicates_found=duplicates_found,
            total_feeds=total_feeds,
            total_categories=total_categories,
            duration_seconds=duration
        )


# Global import processor instance
import_processor = ImportProcessor()