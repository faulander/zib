import pytest
from peewee import SqliteDatabase
from app.core.database import db, BaseModel
from app.models.base import ALL_MODELS


@pytest.fixture(autouse=True)
def setup_test_database():
    """Set up test database for each test"""
    # Use in-memory SQLite database for tests
    test_db = SqliteDatabase(':memory:')
    
    # Store original database
    original_db = db
    
    # Replace the database in models
    BaseModel._meta.database = test_db
    
    # Update the global db reference for models that import it
    import app.core.database
    app.core.database.db = test_db
    
    # Connect to test database
    test_db.connect()
    
    # Create tables
    test_db.create_tables(ALL_MODELS)
    
    yield
    
    # Cleanup after test
    test_db.drop_tables(ALL_MODELS)
    test_db.close()
    
    # Restore original database
    BaseModel._meta.database = original_db
    app.core.database.db = original_db


@pytest.fixture
def sample_category():
    """Create a sample category for testing"""
    from app.models.base import Category
    return Category.create(name="Test Category")


@pytest.fixture
def sample_feed(sample_category):
    """Create a sample feed for testing"""
    from app.models.base import Feed
    return Feed.create(
        url="https://example.com/feed.xml",
        title="Test Feed",
        category=sample_category
    )