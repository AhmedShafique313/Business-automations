from pydantic import BaseModel, EmailStr, HttpUrl, validator
from typing import Optional
from datetime import datetime

class OnboardingRequest(BaseModel):
    name: str
    contact_id: str
    email: EmailStr
    website: Optional[HttpUrl] = None
    
    @validator('name')
    def name_must_be_valid(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()
    
    @validator('contact_id')
    def contact_id_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError('Contact ID cannot be empty')
        return v.strip()

class OnboardingResponse(BaseModel):
    status: str
    message: str
    session_id: str
    created_at: datetime = datetime.utcnow()

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None
