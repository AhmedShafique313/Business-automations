"""
Content Validator
Implements the checker part of maker-checker pattern for content validation.
"""

import logging
from typing import Dict, List, Optional
import asyncio

from ..utils.deepseek_integration import DeepSeekIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentValidator:
    """Validates content created by ViralContentCreator."""
    
    def __init__(self):
        """Initialize the validator."""
        self.deepseek = DeepSeekIntegration()
        self.validation_history: Dict[str, List[Dict]] = {}
        
    async def validate_content(
        self,
        content: Dict,
        platform: str,
        content_type: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Validate content against multiple criteria."""
        try:
            content_id = content.get('content_id')
            validation_result = {
                'content_id': content_id,
                'platform': platform,
                'content_type': content_type,
                'timestamp': datetime.now().isoformat(),
                'validations': {}
            }
            
            # Quality Check
            quality_score = await self._check_content_quality(content)
            validation_result['validations']['quality'] = quality_score
            
            # Platform Compliance
            compliance = await self._check_platform_compliance(content, platform)
            validation_result['validations']['compliance'] = compliance
            
            # Brand Safety
            safety_score = await self._check_brand_safety(content)
            validation_result['validations']['brand_safety'] = safety_score
            
            # Engagement Potential
            engagement_score = await self._predict_engagement(content, platform)
            validation_result['validations']['engagement'] = engagement_score
            
            # Store validation history
            if content_id not in self.validation_history:
                self.validation_history[content_id] = []
            self.validation_history[content_id].append(validation_result)
            
            # Overall validation decision
            validation_result['is_valid'] = all([
                quality_score['passed'],
                compliance['passed'],
                safety_score['passed'],
                engagement_score['passed']
            ])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            raise
    
    async def _check_content_quality(self, content: Dict) -> Dict:
        """Check content quality using DeepSeek."""
        analysis = await self.deepseek.analyze_text(
            content['text'],
            'content_quality'
        )
        return {
            'passed': analysis['quality_score'] >= 0.7,
            'score': analysis['quality_score'],
            'feedback': analysis['quality_feedback']
        }
    
    async def _check_platform_compliance(
        self,
        content: Dict,
        platform: str
    ) -> Dict:
        """Check if content complies with platform guidelines."""
        platform_rules = await self._get_platform_rules(platform)
        violations = []
        
        for rule in platform_rules:
            if not self._check_rule_compliance(content, rule):
                violations.append(rule)
        
        return {
            'passed': len(violations) == 0,
            'violations': violations
        }
    
    async def _check_brand_safety(self, content: Dict) -> Dict:
        """Check content for brand safety concerns."""
        analysis = await self.deepseek.analyze_text(
            content['text'],
            'brand_safety'
        )
        return {
            'passed': analysis['safety_score'] >= 0.8,
            'score': analysis['safety_score'],
            'concerns': analysis['safety_concerns']
        }
    
    async def _predict_engagement(
        self,
        content: Dict,
        platform: str
    ) -> Dict:
        """Predict potential engagement metrics."""
        analysis = await self.deepseek.analyze_text(
            content['text'],
            'engagement_prediction'
        )
        return {
            'passed': analysis['engagement_score'] >= 0.6,
            'score': analysis['engagement_score'],
            'metrics': analysis['predicted_metrics']
        }
    
    async def _get_platform_rules(self, platform: str) -> List[Dict]:
        """Get platform-specific content rules."""
        # This would typically fetch from a database or config
        return [
            {'type': 'length', 'max': 2200 if platform == 'instagram' else 1000},
            {'type': 'hashtags', 'max': 30 if platform == 'instagram' else 10},
            {'type': 'mentions', 'max': 20},
            {'type': 'links', 'allowed': platform != 'instagram'}
        ]
    
    def _check_rule_compliance(self, content: Dict, rule: Dict) -> bool:
        """Check if content complies with a specific rule."""
        if rule['type'] == 'length':
            return len(content['text']) <= rule['max']
        elif rule['type'] == 'hashtags':
            return content['text'].count('#') <= rule['max']
        elif rule['type'] == 'mentions':
            return content['text'].count('@') <= rule['max']
        elif rule['type'] == 'links':
            has_links = 'http://' in content['text'] or 'https://' in content['text']
            return has_links == rule['allowed']
        return True
