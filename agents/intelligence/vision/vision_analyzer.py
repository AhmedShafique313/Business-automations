"""Vision Analyzer using LLaVA for advanced visual intelligence."""

import os
import logging
import torch
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import sys

# Add LLaVA to path
LLAVA_PATH = os.path.join(os.path.dirname(__file__), 'llava')
sys.path.append(LLAVA_PATH)

from llava.model import LlavaLlamaForCausalLM
from llava.conversation import conv_templates
from llava.utils import disable_torch_init
from llava.mm_utils import process_images, tokenizer_image_token

from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = "liuhaotian/llava-v1.5-13b"

@dataclass
class VisionAnalysis:
    """Structure for vision analysis results."""
    content_description: str
    visual_elements: List[str]
    brand_elements: List[str]
    engagement_factors: List[Dict[str, float]]
    improvement_suggestions: List[str]
    reasoning_steps: List[str]

class VisionAnalyzer:
    """Analyzes visual content using LLaVA for advanced reasoning."""
    
    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        """Initialize the vision analyzer.
        
        Args:
            model_path: Path or name of LLaVA model
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not torch.cuda.is_available():
            logger.warning("CUDA not available. Using CPU for vision analysis. This will be slow!")
        
        try:
            # Disable torch init to speed up loading
            disable_torch_init()
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = LlavaLlamaForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            self.model.eval()
            
            # Get conversation template
            self.conv = conv_templates["v1"].copy()
            
            logger.info(f"Successfully loaded LLaVA model from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load LLaVA model: {e}")
            raise
    
    def analyze_image(self, image_path: str) -> VisionAnalysis:
        """Analyze an image using step-by-step reasoning.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            VisionAnalysis object containing detailed analysis
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            # Process image
            image = process_images([image_path])[0]
            image = image.to(self.device, dtype=torch.float16)
            
            # Get analysis components
            content_desc = self._get_content_description(image)
            visual_elements = self._analyze_visual_elements(image)
            brand_elements = self._analyze_brand_elements(image)
            engagement_factors = self._analyze_engagement_factors(image)
            suggestions = self._generate_suggestions(image)
            reasoning_steps = self._get_reasoning_steps(image)
            
            return VisionAnalysis(
                content_description=content_desc,
                visual_elements=visual_elements,
                brand_elements=brand_elements,
                engagement_factors=engagement_factors,
                improvement_suggestions=suggestions,
                reasoning_steps=reasoning_steps
            )
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise
    
    def _run_inference(self, image: torch.Tensor, prompt: str) -> str:
        """Run inference using LLaVA model."""
        try:
            # Prepare conversation
            self.conv.messages = []
            self.conv.append_message(self.conv.roles[0], prompt)
            self.conv.append_message(self.conv.roles[1], None)
            prompt = self.conv.get_prompt()
            
            # Tokenize input
            input_ids = tokenizer_image_token(prompt, self.tokenizer, 0, return_tensors='pt').unsqueeze(0)
            input_ids = input_ids.to(self.device)
            
            # Generate response
            with torch.inference_mode():
                output_ids = self.model.generate(
                    input_ids,
                    images=image.unsqueeze(0),
                    do_sample=True,
                    temperature=0.2,
                    max_new_tokens=512,
                    use_cache=True
                )
            
            # Decode response
            output = self.tokenizer.decode(output_ids[0, input_ids.shape[1]:], skip_special_tokens=True)
            return output.strip()
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return ""
    
    def _get_content_description(self, image: torch.Tensor) -> str:
        """Get detailed description of image content."""
        prompt = """Please provide a detailed description of this image, focusing on:
        1. The main subject or focus
        2. Visual composition and layout
        3. Colors and lighting
        4. Notable details or unique elements
        5. Overall mood or atmosphere"""
        return self._run_inference(image, prompt)
    
    def _analyze_visual_elements(self, image: torch.Tensor) -> List[str]:
        """Analyze key visual elements in the image."""
        prompt = """Analyze this image step by step:
        1. What are the main visual elements?
        2. How are they arranged?
        3. What colors are dominant?
        4. What textures or patterns are present?
        5. How is the lighting used?"""
        result = self._run_inference(image, prompt)
        return [line.strip() for line in result.split('\n') if line.strip()]
    
    def _analyze_brand_elements(self, image: torch.Tensor) -> List[str]:
        """Identify and analyze brand elements."""
        prompt = """Identify brand elements in this image:
        1. Are there any logos present?
        2. What brand colors are used?
        3. Is there any brand-specific typography?
        4. Are there any brand-related symbols or icons?
        5. How are brand guidelines followed?"""
        result = self._run_inference(image, prompt)
        return [line.strip() for line in result.split('\n') if line.strip()]
    
    def _analyze_engagement_factors(self, image: torch.Tensor) -> List[Dict[str, float]]:
        """Analyze factors that might affect engagement."""
        prompt = """Rate these engagement factors from 0-10 and explain your rating:
        1. Visual appeal
        2. Emotional impact
        3. Call-to-action clarity
        4. Brand consistency
        5. Message clarity"""
        result = self._run_inference(image, prompt)
        
        factors = []
        for line in result.split('\n'):
            if ':' in line:
                factor, score = line.split(':')
                try:
                    # Extract numeric score from text
                    score_text = score.strip().split('/')[0].strip()
                    score_float = float(score_text)
                    factors.append({
                        'factor': factor.strip(),
                        'score': score_float
                    })
                except (ValueError, IndexError):
                    continue
        return factors
    
    def _generate_suggestions(self, image: torch.Tensor) -> List[str]:
        """Generate improvement suggestions."""
        prompt = """Based on this image, suggest improvements for:
        1. Visual composition
        2. Brand alignment
        3. Engagement potential
        4. Message clarity
        5. Call-to-action effectiveness"""
        result = self._run_inference(image, prompt)
        return [line.strip() for line in result.split('\n') if line.strip()]
    
    def _get_reasoning_steps(self, image: torch.Tensor) -> List[str]:
        """Get step-by-step reasoning about the image's effectiveness."""
        prompt = """Analyze this image's effectiveness step by step:
        1. What immediately catches attention?
        2. How does it convey its message?
        3. What emotional response does it evoke?
        4. How well does it align with brand goals?
        5. What makes it memorable or shareable?"""
        result = self._run_inference(image, prompt)
        return [line.strip() for line in result.split('\n') if line.strip()]
