import httpx
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with various AI models"""
    
    def __init__(self):
        credentials_path = Path(__file__).parent.parent.parent.parent / 'credentials.json'
        with open(credentials_path) as f:
            self.credentials = json.load(f)
        
        self.local_ai_endpoint = self.credentials['AI_SERVICES']['LOCAL_AI']['endpoint']
        self.hf_api_key = self.credentials['AI_SERVICES']['HUGGING_FACE']['api_key']
        
    async def generate_local_ai(self, prompt: str, model: str = "llama2") -> Optional[str]:
        """Generate text using LocalAI (Ollama)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.local_ai_endpoint}/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                return response.json()['response']
                
        except Exception as e:
            logger.error(f"Error generating text with LocalAI: {str(e)}")
            return None
            
    async def generate_huggingface(
        self, 
        prompt: str, 
        model: str = "meta-llama/Llama-2-7b-chat-hf"
    ) -> Optional[str]:
        """Generate text using HuggingFace API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={"Authorization": f"Bearer {self.hf_api_key}"},
                    json={"inputs": prompt}
                )
                response.raise_for_status()
                return response.json()[0]['generated_text']
                
        except Exception as e:
            logger.error(f"Error generating text with HuggingFace: {str(e)}")
            return None
            
    async def analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment using HuggingFace API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api-inference.huggingface.co/models/cardiffnlp/twitter-roberta-base-sentiment",
                    headers={"Authorization": f"Bearer {self.hf_api_key}"},
                    json={"inputs": text}
                )
                response.raise_for_status()
                return response.json()[0]
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return None
            
    async def summarize_text(self, text: str) -> Optional[str]:
        """Summarize text using HuggingFace API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
                    headers={"Authorization": f"Bearer {self.hf_api_key}"},
                    json={"inputs": text}
                )
                response.raise_for_status()
                return response.json()[0]['summary_text']
                
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return None
