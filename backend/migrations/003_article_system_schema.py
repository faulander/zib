'''
Article System Schema Migration
Creates articles, users, user_subscriptions, and read_statuses tables
'''

from app.core.migrations import Migration
from app.core.database import db
from app.models.article import ARTICLE_MODELS


class ArticleSystemSchemaMigration(Migration):
    '''Article system schema migration'''
    
    def up(self):
        '''Create article system tables and indexes'''
        
        # Create all article system tables
        db.create_tables(ARTICLE_MODELS)
        
        # Create additional performance indexes for articles
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_articles_feed_published 
            ON articles(feed_id, published_date DESC);
        ''')
        
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_articles_published_created 
            ON articles(published_date DESC, created_at DESC);
        ''')
        
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_articles_feed_created 
            ON articles(feed_id, created_at DESC);
        ''')
        
        # Performance indexes for user subscriptions
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active 
            ON user_subscriptions(user_id, is_active);
        ''')
        
        # Performance indexes for read statuses - optimized for common queries
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_read_statuses_user_unread 
            ON read_statuses(user_id, is_read, is_archived) 
            WHERE is_read = false AND is_archived = false;
        ''')
        
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_read_statuses_user_starred 
            ON read_statuses(user_id, is_starred) 
            WHERE is_starred = true;
        ''')
        
        db.execute_sql('''
            CREATE INDEX IF NOT EXISTS idx_read_statuses_article_stats 
            ON read_statuses(article_id, is_read);
        ''')
        
        # Create triggers for automatic timestamp updates
        db.execute_sql('''
            CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
            AFTER UPDATE ON users
            FOR EACH ROW
            BEGIN
                UPDATE users 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
        ''')
        
        db.execute_sql('''
            CREATE TRIGGER IF NOT EXISTS update_articles_timestamp 
            AFTER UPDATE ON articles
            FOR EACH ROW
            BEGIN
                UPDATE articles 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
        ''')
        
        db.execute_sql('''
            CREATE TRIGGER IF NOT EXISTS update_user_subscriptions_timestamp 
            AFTER UPDATE ON user_subscriptions
            FOR EACH ROW
            BEGIN
                UPDATE user_subscriptions 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
        ''')
        
        db.execute_sql('''
            CREATE TRIGGER IF NOT EXISTS update_read_statuses_timestamp 
            AFTER UPDATE ON read_statuses
            FOR EACH ROW
            BEGIN
                UPDATE read_statuses 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
        ''')
        
        # Create a view for article statistics
        db.execute_sql('''
            CREATE VIEW IF NOT EXISTS article_stats AS
            SELECT 
                a.id,
                a.feed_id,
                a.title,
                a.url,
                a.published_date,
                a.created_at,
                COUNT(rs.id) as total_readers,
                COUNT(CASE WHEN rs.is_read = true THEN 1 END) as read_count,
                COUNT(CASE WHEN rs.is_starred = true THEN 1 END) as starred_count
            FROM articles a
            LEFT JOIN read_statuses rs ON a.id = rs.article_id
            GROUP BY a.id, a.feed_id, a.title, a.url, a.published_date, a.created_at;
        ''')
        
        # Create a view for user reading statistics
        db.execute_sql('''
            CREATE VIEW IF NOT EXISTS user_reading_stats AS
            SELECT 
                u.id as user_id,
                u.username,
                COUNT(rs.id) as total_articles,
                COUNT(CASE WHEN rs.is_read = true THEN 1 END) as read_articles,
                COUNT(CASE WHEN rs.is_starred = true THEN 1 END) as starred_articles,
                COUNT(us.id) as subscribed_feeds
            FROM users u
            LEFT JOIN read_statuses rs ON u.id = rs.user_id
            LEFT JOIN user_subscriptions us ON u.id = us.user_id AND us.is_active = true
            GROUP BY u.id, u.username;
        ''')
    
    def down(self):
        '''Remove article system tables and related objects'''
        
        # Drop views first
        db.execute_sql('DROP VIEW IF EXISTS user_reading_stats;')
        db.execute_sql('DROP VIEW IF EXISTS article_stats;')
        
        # Drop triggers
        db.execute_sql('DROP TRIGGER IF EXISTS update_read_statuses_timestamp;')
        db.execute_sql('DROP TRIGGER IF EXISTS update_user_subscriptions_timestamp;')
        db.execute_sql('DROP TRIGGER IF EXISTS update_articles_timestamp;')
        db.execute_sql('DROP TRIGGER IF EXISTS update_users_timestamp;')
        
        # Drop custom indexes
        db.execute_sql('DROP INDEX IF EXISTS idx_read_statuses_article_stats;')
        db.execute_sql('DROP INDEX IF EXISTS idx_read_statuses_user_starred;')
        db.execute_sql('DROP INDEX IF EXISTS idx_read_statuses_user_unread;')
        db.execute_sql('DROP INDEX IF EXISTS idx_user_subscriptions_active;')
        db.execute_sql('DROP INDEX IF EXISTS idx_articles_feed_created;')
        db.execute_sql('DROP INDEX IF EXISTS idx_articles_published_created;')
        db.execute_sql('DROP INDEX IF EXISTS idx_articles_feed_published;')
        
        # Drop tables in reverse order to handle foreign keys
        db.drop_tables(ARTICLE_MODELS[::-1])


# Migration instance
migration = ArticleSystemSchemaMigration(
    version=3,
    description='Article system with users, articles, subscriptions, and read status'
)