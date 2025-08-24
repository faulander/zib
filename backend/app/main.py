from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import time
from contextlib import asynccontextmanager

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .core.exceptions import (
    ZibException, validation_exception_handler, zib_exception_handler,
    http_exception_handler, general_exception_handler
)
from .routes import feeds_router, categories_router, opml_router, articles_router, filters_router, settings_router
from .services.health_service import HealthService
from .services.auto_refresh_service import auto_refresh_service

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''Application lifespan events'''
    # Startup
    logger.info(f'Starting {settings.app_name} v{settings.app_version}')
    logger.info(f'Debug mode: {settings.debug}')
    logger.info(f'Database URL: {settings.database_url}')
    
    # Ensure database directory exists and log environment
    from .core.database import log_database_environment, ensure_database_directory
    logger.info('Checking database environment...')
    log_database_environment()
    ensure_database_directory()
    
    # Initialize database and run migrations
    try:
        logger.info('Initializing database...')
        from .core.database import init_database
        init_database()
        logger.info('Database initialized successfully')
    except Exception as e:
        logger.error(f'Failed to initialize database: {e}')
        raise
    
    # Ensure default user exists for auto-refresh
    try:
        from app.services.auto_refresh_helper import ensure_default_user
        ensure_default_user()
    except Exception as e:
        logger.error(f'Failed to ensure default user: {e}')
    
    # Start auto-refresh service
    try:
        logger.info('Starting auto-refresh service...')
        await auto_refresh_service.start()
        logger.info(f'Auto-refresh service started. Running: {auto_refresh_service.running}, Tasks: {len(auto_refresh_service.refresh_tasks)}')
    except Exception as e:
        logger.error(f'Failed to start auto-refresh service: {e}')
    
    yield
    
    # Shutdown
    logger.info('Shutting down application')
    await auto_refresh_service.stop()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    root_path="",  # Set if API is served under a path
    description='''
## Zib RSS Reader API

An opinionated RSS reader inspired by Austrian news culture ("Zeit im Bild").

### Features

- **Feed Management**: Add, update, and manage RSS/Atom feeds
- **Category Organization**: Organize feeds into categories with color coding
- **Health Monitoring**: Comprehensive health checks with database connectivity
- **Filtering & Pagination**: Advanced filtering and pagination for all endpoints

### API Structure

- **Feeds**: `/api/feeds/` - Manage RSS/Atom feeds
- **Categories**: `/api/categories/` - Organize feeds into categories  
- **Health**: `/health` - System health and monitoring

### Getting Started

1. Use the category endpoints to create feed categories
2. Add RSS feeds to your categories
3. Use filtering and pagination to manage large collections
4. Monitor system health with the `/health` endpoint

For detailed usage examples, see the individual endpoint documentation below.
    ''',
    debug=settings.debug,
    lifespan=lifespan,
    docs_url='/docs',
    redoc_url='/redoc',
    openapi_url='/openapi.json',
    contact={
        'name': 'Zib RSS Reader',
        'url': 'https://github.com/your-org/zib-rss-reader',
    },
    license_info={
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/MIT',
    },
    tags_metadata=[
        {
            'name': 'system',
            'description': 'System health and information endpoints'
        },
        {
            'name': 'feeds',
            'description': 'RSS/Atom feed management operations'
        },
        {
            'name': 'categories',
            'description': 'Feed category organization operations'
        },
        {
            'name': 'articles',
            'description': 'Article reading and management operations'
        },
        {
            'name': 'OPML Import',
            'description': 'OPML file import and job management operations'
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Add middleware to handle proxy headers (for nginx reverse proxy with SSL)
from starlette.middleware.base import BaseHTTPMiddleware

class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Trust X-Forwarded headers from nginx
        if "x-forwarded-proto" in request.headers:
            request.scope["scheme"] = request.headers["x-forwarded-proto"]
        if "x-forwarded-host" in request.headers:
            request.scope["server"] = (request.headers["x-forwarded-host"], request.scope["server"][1])
        
        response = await call_next(request)
        return response

app.add_middleware(ProxyHeadersMiddleware)

# Add exception handlers
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(ZibException, zib_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routers
app.include_router(feeds_router, prefix='/api')
app.include_router(categories_router, prefix='/api')
app.include_router(opml_router, prefix='/api')
app.include_router(articles_router, prefix='/api')
app.include_router(filters_router, prefix='/api')
app.include_router(settings_router, prefix='/api')


@app.middleware('http')
async def logging_middleware(request: Request, call_next):
    '''Log all requests with timing'''
    start_time = time.time()
    
    logger.info(f'{request.method} {request.url.path}')
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f'{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s')
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    '''Global exception handler'''
    logger.error(f'Unhandled exception: {exc}', exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }
    )


# Health check endpoint
@app.get('/health', tags=['system'], summary='System Health Check')
async def health_check(
    check_db: bool = Query(False, description='Include database connectivity check'),
    detailed: bool = Query(False, description='Include detailed system information')
):
    '''
    Comprehensive system health check endpoint.
    
    **Parameters:**
    - `check_db`: Include database connectivity and performance check
    - `detailed`: Include detailed system information (Python version, platform, etc.)
    
    **Response Status:**
    - `200`: System is healthy
    - `503`: System is unhealthy or degraded
    
    **Health Status Values:**
    - `healthy`: All systems operational
    - `degraded`: Some systems experiencing issues
    - `unhealthy`: Critical systems down
    
    **Example Usage:**
    - Basic health: `GET /health`
    - With database check: `GET /health?check_db=true`
    - Detailed health: `GET /health?check_db=true&detailed=true`
    '''
    try:
        health_data = HealthService.get_comprehensive_health(check_db=check_db)
        
        if detailed:
            health_data['system'] = HealthService.get_system_info()
        
        return health_data
        
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'app_name': settings.app_name,
                'version': settings.app_version
            }
        )


# Root endpoint
@app.get('/', tags=['system'], summary='API Information')
async def root():
    '''
    Get API information and available endpoints.
    
    Returns basic information about the Zib RSS Reader API including
    version, available documentation URLs, and key endpoints.
    '''
    return {
        'app_name': settings.app_name,
        'version': settings.app_version,
        'description': 'An opinionated RSS reader API inspired by Austrian news culture',
        'docs_url': '/docs',
        'redoc_url': '/redoc',
        'openapi_url': '/openapi.json',
        'health_url': '/health',
        'endpoints': {
            'feeds': '/api/feeds/',
            'categories': '/api/categories/',
            'articles': '/api/articles/',
            'health': '/health'
        },
        'status': 'operational'
    }


if __name__ == '__main__':
    import uvicorn
    
    logger.info(f'Starting Zib RSS Reader API server')
    logger.info(f'Server: {settings.host}:{settings.port}')
    logger.info(f'Debug mode: {settings.debug}')
    logger.info(f'Reload: {settings.reload}')
    logger.info(f'Database: {settings.database_url}')
    
    # Configure uvicorn for development and production
    uvicorn_config = {
        'app': 'app.main:app',
        'host': settings.host,
        'port': settings.port,
        'reload': settings.reload,
        'log_config': None,  # Disable uvicorn logging in favor of loguru
        'access_log': False,  # Disable access log (we have custom middleware)
        'server_header': False,  # Don't expose server header
        'date_header': False,  # Don't include date in headers
    }
    
    # Production optimizations
    if not settings.debug:
        uvicorn_config.update({
            'workers': 1,  # Single worker for SQLite
            'loop': 'uvloop',  # Use uvloop for better performance on Unix
            'http': 'httptools',  # Use httptools for better HTTP parsing
            'lifespan': 'on',  # Enable lifespan events
        })
    
    logger.info('Server configuration ready')
    logger.info(f'Documentation available at: http://{settings.host}:{settings.port}/docs')
    logger.info(f'Health check available at: http://{settings.host}:{settings.port}/health')
    
    uvicorn.run(**uvicorn_config)