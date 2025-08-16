from .feeds import router as feeds_router
from .categories import router as categories_router
from .opml import router as opml_router

__all__ = [
    'feeds_router',
    'categories_router',
    'opml_router'
]