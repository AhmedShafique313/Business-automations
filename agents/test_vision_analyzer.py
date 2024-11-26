"""Test script for vision analyzer using LLaVA-CoT."""

import os
import logging
from intelligence.vision.vision_analyzer import VisionAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vision_analyzer():
    """Test vision analyzer functionality."""
    
    # Path to LLaVA-CoT model checkpoint
    model_path = os.path.join(
        os.path.dirname(__file__),
        'intelligence/vision/llava-cot/checkpoints/llava-v1.5-13b'
    )
    
    # Initialize vision analyzer
    try:
        analyzer = VisionAnalyzer(model_path)
        logger.info("Successfully initialized vision analyzer")
    except Exception as e:
        logger.error(f"Failed to initialize vision analyzer: {e}")
        return
    
    # Test image path (replace with actual test image)
    test_image = os.path.join(
        os.path.dirname(__file__),
        'test_data/test_image.jpg'
    )
    
    # Create test directory if it doesn't exist
    os.makedirs(os.path.dirname(test_image), exist_ok=True)
    
    try:
        # Analyze test image
        analysis = analyzer.analyze_image(test_image)
        
        # Print results
        logger.info("\n=== Vision Analysis Results ===")
        logger.info(f"\nContent Description:\n{analysis.content_description}")
        
        logger.info("\nVisual Elements:")
        for element in analysis.visual_elements:
            logger.info(f"- {element}")
        
        logger.info("\nBrand Elements:")
        for element in analysis.brand_elements:
            logger.info(f"- {element}")
        
        logger.info("\nEngagement Factors:")
        for factor in analysis.engagement_factors:
            logger.info(f"- {factor['factor']}: {factor['score']}/10")
        
        logger.info("\nImprovement Suggestions:")
        for suggestion in analysis.improvement_suggestions:
            logger.info(f"- {suggestion}")
        
        logger.info("\nReasoning Steps:")
        for step in analysis.reasoning_steps:
            logger.info(f"- {step}")
            
        logger.info("\nVision analysis test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during vision analysis: {e}")

if __name__ == "__main__":
    test_vision_analyzer()
