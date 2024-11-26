from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import logging
from typing import Dict, Any, List, Optional
import uuid
from ..services.email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
email_service = EmailService()

class OnboardingRequest(BaseModel):
    name: str
    contact_id: str
    website: Optional[str] = None
    email: EmailStr

class OnboardingResponse(BaseModel):
    session_id: str
    message: str
    email_sent: bool

@router.post("/onboarding", response_model=OnboardingResponse)
async def onboard_user(request: OnboardingRequest):
    logger.info(f"Received onboarding request for user: {request.name}")
    
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Send welcome email
        email_sent = await email_service.send_welcome_email(
            recipient_email=request.email,
            recipient_name=request.name
        )
        
        return OnboardingResponse(
            session_id=session_id,
            message="Onboarding successful",
            email_sent=email_sent
        )
    except Exception as e:
        logger.error(f"Error during onboarding: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}", response_model=Dict[str, Any])
async def get_session_status(session_id: str):
    logger.info(f"Checking status for session: {session_id}")
    try:
        # TO DO: implement get_session_status
        return {}
    except ValueError as e:
        logger.error(f"Invalid session ID: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
