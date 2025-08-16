import sys
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
from typing import Optional

from .config import settings


def setup_logging(
    level: str = None,
    format_type: str = None,
    log_file: Optional[str] = None
) -> None:
    '''Configure loguru logging with rich console output'''
    
    # Use settings if parameters not provided
    level = level or settings.log_level
    format_type = format_type or settings.log_format
    log_file = log_file or settings.log_file
    
    # Remove default logger
    logger.remove()
    
    # Console logging with rich
    if format_type == 'rich':
        console = Console()
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True
        )
        
        logger.add(
            rich_handler,
            level=level,
            format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}',
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    else:
        # Standard console logging
        logger.add(
            sys.stdout,
            level=level,
            format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>',
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # File logging if specified
    if log_file:
        logger.add(
            log_file,
            level=level,
            format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}',
            rotation='10 MB',
            retention='1 week',
            compression='gz',
            backtrace=True,
            diagnose=True
        )
    
    # Log startup message
    logger.info(f'Logging configured with level: {level}, format: {format_type}')
    if log_file:
        logger.info(f'File logging enabled: {log_file}')


def get_logger(name: str = None):
    '''Get a logger instance for a specific module'''
    return logger.bind(name=name) if name else logger