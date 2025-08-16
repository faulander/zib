from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from contextlib import asynccontextmanager

from .core.config import settings
from .core.logging import setup_logging, get_logger

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
    
    yield
    
    # Shutdown
    logger.info('Shutting down application')


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description='An opinionated RSS reader inspired by Austrian news culture',
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


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
@app.get('/health', tags=['system'])
async def health_check():
    '''Health check endpoint'''
    return {
        'status': 'healthy',
        'app_name': settings.app_name,
        'version': settings.app_version,
        'debug': settings.debug
    }


# Root endpoint
@app.get('/', tags=['system'])
async def root():
    '''Root endpoint with API information'''
    return {
        'app_name': settings.app_name,
        'version': settings.app_version,
        'description': 'An opinionated RSS reader API',
        'docs_url': '/docs',
        'health_url': '/health'
    }


if __name__ == '__main__':
    import uvicorn
    
    logger.info(f'Starting server on {settings.host}:{settings.port}')
    
    uvicorn.run(
        'app.main:app',
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_config=None  # Disable uvicorn logging in favor of loguru
    )