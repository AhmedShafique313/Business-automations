from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os
import requests

# Add the parent directory to sys.path to import the wrapper
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str
    use_deepseek: Optional[bool] = False
    max_tokens: Optional[int] = 1000

class AIResponse(BaseModel):
    response: str
    source: str  # 'meta' or 'deepseek'

@router.post("/generate", response_model=AIResponse)
async def generate_response(request: PromptRequest):
    try:
        # Set up Deep Seek API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer sk-bc0ab457bbb6473e8206924592aed710"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.prompt}
            ],
            "stream": False
        }
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload)
        response_data = response.json()
        return AIResponse(response=response_data.get('choices', [{}])[0].get('message', {}).get('content', ''), source="deepseek")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy", "services": ["deepseek"]}
