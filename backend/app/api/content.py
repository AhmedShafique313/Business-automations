from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.services.content_service import ContentService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
content_service = ContentService()

class ContentRequest(BaseModel):
    type: str
    topic: str
    tone: Optional[str] = None
    length: Optional[int] = None
    keywords: Optional[List[str]] = None
    target_audience: Optional[str] = None

class ContentMetadata(BaseModel):
    seo_score: Optional[float] = None
    readability_score: Optional[float] = None
    target_keywords: Optional[List[str]] = None

class ContentResponse(BaseModel):
    id: str
    content: str
    type: str
    status: str
    created_at: str
    metadata: Optional[ContentMetadata] = None

@router.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    try:
        content = await content_service.generate_content(request)
        return content
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_content_history(
    type: Optional[str] = Query(None, description="Content type filter")
):
    try:
        history = await content_service.get_content_history(type)
        return history
    except Exception as e:
        logger.error(f"Error fetching content history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(content_id: str, updates: Dict):
    try:
        updated_content = await content_service.update_content(content_id, updates)
        return updated_content
    except Exception as e:
        logger.error(f"Error updating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_content(content: str):
    try:
        analysis = await content_service.analyze_content(content)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_content(
    content: str,
    target_keywords: List[str],
    content_type: str
):
    try:
        optimized = await content_service.optimize_content(
            content, target_keywords, content_type
        )
        return optimized
    except Exception as e:
        logger.error(f"Error optimizing content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
