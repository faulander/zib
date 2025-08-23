from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime
from peewee import DoesNotExist, fn, JOIN
from app.schemas.article import (
    ArticleResponse, ArticleListResponse, ArticleQueryParams,
    BulkMarkReadRequest, BulkOperationResponse, ArticleStatsResponse,
    MarkArticleRequest, MessageResponse, ReadStatusFilter,
    FilteredCountsResponse
)
from app.models.article import Article, User, ReadStatus
from app.models.base import Feed, Category
from app.core.auth import get_current_user
from app.core.database import db

router = APIRouter(prefix="/articles", tags=["articles"])


def build_article_query(user: User, params: ArticleQueryParams):
    '''Build article query with filtering and joins'''
    
    # Base query with joins
    query = (Article
        .select()
        .join(Feed, JOIN.INNER)
        .join(Category, JOIN.LEFT_OUTER, on=(Feed.category == Category.id))
    )
    
    # Apply cursor-based pagination filter
    if params.since_id:
        # For cursor pagination, we want articles that come after since_id in the sort order
        # Since we sort by published_date DESC, then id DESC, we want articles with:
        # - published_date < since_article.published_date, OR
        # - published_date = since_article.published_date AND id < since_id
        try:
            since_article = Article.get_by_id(params.since_id)
            query = query.where(
                (Article.published_date < since_article.published_date) |
                ((Article.published_date == since_article.published_date) & (Article.id < params.since_id))
            )
        except Article.DoesNotExist:
            # If since_id article doesn't exist, fall back to simple id comparison
            query = query.where(Article.id < params.since_id)
    
    # Apply filters
    if params.feed_id:
        query = query.where(Feed.id == params.feed_id)
    
    if params.category_id:
        query = query.where(Category.id == params.category_id)
    
    # Handle read status filtering separately since it requires a different join
    if params.read_status != ReadStatusFilter.all:
        if params.read_status == ReadStatusFilter.read:
            # Only articles that are marked as read by this user
            read_article_ids = (ReadStatus
                .select(ReadStatus.article)
                .where((ReadStatus.user == user) & (ReadStatus.is_read == True)))
            query = query.where(Article.id.in_(read_article_ids))
        elif params.read_status == ReadStatusFilter.unread:
            # Articles not marked as read by this user
            read_article_ids = (ReadStatus
                .select(ReadStatus.article)
                .where((ReadStatus.user == user) & (ReadStatus.is_read == True)))
            query = query.where(Article.id.not_in(read_article_ids))
        elif params.read_status == ReadStatusFilter.starred:
            # Only articles that are starred by this user
            starred_article_ids = (ReadStatus
                .select(ReadStatus.article)
                .where((ReadStatus.user == user) & (ReadStatus.is_starred == True)))
            query = query.where(Article.id.in_(starred_article_ids))
    
    if params.search:
        # Use LIKE for case-insensitive search
        search_pattern = f'%{params.search}%'
        query = query.where(
            (Article.title ** search_pattern) |
            (Article.content ** search_pattern)
        )
    
    if params.tags:
        tag_list = [tag.strip() for tag in params.tags.split(',') if tag.strip()]
        for tag in tag_list:
            query = query.where(Article.tags.contains(tag))
    
    if params.author:
        query = query.where(Article.author.contains(params.author))
    
    if params.date_from:
        query = query.where(Article.published_date >= params.date_from)
    
    if params.date_to:
        query = query.where(Article.published_date <= params.date_to)
    
    # Apply sorting
    if params.sort.value == 'created_at':
        sort_field = Article.created_at
    elif params.sort.value == 'published_date':
        sort_field = Article.published_date
    elif params.sort.value == 'title':
        sort_field = Article.title
    elif params.sort.value == 'author':
        sort_field = Article.author
    else:
        sort_field = Article.published_date
    
    if params.order.value == 'asc':
        query = query.order_by(sort_field.asc(), Article.id.asc())
    else:
        query = query.order_by(sort_field.desc(), Article.id.desc())
    
    return query


def serialize_article(article: Article, user: User) -> ArticleResponse:
    '''Serialize article with read status information'''
    
    # Build feed info
    feed_info = {
        'id': article.feed.id,
        'title': article.feed.title,
        'url': article.feed.url,
        'category': None
    }
    
    # Add category if available
    if article.feed.category:
        feed_info['category'] = {
            'id': article.feed.category.id,
            'name': article.feed.category.name
        }
    
    # Get read status for this user and article
    try:
        read_status = ReadStatus.get(
            (ReadStatus.user == user) & (ReadStatus.article == article)
        )
        read_status_info = {
            'is_read': read_status.is_read,
            'is_starred': read_status.is_starred,
            'is_archived': read_status.is_archived,
            'read_at': read_status.read_at,
            'starred_at': read_status.starred_at
        }
    except ReadStatus.DoesNotExist:
        # No read status record for this user/article
        read_status_info = {
            'is_read': False,
            'is_starred': False,
            'is_archived': False,
            'read_at': None,
            'starred_at': None
        }
    
    return ArticleResponse(
        id=article.id,
        title=article.title,
        content=article.content,
        summary=article.summary,
        url=article.url,
        guid=article.guid,
        author=article.author,
        published_date=article.published_date,
        tags=article.get_tag_list(),
        image_url=article.image_url,
        created_at=article.created_at,
        updated_at=article.updated_at,
        feed=feed_info,
        read_status=read_status_info,
        word_count=article.get_word_count(),
        estimated_reading_time=article.get_estimated_reading_time()
    )


def fetch_filtered_articles_with_pagination(query, user, category_id, requested_limit, cursor=None, max_queries=5):
    '''
    Smart pagination that fetches articles iteratively until we have enough filtered results.
    
    Args:
        query: Base Peewee query object
        user: Current user for filtering
        category_id: Category ID for content filters
        requested_limit: Number of filtered articles requested
        cursor: Cursor for pagination (article ID)
        max_queries: Maximum number of database queries to prevent infinite loops
        
    Returns:
        tuple: (filtered_articles, has_more, next_cursor)
    '''
    from app.services.filter_service import FilterService
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    
    filtered_articles = []
    current_cursor = cursor
    queries_made = 0
    batch_size = max(requested_limit * 2, 100)  # Start with larger batches to account for filtering
    
    logger.info(f"Smart pagination: requesting {requested_limit} articles, starting with batch size {batch_size}")
    
    while len(filtered_articles) < requested_limit and queries_made < max_queries:
        queries_made += 1
        
        # Apply cursor if we have one
        batch_query = query
        if current_cursor:
            batch_query = batch_query.where(Article.id < current_cursor)
        
        # Fetch articles with extra buffer to check for has_more
        fetch_limit = batch_size + 1
        batch_articles = list(batch_query.limit(fetch_limit))
        
        logger.info(f"Query {queries_made}: Fetched {len(batch_articles)} raw articles")
        
        if not batch_articles:
            # No more articles in database
            logger.info("No more articles in database")
            break
            
        # Remember if we got the extra article (indicates more available)
        has_more_raw = len(batch_articles) > batch_size
        if has_more_raw:
            batch_articles = batch_articles[:batch_size]  # Remove the extra article
            
        # Apply content filters
        filtered_batch = FilterService.apply_filters(batch_articles, user, category_id)
        
        logger.info(f"Query {queries_made}: After filtering: {len(filtered_batch)} articles")
        
        # Add to our result collection, but avoid duplicates
        for article in filtered_batch:
            # Check if we already have this article (shouldn't happen, but safety check)
            if not any(existing.id == article.id for existing in filtered_articles):
                filtered_articles.append(article)
            else:
                logger.warning(f"Duplicate article detected: {article.id} - {article.title}")
        
        # Update cursor for next iteration
        if batch_articles:
            current_cursor = batch_articles[-1].id
            
        # If we didn't get any new raw articles, we're at the end
        if not has_more_raw:
            logger.info("Reached end of raw articles")
            break
            
        # If we got enough filtered articles, we can stop
        if len(filtered_articles) >= requested_limit:
            logger.info(f"Got enough filtered articles: {len(filtered_articles)}")
            break
            
        # Adaptive batch sizing: if filtering is very aggressive, increase batch size
        filter_efficiency = len(filtered_batch) / len(batch_articles) if batch_articles else 0
        if filter_efficiency < 0.1 and queries_made < max_queries - 1:  # Less than 10% pass through
            batch_size = min(batch_size * 2, 500)  # Double batch size, cap at 500
            logger.info(f"Low filter efficiency ({filter_efficiency:.2%}), increasing batch size to {batch_size}")
    
    # Trim to requested limit
    has_more_filtered = len(filtered_articles) > requested_limit
    if has_more_filtered:
        filtered_articles = filtered_articles[:requested_limit]
        
    # Calculate next cursor
    next_cursor = None
    if filtered_articles and (has_more_filtered or queries_made == max_queries):
        next_cursor = filtered_articles[-1].id
        
    logger.info(f"Smart pagination complete: {len(filtered_articles)} articles returned, has_more={has_more_filtered or queries_made == max_queries}, {queries_made} queries made")
    
    return filtered_articles, (has_more_filtered or queries_made == max_queries), next_cursor


@router.get("/", response_model=ArticleListResponse)
async def get_articles(
    params: ArticleQueryParams = Depends(),
    current_user: User = Depends(get_current_user)
):
    '''Get articles with cursor-based pagination, filtering, and search'''
    
    try:
        # Debug: Log the parameters being received
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info(f"Articles API called with params: limit={params.limit}, category_id={params.category_id}, feed_id={params.feed_id}, read_status={params.read_status}, search={params.search}")
        
        # Build query
        query = build_article_query(current_user, params)
        
        # Get total count (for legacy pagination info) - this is not filtered by content filters
        total_query = query.clone()
        if params.since_id:
            # Remove cursor filter for total count
            total_query = build_article_query(current_user, ArticleQueryParams(
                limit=params.limit,
                feed_id=params.feed_id,
                category_id=params.category_id,
                read_status=params.read_status,
                search=params.search,
                tags=params.tags,
                author=params.author,
                date_from=params.date_from,
                date_to=params.date_to,
                sort=params.sort,
                order=params.order
            ))
        total = total_query.count()
        
        # Use smart pagination that handles content filtering properly
        articles_data, has_more, next_cursor = fetch_filtered_articles_with_pagination(
            query=query,
            user=current_user,
            category_id=params.category_id,
            requested_limit=params.limit,
            cursor=params.since_id
        )
        
        # Serialize articles
        articles = [serialize_article(article, current_user) for article in articles_data]
        
        # Build legacy pagination info (for backward compatibility)
        pagination = {
            'limit': params.limit,
            'since_id': params.since_id,
            'total': total,
            'returned': len(articles)
        }
        
        return ArticleListResponse(
            articles=articles,
            pagination=pagination,
            has_more=has_more,
            next_cursor=next_cursor
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching articles: {str(e)}"
        )


@router.post("/bulk/mark-read", response_model=BulkOperationResponse)
async def bulk_mark_read(
    request: BulkMarkReadRequest,
    current_user: User = Depends(get_current_user)
):
    '''Bulk mark articles as read'''
    
    try:
        # Verify all articles exist
        articles = list(Article.select().where(Article.id.in_(request.article_ids)))
        
        if len(articles) != len(request.article_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more articles not found"
            )
        
        # Mark all as read
        updated_count = 0
        for article in articles:
            ReadStatus.mark_read(current_user, article, True)
            updated_count += 1
        
        return BulkOperationResponse(
            message=f"Marked {updated_count} articles as read",
            updated_count=updated_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error bulk marking articles as read: {str(e)}"
        )


@router.post("/bulk/mark-read-by-feed/{feed_id}", response_model=BulkOperationResponse)
async def bulk_mark_read_by_feed(
    feed_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Bulk mark all articles in a feed as read'''
    
    try:
        # Get all articles in the feed
        articles = list(Article.select().where(Article.feed_id == feed_id))
        
        if not articles:
            return BulkOperationResponse(
                message="No articles found in feed",
                updated_count=0
            )
        
        # Mark all as read
        updated_count = 0
        for article in articles:
            ReadStatus.mark_read(current_user, article, True)
            updated_count += 1
        
        return BulkOperationResponse(
            message="Marked all articles in feed as read",
            updated_count=updated_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error bulk marking feed articles as read: {str(e)}"
        )


@router.post("/bulk/mark-read-by-category/{category_id}", response_model=BulkOperationResponse)
async def bulk_mark_read_by_category(
    category_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Bulk mark all articles in a category as read'''
    
    try:
        # Get all articles in feeds that belong to this category
        articles = list(
            Article
            .select()
            .join(Feed, JOIN.INNER)
            .where(Feed.category_id == category_id)
        )
        
        if not articles:
            return BulkOperationResponse(
                message="No articles found in category",
                updated_count=0
            )
        
        # Mark all as read
        updated_count = 0
        for article in articles:
            ReadStatus.mark_read(current_user, article, True)
            updated_count += 1
        
        return BulkOperationResponse(
            message="Marked all articles in category as read",
            updated_count=updated_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error bulk marking category articles as read: {str(e)}"
        )


@router.get("/filtered-counts", response_model=FilteredCountsResponse)
async def get_filtered_counts(
    search: Optional[str] = Query(None, description='Search query to apply to counts'),
    current_user: User = Depends(get_current_user)
):
    '''Get filtered article counts for categories and feeds including content filter rules'''
    
    try:
        from app.services.filter_service import FilterService
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        
        logger.info(f"Getting filtered counts with search: {search}")
        
        # Get all categories and feeds
        categories = list(Category.select())
        feeds = list(Feed.select())
        
        # Initialize counters
        category_counts = {}
        feed_counts = {}
        total_unread = 0
        
        # For each category, get filtered unread count
        for category in categories:
            try:
                # Build base query for unread articles in this category
                query = (Article
                    .select()
                    .join(Feed)
                    .where(
                        (Feed.category == category) &
                        (Feed.is_active == True)
                    ))
                
                # Apply search filter if provided
                if search:
                    query = query.where(
                        (Article.title.contains(search)) |
                        (Article.author.contains(search))
                    )
                
                # Filter out read articles for this user
                read_article_ids = (ReadStatus
                    .select(ReadStatus.article)
                    .where(
                        (ReadStatus.user == current_user) & 
                        (ReadStatus.is_read == True)
                    ))
                
                query = query.where(Article.id.not_in(read_article_ids))
                
                # Execute query to get articles
                articles_data = list(query)
                
                # Apply content filter rules (this is where the magic happens!)
                filtered_articles = FilterService.apply_filters(articles_data, current_user, category.id)
                
                # Count the filtered results
                count = len(filtered_articles)
                category_counts[category.id] = count
                
            except Exception as e:
                logger.error(f"Error counting category {category.id}: {e}")
                category_counts[category.id] = 0
        
        # For each feed, get filtered unread count
        for feed in feeds:
            try:
                # Build base query for unread articles in this feed
                query = (Article
                    .select()
                    .where(
                        (Article.feed == feed) &
                        (feed.is_active == True)
                    ))
                
                # Apply search filter if provided
                if search:
                    query = query.where(
                        (Article.title.contains(search)) |
                        (Article.author.contains(search))
                    )
                
                # Filter out read articles for this user
                read_article_ids = (ReadStatus
                    .select(ReadStatus.article)
                    .where(
                        (ReadStatus.user == current_user) & 
                        (ReadStatus.is_read == True)
                    ))
                
                query = query.where(Article.id.not_in(read_article_ids))
                
                # Execute query to get articles
                articles_data = list(query)
                
                # Apply content filter rules
                filtered_articles = FilterService.apply_filters(articles_data, current_user, feed.category.id if feed.category else None)
                
                # Count the filtered results
                count = len(filtered_articles)
                feed_counts[feed.id] = count
                
            except Exception as e:
                logger.error(f"Error counting feed {feed.id}: {e}")
                feed_counts[feed.id] = 0
        
        # Calculate total unread (sum all category counts)
        total_unread = sum(category_counts.values())
        
        logger.info(f"Filtered counts calculated: categories={len(category_counts)}, feeds={len(feed_counts)}, total={total_unread}")
        
        return FilteredCountsResponse(
            categories=category_counts,
            feeds=feed_counts,
            total_unread=total_unread
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching filtered counts: {str(e)}"
        )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article_by_id(
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Get a specific article by ID'''
    
    try:
        # Get article with feed and category
        article = (Article
            .select()
            .join(Feed, JOIN.INNER)
            .join(Category, JOIN.LEFT_OUTER, on=(Feed.category == Category.id))
            .where(Article.id == article_id)
            .get())
        
        return serialize_article(article, current_user)
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching article: {str(e)}"
        )


@router.post("/{article_id}/mark-read", response_model=MessageResponse)
async def mark_article_read(
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Mark an article as read'''
    
    try:
        article = Article.get_by_id(article_id)
        ReadStatus.mark_read(current_user, article, True)
        
        return MessageResponse(message="Article marked as read")
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking article as read: {str(e)}"
        )


@router.post("/{article_id}/mark-unread", response_model=MessageResponse)
async def mark_article_unread(
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Mark an article as unread'''
    
    try:
        article = Article.get_by_id(article_id)
        ReadStatus.mark_read(current_user, article, False)
        
        return MessageResponse(message="Article marked as unread")
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking article as unread: {str(e)}"
        )


@router.post("/{article_id}/star", response_model=MessageResponse)
async def star_article(
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Star an article'''
    
    try:
        article = Article.get_by_id(article_id)
        ReadStatus.mark_starred(current_user, article, True)
        
        return MessageResponse(message="Article starred")
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starring article: {str(e)}"
        )


@router.post("/{article_id}/unstar", response_model=MessageResponse)
async def unstar_article(
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    '''Unstar an article'''
    
    try:
        article = Article.get_by_id(article_id)
        ReadStatus.mark_starred(current_user, article, False)
        
        return MessageResponse(message="Article unstarred")
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unstarring article: {str(e)}"
        )



@router.get("/stats", response_model=ArticleStatsResponse)
async def get_article_statistics(
    current_user: User = Depends(get_current_user)
):
    '''Get article statistics for the current user'''
    
    try:
        from datetime import datetime, timedelta
        
        # Get total articles count
        total_articles = Article.select().count()
        
        # Get read/unread counts for current user
        read_articles = (ReadStatus
            .select()
            .where((ReadStatus.user == current_user) & (ReadStatus.is_read == True))
            .count())
        
        unread_articles = total_articles - read_articles
        
        # Get starred articles count
        starred_articles = (ReadStatus
            .select()
            .where((ReadStatus.user == current_user) & (ReadStatus.is_starred == True))
            .count())
        
        # Get articles from this week
        week_ago = datetime.now() - timedelta(days=7)
        articles_this_week = (Article
            .select()
            .where(Article.created_at >= week_ago)
            .count())
        
        # Get articles from this month
        month_ago = datetime.now() - timedelta(days=30)
        articles_this_month = (Article
            .select()
            .where(Article.created_at >= month_ago)
            .count())
        
        return ArticleStatsResponse(
            total_articles=total_articles,
            read_articles=read_articles,
            unread_articles=unread_articles,
            starred_articles=starred_articles,
            articles_this_week=articles_this_week,
            articles_this_month=articles_this_month
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching article statistics: {str(e)}"
        )

