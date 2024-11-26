"""
DeepSeek Integration Utility
Provides integration with DeepSeek-V2 model for content generation and analysis.
"""

import logging
import torch
from typing import Dict, List, Optional, Union
from transformers import AutoTokenizer, AutoModelForCausalLM
import asyncio
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSeekIntegration:
    """Integration class for DeepSeek-V2 model operations."""
    
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-6.7b-base"):
        """Initialize the DeepSeek integration."""
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the DeepSeek model with optimized memory settings."""
        try:
            logger.info(f"Loading DeepSeek model: {self.model_name}")
            
            # Load tokenizer first
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Load model with optimized settings
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="balanced_low_0",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                max_memory={0: "4GB", "cpu": "16GB"}
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise
    
    async def generate_content(
        self,
        prompt: str,
        max_length: int = 1000,
        temperature: float = 0.7,
        num_return_sequences: int = 1,
        **kwargs
    ) -> List[str]:
        """Generate content using the model."""
        try:
            def _generate():
                inputs = self.tokenizer(
                    prompt,
                    return_tensors="pt",
                    padding=True,
                    truncation=True
                ).to(self.device)
                
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    num_return_sequences=num_return_sequences,
                    pad_token_id=self.tokenizer.eos_token_id,
                    **kwargs
                )
                
                return [
                    self.tokenizer.decode(output, skip_special_tokens=True)
                    for output in outputs
                ]
            
            # Run generation in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, _generate)
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
    
    async def analyze_text(
        self,
        text: str,
        analysis_type: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Analyze text for various metrics."""
        try:
            analysis_prompts = {
                'trend_fit': """
                    Analyze the following trend for content creation:
                    
                    Trend: {text}
                    Industry: {industry}
                    Platform: {platform}
                    
                    Provide scores and insights for:
                    1. Trend alignment score (0-1)
                    2. Viral potential (0-1)
                    3. Content opportunities
                    4. Risk factors
                    
                    Format the response as a JSON object.
                    """,
                'sentiment': """
                    Analyze the sentiment of the following text:
                    
                    Text: {text}
                    
                    Provide:
                    1. Sentiment score (-1 to 1)
                    2. Key emotional triggers
                    3. Tone analysis
                    
                    Format the response as a JSON object.
                    """
            }
            
            prompt = analysis_prompts[analysis_type].format(
                text=text,
                **(context or {})
            )
            
            analysis_text = (await self.generate_content(
                prompt,
                max_length=500,
                temperature=0.3
            ))[0]
            
            # Parse the JSON response
            # Note: In production, add proper JSON validation
            import json
            return json.loads(analysis_text)
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            raise
    
    async def evaluate_content(
        self,
        content: str,
        metrics: Dict[str, float],
        context: Optional[Dict] = None
    ) -> Dict:
        """Evaluate content based on specified metrics."""
        try:
            evaluation_prompt = f"""
                Evaluate the following content based on these metrics:
                {', '.join(f'{k} (weight: {v})' for k, v in metrics.items())}
                
                Content:
                {content}
                
                Context:
                {context}
                
                Provide:
                1. Individual metric scores (0-1)
                2. Overall weighted score
                3. Improvement suggestions
                
                Format the response as a JSON object.
                """
            
            evaluation_text = (await self.generate_content(
                evaluation_prompt,
                max_length=800,
                temperature=0.3
            ))[0]
            
            # Parse the JSON response
            import json
            return json.loads(evaluation_text)
            
        except Exception as e:
            logger.error(f"Content evaluation failed: {e}")
            raise
    
    def __del__(self):
        """Cleanup resources."""
        self.executor.shutdown(wait=False)
