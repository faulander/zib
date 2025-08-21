import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict

from app.models.article import User
from app.models.base import Feed
from app.core.database import db

logger = logging.getLogger(__name__)


class AutoRefreshService:
    '''Service for automatically refreshing feeds based on user preferences'''
    
    def __init__(self):
        self.refresh_tasks: Dict[int, asyncio.Task] = {}  # user_id -> task
        self.running = False
    
    async def start(self):
        '''Start the auto-refresh service'''
        if self.running:
            return
        
        self.running = True
        logger.info('Auto-refresh service started')
        
        # Start refresh tasks for all users with auto-refresh enabled
        await self._start_user_refresh_tasks()
    
    async def stop(self):
        '''Stop the auto-refresh service'''
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all running tasks
        for task in self.refresh_tasks.values():
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        if self.refresh_tasks:
            await asyncio.gather(*self.refresh_tasks.values(), return_exceptions=True)
        
        self.refresh_tasks.clear()
        logger.info('Auto-refresh service stopped')
    
    async def _start_user_refresh_tasks(self):
        '''Start refresh tasks for all users with auto-refresh enabled'''
        try:
            users = list(User.select().where(User.auto_refresh_feeds == True))
            logger.info(f'Found {len(users)} users with auto-refresh enabled')
            
            for user in users:
                await self._start_user_refresh_task(user)
                
        except Exception as e:
            logger.error(f'Failed to start user refresh tasks: {e}')
            import traceback
            logger.error(traceback.format_exc())
    
    async def _start_user_refresh_task(self, user: User):
        '''Start refresh task for a specific user'''
        if user.id in self.refresh_tasks:
            # Cancel existing task
            self.refresh_tasks[user.id].cancel()
        
        # Create new task
        task = asyncio.create_task(self._user_refresh_loop(user))
        self.refresh_tasks[user.id] = task
        
        logger.info(f'Started auto-refresh for user {user.username} (interval: {user.auto_refresh_interval_minutes} minutes)')
    
    async def _user_refresh_loop(self, user: User):
        '''Main refresh loop for a user'''
        try:
            user_id = user.id
            logger.info(f'Starting refresh loop for user {user.username} (ID: {user_id})')
            
            while self.running:
                # Refresh user object to get latest settings
                try:
                    current_user = User.get_by_id(user_id)
                    if not current_user.auto_refresh_feeds:
                        logger.info(f'Auto-refresh disabled for user {current_user.username}, stopping task')
                        break
                except Exception as e:
                    logger.error(f'Failed to refresh user settings: {e}')
                    current_user = user  # Fallback to original user object
                
                # Do the refresh first, then sleep
                await self._refresh_user_feeds(current_user)
                
                if not self.running:
                    break
                
                # Wait for the refresh interval using current settings
                sleep_seconds = current_user.auto_refresh_interval_minutes * 60
                logger.info(f'Next refresh for user {current_user.username} in {current_user.auto_refresh_interval_minutes} minutes')
                await asyncio.sleep(sleep_seconds)
                
        except asyncio.CancelledError:
            logger.info(f'Auto-refresh cancelled for user {user.username}')
        except Exception as e:
            logger.error(f'Error in auto-refresh loop for user {user.username}: {e}')
    
    async def _refresh_user_feeds(self, user: User):
        '''Refresh all feeds for a user'''
        try:
            logger.info(f'Auto-refreshing feeds for user {user.username}')
            
            # Ensure database connection is active
            from app.core.database import db
            if db.is_closed():
                logger.info('Database connection closed, reconnecting...')
                db.connect()
            
            # Import feed_fetcher here to avoid circular imports
            from app.services.feed_fetcher import feed_fetcher
            
            # Get all active feeds
            feeds = list(Feed.select().where(Feed.is_active == True))
            
            if not feeds:
                logger.info(f'No active feeds to refresh for user {user.username}')
                return
            
            # Use the existing feed_fetcher service
            results = await feed_fetcher.update_multiple_feeds(feeds, force=True, max_concurrent=3)
            
            # Calculate summary
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            total_articles_added = sum(r.articles_added for r in results if r.success)
            
            logger.info(f'Auto-refresh completed for user {user.username}: {successful}/{len(feeds)} feeds refreshed, {total_articles_added} new articles')
            
        except Exception as e:
            logger.error(f'Failed to refresh feeds for user {user.username}: {e}')
            import traceback
            logger.error(traceback.format_exc())
    
    async def update_user_settings(self, user: User):
        '''Update refresh task when user settings change'''
        if user.auto_refresh_feeds:
            await self._start_user_refresh_task(user)
        else:
            # Stop refresh task for this user
            if user.id in self.refresh_tasks:
                self.refresh_tasks[user.id].cancel()
                del self.refresh_tasks[user.id]
                logger.info(f'Stopped auto-refresh for user {user.username}')


# Global auto-refresh service instance
auto_refresh_service = AutoRefreshService()