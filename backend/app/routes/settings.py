from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.models.article import User
from app.core.database import TransactionManager
from app.services.auto_refresh_service import auto_refresh_service

router = APIRouter(prefix='/api/settings', tags=['settings'])


# Schemas
class UserSettingsRequest(BaseModel):
    '''Request model for updating user settings'''
    feeds_per_page: int = Field(default=50, ge=1, le=200)
    default_view: str = Field(default='unread')
    open_webpage_for_short_articles: bool = Field(default=False)
    short_article_threshold: int = Field(default=500, ge=50, le=5000)
    auto_refresh_feeds: bool = Field(default=False)
    auto_refresh_interval_minutes: int = Field(default=30, ge=5, le=1440)  # 5 min to 24 hours
    show_timestamps_in_list: bool = Field(default=True)
    preferred_view_mode: str = Field(default='list')


class UserSettingsResponse(BaseModel):
    '''Response model for user settings'''
    feeds_per_page: int
    default_view: str
    open_webpage_for_short_articles: bool
    short_article_threshold: int
    auto_refresh_feeds: bool
    auto_refresh_interval_minutes: int
    show_timestamps_in_list: bool
    preferred_view_mode: str


@router.get('', response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user)
):
    '''Get current user settings'''
    return UserSettingsResponse(
        feeds_per_page=current_user.feeds_per_page,
        default_view=current_user.default_view,
        open_webpage_for_short_articles=current_user.open_webpage_for_short_articles,
        short_article_threshold=current_user.short_article_threshold,
        auto_refresh_feeds=current_user.auto_refresh_feeds,
        auto_refresh_interval_minutes=current_user.auto_refresh_interval_minutes,
        show_timestamps_in_list=current_user.show_timestamps_in_list,
        preferred_view_mode=current_user.preferred_view_mode
    )


@router.put('', response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsRequest,
    current_user: User = Depends(get_current_user)
):
    '''Update user settings'''
    try:
        with TransactionManager():
            # Update user settings
            current_user.feeds_per_page = settings_data.feeds_per_page
            current_user.default_view = settings_data.default_view
            current_user.open_webpage_for_short_articles = settings_data.open_webpage_for_short_articles
            current_user.short_article_threshold = settings_data.short_article_threshold
            current_user.auto_refresh_feeds = settings_data.auto_refresh_feeds
            current_user.auto_refresh_interval_minutes = settings_data.auto_refresh_interval_minutes
            current_user.show_timestamps_in_list = settings_data.show_timestamps_in_list
            current_user.preferred_view_mode = settings_data.preferred_view_mode
            current_user.save()
            
            # Update auto-refresh service with new settings
            await auto_refresh_service.update_user_settings(current_user)
            
            return UserSettingsResponse(
                feeds_per_page=current_user.feeds_per_page,
                default_view=current_user.default_view,
                open_webpage_for_short_articles=current_user.open_webpage_for_short_articles,
                short_article_threshold=current_user.short_article_threshold,
                auto_refresh_feeds=current_user.auto_refresh_feeds,
                auto_refresh_interval_minutes=current_user.auto_refresh_interval_minutes,
                show_timestamps_in_list=current_user.show_timestamps_in_list,
                preferred_view_mode=current_user.preferred_view_mode
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to update settings: {str(e)}'
        )