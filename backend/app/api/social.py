from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.services.social_service import SocialService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
social_service = SocialService()

class SocialPost(BaseModel):
    content: str
    platforms: List[str]
    media_urls: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None

class SocialAnalytics(BaseModel):
    platform: str
    metrics: dict
    period: str

@router.post("/post")
async def create_post(post: SocialPost):
    try:
        result = await social_service.create_post(post)
        return {"status": "success", "post_id": result}
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule")
async def schedule_post(post: SocialPost):
    if not post.scheduled_time:
        raise HTTPException(status_code=400, detail="Scheduled time is required")
    try:
        result = await social_service.schedule_post(post)
        return {"status": "success", "schedule_id": result}
    except Exception as e:
        logger.error(f"Error scheduling post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_analytics(
    platform: str = Query(..., description="Social media platform"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    try:
        analytics = await social_service.get_analytics(platform, start_date, end_date)
        return analytics
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending")
async def get_pending_posts():
    try:
        posts = await social_service.get_pending_posts()
        return posts
    except Exception as e:
        logger.error(f"Error fetching pending posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
