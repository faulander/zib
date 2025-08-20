from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, Union


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
    database_url: str = 'sqlite:///data/zib.db'
    database_echo: bool = False
    
    # CORS Settings
    cors_origins: Union[list[str], str] = [
        'http://localhost:5173', 'http://127.0.0.1:5173',
        'http://localhost:5174', 'http://127.0.0.1:5174'
    ]
    cors_methods: list[str] = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    cors_headers: list[str] = ['*']
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Split comma-separated string into list
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
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
        extra = 'ignore'  # Ignore extra fields from environment


# Global settings instance
settings = Settings()