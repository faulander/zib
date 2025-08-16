#!/usr/bin/env python3
'''
Real-world OPML import test using Inoreader export
Tests the complete OPML import functionality with actual data
'''

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.opml import (
    import_processor,
    import_manager,
    OPMLParser,
    FeedValidator,
    DuplicateDetector,
    ImportStatus,
    ImportPhase
)
from loguru import logger


async def test_inoreader_import():
    '''Test importing the real Inoreader OPML file'''
    
    print("🚀 Testing OPML Import with Real Inoreader File")
    print("=" * 60)
    
    # Path to the OPML file
    opml_file_path = '/Users/haraldfauland/Projects/zib/Inoreader Feeds 20250814.xml'
    
    if not os.path.exists(opml_file_path):
        print(f"❌ OPML file not found: {opml_file_path}")
        return False
    
    try:
        # Read the OPML file
        with open(opml_file_path, 'r', encoding='utf-8') as f:
            opml_content = f.read()
        
        file_size = len(opml_content.encode('utf-8'))
        print(f"📁 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"📄 Content length: {len(opml_content):,} characters")
        
        # Step 1: Test OPML Parser
        print("\n🔍 Step 1: Testing OPML Parser")
        print("-" * 30)
        
        parser = OPMLParser()
        parsed_data = parser.parse(opml_content)
        
        print(f"✅ Parsed successfully!")
        print(f"   📂 Categories found: {len(parsed_data['categories'])}")
        print(f"   📰 Feeds found: {len(parsed_data['feeds'])}")
        
        # Show category breakdown
        print("\n📂 Categories:")
        for i, category in enumerate(parsed_data['categories'][:10], 1):  # Show first 10
            print(f"   {i:2}. {category['name']}")
        if len(parsed_data['categories']) > 10:
            print(f"   ... and {len(parsed_data['categories']) - 10} more")
        
        # Show some feeds
        print("\n📰 Sample Feeds:")
        for i, feed in enumerate(parsed_data['feeds'][:5], 1):  # Show first 5
            print(f"   {i}. {feed['title']}")
            print(f"      URL: {feed['xml_url']}")
            print(f"      Category: {feed.get('category_path', 'None')}")
        if len(parsed_data['feeds']) > 5:
            print(f"   ... and {len(parsed_data['feeds']) - 5} more feeds")
        
        # Step 2: Test Feed Validation (sample)
        print("\n🔗 Step 2: Testing Feed Validation (Sample)")
        print("-" * 40)
        
        validator = FeedValidator()
        
        # Test validate just first 3 feeds for speed
        sample_feeds = parsed_data['feeds'][:3]
        sample_urls = [feed['xml_url'] for feed in sample_feeds]
        
        print(f"Validating {len(sample_urls)} sample feeds...")
        validation_results = await validator.validate_batch(sample_urls)
        
        for result in validation_results:
            status = "✅ Valid" if result.is_valid else "❌ Invalid"
            print(f"   {status}: {result.feed_url}")
            if not result.is_valid:
                print(f"      Error: {result.error_message}")
        
        # Step 3: Test Duplicate Detection
        print("\n🔍 Step 3: Testing Duplicate Detection")
        print("-" * 35)
        
        detector = DuplicateDetector(
            user_id=1,
            merge_categories=True,
            skip_existing_feeds=True
        )
        
        # Load existing data (will be empty in clean database)
        await detector.load_existing_data()
        
        # Detect duplicates
        feed_duplicates = detector.detect_feed_duplicates(parsed_data['feeds'])
        category_duplicates = detector.detect_category_duplicates(parsed_data['categories'])
        
        print(f"   🔗 Feed duplicates found: {len(feed_duplicates)}")
        print(f"   📂 Category duplicates found: {len(category_duplicates)}")
        
        # Get unique items
        unique_feeds = detector.get_unique_feeds(parsed_data['feeds'], feed_duplicates)
        unique_categories = detector.get_unique_categories(parsed_data['categories'], category_duplicates)
        
        print(f"   📰 Unique feeds to import: {len(unique_feeds)}")
        print(f"   📂 Unique categories to import: {len(unique_categories)}")
        
        # Step 4: Test Full Import Process
        print("\n🚀 Step 4: Testing Full Import Process")
        print("-" * 35)
        
        # Import options
        options = {
            'duplicate_strategy': 'skip',
            'validate_feeds': False,  # Skip validation for speed in test
            'merge_categories': True,
            'category_parent_id': None
        }
        
        print("Starting import process...")
        print(f"Options: {options}")
        
        # Start the import
        result = await import_processor.process_import(
            user_id=1,
            opml_content=opml_content,
            filename='Inoreader Feeds 20250814.xml',
            options=options
        )
        
        # Display results
        print(f"\n📊 Import Results:")
        print(f"   🆔 Job ID: {result.job_id}")
        print(f"   ✅ Success: {result.success}")
        print(f"   📂 Categories created: {result.categories_created}")
        print(f"   📰 Feeds imported: {result.feeds_imported}")
        print(f"   ❌ Feeds failed: {result.feeds_failed}")
        print(f"   🔄 Duplicates found: {result.duplicates_found}")
        print(f"   ⏱️  Processing time: {result.total_processing_time:.2f} seconds")
        
        if result.error_message:
            print(f"   ⚠️  Error: {result.error_message}")
        
        # Step 5: Check Job Status
        print("\n📋 Step 5: Checking Job Status")
        print("-" * 30)
        
        job = import_manager.get_job(result.job_id)
        if job:
            print(f"   📋 Job Status: {job.status}")
            print(f"   📊 Progress: {job.current_step}/{job.total_steps}")
            if job.current_phase:
                print(f"   🔄 Current Phase: {job.current_phase}")
            print(f"   📅 Created: {job.created_at}")
            if job.completed_at:
                print(f"   ✅ Completed: {job.completed_at}")
        
        # Final Summary
        print("\n" + "=" * 60)
        print("🎉 OPML Import Test Complete!")
        print("=" * 60)
        
        if result.success:
            print("✅ All tests passed successfully!")
            print(f"✅ Imported {result.feeds_imported} feeds into {result.categories_created} categories")
        else:
            print("❌ Import failed!")
            print(f"❌ Error: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        logger.exception("OPML import test failed")
        return False


async def main():
    '''Main test function'''
    print("🧪 Real-world OPML Import Test")
    print("Testing with Inoreader export file\n")
    
    success = await test_inoreader_import()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print("\n💥 Tests failed!")
        return 1


if __name__ == '__main__':
    # Run the test
    exit_code = asyncio.run(main())
    sys.exit(exit_code)