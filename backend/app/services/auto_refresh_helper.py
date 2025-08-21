"""Helper functions for auto-refresh service initialization"""
import logging
from datetime import datetime
from app.models.article import User

logger = logging.getLogger(__name__)

def ensure_default_user():
    """Ensure a default user exists for single-user RSS reader"""
    try:
        # Check if any users exist
        user_count = User.select().count()
        
        if user_count == 0:
            logger.info("No users found, creating default user for auto-refresh")
            
            # Create a default user for the single-user RSS reader
            default_user = User.create(
                username="default",
                email="user@localhost",
                password_hash="not_used",  # Auth not implemented yet
                is_active=True,
                auto_refresh_feeds=True,  # Enable auto-refresh by default
                auto_refresh_interval_minutes=30,  # Default 30 minutes, user can change in UI
                show_unread_count_in_title=True,
                default_view='unread',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.info(f"Created default user with auto-refresh enabled (interval: {default_user.auto_refresh_interval_minutes} minutes)")
            return default_user
        else:
            # Get the first user (single-user system)
            user = User.select().first()
            
            # Log current auto-refresh status
            logger.info(f"Found existing user {user.username} - auto_refresh: {user.auto_refresh_feeds}, interval: {user.auto_refresh_interval_minutes} minutes")
            
            # Don't override user's settings from UI
            # Just log the current state
            if user.auto_refresh_feeds:
                logger.info(f"Auto-refresh is enabled with {user.auto_refresh_interval_minutes} minute interval")
            else:
                logger.info("Auto-refresh is disabled by user preference")
            
            return user
            
    except Exception as e:
        logger.error(f"Failed to ensure default user: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None