from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    '''Application settings and configuration'''
    
    # App Settings
    app_name: str = 'Zib RSS Reader'
    app_version: str = '0.1.0'
    debug: bool = False
    
    # Server Settings
    host: str = '0.0.0.0'
    port: int = 8000
    reload: bool = False
    
    # Database Settings
    database_url: str = 'sqlite:///zib.db'
    database_echo: bool = False
    
    # CORS Settings
    cors_origins: list[str] = ['http://localhost:5173', 'http://127.0.0.1:5173']
    cors_methods: list[str] = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    cors_headers: list[str] = ['*']
    
    # Logging Settings
    log_level: str = 'INFO'
    log_format: str = 'rich'
    log_file: Optional[str] = None
    
    # Feed Settings
    default_feed_update_interval: int = 3600  # 1 hour in seconds
    max_feeds_per_user: int = 1000
    feed_timeout: int = 30  # seconds
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


# Global settings instance
settings = Settings()