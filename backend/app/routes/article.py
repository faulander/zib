from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime
from peewee import DoesNotExist, fn, JOIN
from app.schemas.article import (
    ArticleResponse, ArticleListResponse, ArticleQueryParams,
    BulkMarkReadRequest, BulkOperationResponse, ArticleStatsResponse,
    MarkArticleRequest, MessageResponse, ReadStatusFilter
)
from app.models.article import Article, User, ReadStatus
from app.models.base import Feed, Category
from app.core.auth import get_current_user
from app.core.database import db

router = APIRouter(prefix="/api/articles", tags=["articles"])


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


@router.get("", response_model=ArticleListResponse)
async def get_articles(
    params: ArticleQueryParams = Depends(),
    current_user: User = Depends(get_current_user)
):
    '''Get articles with cursor-based pagination, filtering, and search'''
    
    try:
        # Build query
        query = build_article_query(current_user, params)
        
        # Get total count (for legacy pagination info)
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
        
        # Execute query with limit + 1 to check if there are more articles
        limit_plus_one = params.limit + 1
        articles_data = list(query.limit(limit_plus_one))
        
        # Apply user filters to remove unwanted articles
        from app.services.filter_service import FilterService
        articles_data = FilterService.apply_filters(articles_data, current_user, params.category_id)
        
        # Check if there are more articles
        has_more = len(articles_data) > params.limit
        if has_more:
            articles_data = articles_data[:params.limit]  # Remove the extra article
        
        # Serialize articles
        articles = [serialize_article(article, current_user) for article in articles_data]
        
        # Get next cursor (ID of the last article)
        next_cursor = None
        if has_more and articles:
            next_cursor = articles[-1].id
        
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