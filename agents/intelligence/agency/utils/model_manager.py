"""
Model manager for handling AI model initialization and caching.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..storage.storage_manager import StorageManager
from .logger import AgencyLogger

class ModelManager:
    def __init__(self, model_name: str = "deepseek-ai/deepseek-coder-6.7b-base"):
        self.logger = AgencyLogger("ModelManager").get_logger()
        self.storage = StorageManager()
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.logger.info(f"Initializing ModelManager with device: {self.device}")
        
        # Create model directory if it doesn't exist
        self.model_dir = Path(self.storage.get_model_path(model_name))
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize_model(self, force_reload: bool = False) -> None:
        """Initialize the model with proper error handling and logging."""
        try:
            if self.model is not None and not force_reload:
                self.logger.info("Model already initialized")
                return
            
            self.logger.info(f"Loading model: {self.model_name}")
            
            # Set up proper caching
            os.environ['TRANSFORMERS_CACHE'] = str(self.model_dir)
            
            # Initialize tokenizer first
            self.logger.debug("Initializing tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.model_dir),
                trust_remote_code=True
            )
            
            # Initialize model with proper memory handling
            self.logger.debug("Initializing model...")
            model_kwargs = {
                'torch_dtype': torch.float16 if self.device.type == 'cuda' else torch.float32,
                'low_cpu_mem_usage': True,
                'cache_dir': str(self.model_dir),
                'trust_remote_code': True
            }
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # Move model to device
            self.logger.debug(f"Moving model to device: {self.device}")
            self.model.to(self.device)
            
            self.logger.info("Model initialization complete")
            
        except Exception as e:
            self.logger.error(f"Error initializing model: {AgencyLogger.format_error(e)}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content with the model."""
        try:
            if self.model is None or self.tokenizer is None:
                self.initialize_model()
            
            # Encode input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=kwargs.get('max_length', 1024),
                    temperature=kwargs.get('temperature', 0.7),
                    top_p=kwargs.get('top_p', 0.9),
                    num_return_sequences=kwargs.get('num_sequences', 1)
                )
            
            # Decode output
            generated_text = self.tokenizer.batch_decode(
                outputs, skip_special_tokens=True
            )
            
            return {
                'generated_text': generated_text,
                'metadata': {
                    'model_name': self.model_name,
                    'device': str(self.device),
                    'generation_params': kwargs
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error during generation: {AgencyLogger.format_error(e)}")
            raise
    
    def cleanup(self) -> None:
        """Clean up model resources."""
        try:
            if self.model is not None:
                self.model.cpu()
                del self.model
                self.model = None
            
            if self.tokenizer is not None:
                del self.tokenizer
                self.tokenizer = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.logger.info("Model resources cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {AgencyLogger.format_error(e)}")
            raise
