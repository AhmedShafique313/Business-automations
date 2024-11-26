from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import uuid
import logging
from datetime import datetime

from app.services.email_service import EmailService
from app.services.ai_service import AIService
from app.services.storage_service import StorageService

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Business Platform API")

# CORS middleware configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
email_service = EmailService()
ai_service = AIService()
storage_service = StorageService()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

class OnboardingRequest(BaseModel):
    name: str
    email: EmailStr
    website: str
    business_type: str
    contact_id: Optional[str] = None

class OnboardingResponse(BaseModel):
    session_id: str
    message: str
    dashboard_url: str

async def generate_welcome_content(user_data: OnboardingRequest) -> Dict[str, str]:
    """Generate personalized welcome content using AI"""
    try:
        prompt = f"""Create a personalized welcome message for {user_data.name}'s {user_data.business_type} business.
        Include specific tips for their industry and how our AI platform can help them grow."""
        
        welcome_message = await ai_service.generate_local_ai(prompt)
        if not welcome_message:
            welcome_message = f"Welcome {user_data.name}! We're excited to help grow your {user_data.business_type} business."
            
        return {
            "subject": f"Welcome to AI Business Platform, {user_data.name}!",
            "content": welcome_message
        }
    except Exception as e:
        logger.error(f"Error generating welcome content: {str(e)}")
        return {
            "subject": "Welcome to AI Business Platform!",
            "content": f"Welcome {user_data.name}! We're excited to have you onboard."
        }

@app.post("/api/onboard", response_model=OnboardingResponse)
async def onboard_user(request: OnboardingRequest):
    try:
        logger.info(f"Starting onboarding process for {request.name}")
        
        # Validate email format
        if not request.email or '@' not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email format")
            
        # Validate website format
        if not request.website:
            raise HTTPException(status_code=400, detail="Website URL is required")
            
        # Validate business type
        valid_business_types = [
            'E-commerce', 'Local Business', 'Professional Services',
            'Healthcare', 'Real Estate', 'Technology', 'Other'
        ]
        if request.business_type not in valid_business_types:
            raise HTTPException(status_code=400, detail="Invalid business type")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Generated session ID: {session_id}")
        
        # Store user data (mock database operation)
        user_data = {
            "session_id": session_id,
            "name": request.name,
            "email": request.email,
            "website": request.website,
            "business_type": request.business_type,
            "contact_id": request.contact_id or str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Storing user data: {user_data}")
        
        try:
            # Generate welcome content
            welcome_content = await generate_welcome_content(request)
            logger.info("Generated welcome content successfully")
            
            # Send welcome email
            await email_service.send_welcome_email(
                to_email=request.email,
                subject=welcome_content["subject"],
                content=welcome_content["content"]
            )
            logger.info(f"Sent welcome email to {request.email}")
            
        except Exception as e:
            logger.error(f"Non-critical error during onboarding: {str(e)}")
            # Continue with onboarding even if email fails
        
        # Initialize AI tasks
        try:
            initial_tasks = [
                "Analyze website content and suggest improvements",
                "Generate social media content calendar",
                "Create email marketing templates",
                "Prepare business performance report"
            ]
            
            # Store tasks in user's workspace
            for task in initial_tasks:
                logger.info(f"Created task for user {session_id}: {task}")
                
        except Exception as e:
            logger.error(f"Failed to create initial tasks: {str(e)}")
            # Continue with onboarding even if task creation fails
        
        response_data = OnboardingResponse(
            session_id=session_id,
            message="Onboarding successful! Welcome to AI Business Platform.",
            dashboard_url=f"/dashboard?session={session_id}"
        )
        logger.info(f"Onboarding successful for {request.name}")
        
        return response_data
        
    except HTTPException as he:
        logger.error(f"HTTP error during onboarding: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during onboarding: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during onboarding. Please try again."
        )

@app.get("/api/dashboard/{session_id}")
async def get_dashboard_data(session_id: str):
    try:
        logger.info(f"Fetching dashboard data for session: {session_id}")
        
        # Mock dashboard data - replace with actual database queries
        tasks = [
            {
                "id": "1",
                "title": "Analyze website content",
                "status": "in_progress",
                "progress": 45
            },
            {
                "id": "2",
                "title": "Generate social media content",
                "status": "pending",
                "progress": 0
            },
            {
                "id": "3",
                "title": "Create email templates",
                "status": "pending",
                "progress": 0
            }
        ]
        
        response_data = {
            "session_id": session_id,
            "tasks": tasks,
            "last_updated": datetime.utcnow().isoformat()
        }
        logger.info(f"Sending dashboard data: {response_data}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
