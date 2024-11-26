"""
Viral Content Creator Agent
Creates viral content using DeepSeek-V2 model.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import copy

from ..utils.deepseek_integration import DeepSeekIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ViralContentCreator:
    """Agent that creates viral content using DeepSeek-V2."""
    
    def __init__(self):
        """Initialize the viral content creator."""
        self.deepseek = DeepSeekIntegration()
        self.platform_specs = {
            'tiktok': {
                'max_duration': 60,
                'optimal_duration': 30,
                'content_types': ['video', 'music'],
                'aspect_ratio': '9:16'
            },
            'instagram': {
                'max_duration': 60,
                'optimal_duration': 30,
                'content_types': ['video', 'image', 'carousel'],
                'aspect_ratio': '1:1'
            },
            'youtube_shorts': {
                'max_duration': 60,
                'optimal_duration': 45,
                'content_types': ['video'],
                'aspect_ratio': '9:16'
            }
        }
        self.content_history: Dict[str, List[Dict]] = {}
        
    async def create_viral_content(
        self,
        trends: List,
        industry: str,
        target_platform: str
    ) -> Dict:
        """Create viral content based on trends."""
        try:
            # Analyze trends for content opportunities
            opportunities = await self._analyze_content_opportunities(
                trends,
                industry,
                target_platform
            )
            
            # Generate content variations
            content_variations = []
            for opportunity in opportunities:
                variation = await self._generate_content_variation(
                    opportunity,
                    target_platform
                )
                content_variations.append(variation)
            
            # Select best content variation
            best_content = await self._select_best_content(
                content_variations,
                industry,
                target_platform
            )
            
            # Prepare content for validation
            content_package = await self._prepare_content_package(
                best_content,
                industry,
                target_platform
            )
            
            # Update content history
            await self._update_content_history(content_package)
            
            return content_package
            
        except Exception as e:
            logger.error(f"Failed to create viral content: {e}")
            raise
    
    async def refine_content(
        self,
        content: Dict,
        validation_feedback: Dict
    ) -> Dict:
        """Refine content based on validation feedback."""
        try:
            # Analyze validation feedback
            improvement_areas = await self._analyze_validation_feedback(
                validation_feedback
            )
            
            # Generate improvement prompt
            improvement_prompt = await self._create_improvement_prompt(
                content,
                improvement_areas
            )
            
            # Generate refined content
            refined_texts = await self.deepseek.generate_content(
                improvement_prompt,
                max_length=1000,
                temperature=0.7,
                num_return_sequences=3
            )
            
            # Score and select best refinement
            best_refinement = await self._select_best_refinement(
                refined_texts,
                content,
                validation_feedback
            )
            
            # Prepare refined content package
            content_package = await self._prepare_content_package(
                best_refinement,
                content['industry'],
                content['platform']
            )
            
            return content_package
            
        except Exception as e:
            logger.error(f"Failed to refine content: {e}")
            raise
    
    async def _analyze_content_opportunities(
        self,
        trends: List,
        industry: str,
        platform: str
    ) -> List[Dict]:
        """Analyze trends for content opportunities using DeepSeek."""
        opportunities = []
        
        for trend in trends:
            # Analyze trend with DeepSeek
            analysis = await self.deepseek.analyze_text(
                str(trend),
                'trend_fit',
                {'industry': industry, 'platform': platform}
            )
            
            if float(analysis.get('trend_alignment_score', 0)) >= 0.7:
                opportunities.append({
                    'trend': trend,
                    'analysis': analysis,
                    'content_angles': await self._generate_content_angles(
                        trend,
                        industry,
                        platform
                    )
                })
        
        return sorted(
            opportunities,
            key=lambda x: float(x['analysis'].get('trend_alignment_score', 0)),
            reverse=True
        )
    
    async def _generate_content_variation(
        self,
        opportunity: Dict,
        platform: str
    ) -> Dict:
        """Generate a content variation using DeepSeek."""
        platform_spec = self.platform_specs[platform]
        
        # Create content generation prompt
        prompt = await self._create_content_prompt(
            opportunity,
            platform_spec
        )
        
        # Generate content elements
        generated_texts = await self.deepseek.generate_content(
            prompt,
            max_length=1000,
            temperature=0.8,
            num_return_sequences=1
        )
        
        elements = await self._parse_generated_content(
            generated_texts[0],
            platform_spec
        )
        
        return {
            'trend_id': opportunity['trend'].trend_id,
            'platform': platform,
            'content_type': platform_spec['content_types'][0],
            'elements': elements,
            'specs': {
                'duration': platform_spec['optimal_duration'],
                'aspect_ratio': platform_spec['aspect_ratio']
            }
        }
    
    async def _select_best_content(
        self,
        variations: List[Dict],
        industry: str,
        platform: str
    ) -> Dict:
        """Select best content using DeepSeek evaluation."""
        scores = []
        
        for variation in variations:
            # Evaluate content
            evaluation = await self.deepseek.evaluate_content(
                str(variation['elements']),
                {
                    'virality': 0.4,
                    'engagement': 0.3,
                    'brand_safety': 0.2,
                    'platform_fit': 0.1
                },
                {
                    'industry': industry,
                    'platform': platform
                }
            )
            
            scores.append((evaluation['overall_score'], variation))
        
        return max(scores, key=lambda x: x[0])[1]
    
    async def _create_content_prompt(
        self,
        opportunity: Dict,
        platform_spec: Dict
    ) -> str:
        """Create a prompt for content generation."""
        return f"""
            Create viral content for {platform_spec['content_types'][0]} format.
            
            Trend Information:
            {opportunity['trend']}
            
            Content Angles:
            {opportunity['content_angles']}
            
            Platform Specifications:
            - Format: {platform_spec['content_types'][0]}
            - Optimal Duration: {platform_spec['optimal_duration']} seconds
            - Aspect Ratio: {platform_spec['aspect_ratio']}
            
            Generate engaging content that includes:
            1. Attention-grabbing hook
            2. Main content body
            3. Call to action
            4. Relevant hashtags
            
            Make it viral, edgy, and highly shareable while maintaining brand safety.
            """
    
    async def _parse_generated_content(
        self,
        generated_text: str,
        platform_spec: Dict
    ) -> Dict:
        """Parse generated content into structured elements."""
        # TODO: Implement more sophisticated parsing
        sections = generated_text.split('\n\n')
        
        return {
            'hook': sections[0] if len(sections) > 0 else '',
            'main_content': sections[1] if len(sections) > 1 else '',
            'call_to_action': sections[2] if len(sections) > 2 else '',
            'hashtags': sections[3] if len(sections) > 3 else ''
        }
    
    async def _create_improvement_prompt(
        self,
        content: Dict,
        improvements: List[Dict]
    ) -> str:
        """Create a prompt for content improvement."""
        improvement_points = "\n".join(
            f"- {imp['metric']}: {', '.join(imp['suggestions'])}"
            for imp in improvements
        )
        
        return f"""
            Improve the following content based on feedback:
            
            Original Content:
            {content['elements']}
            
            Improvement Areas:
            {improvement_points}
            
            Generate an improved version that:
            1. Addresses all feedback points
            2. Maintains the original message
            3. Enhances viral potential
            4. Fits platform: {content['platform']}
            
            Keep the content edgy and engaging while implementing improvements.
            """
    
    async def _select_best_refinement(
        self,
        refinements: List[str],
        original_content: Dict,
        validation_feedback: Dict
    ) -> Dict:
        """Select the best content refinement."""
        scores = []
        
        for refinement in refinements:
            # Evaluate refinement
            evaluation = await self.deepseek.evaluate_content(
                refinement,
                {
                    'improvement': 0.4,
                    'originality': 0.3,
                    'engagement': 0.3
                },
                {
                    'original_content': original_content,
                    'feedback': validation_feedback
                }
            )
            
            scores.append((evaluation['overall_score'], refinement))
        
        best_refinement = max(scores, key=lambda x: x[0])[1]
        
        return {
            'trend_id': original_content['trend_id'],
            'platform': original_content['platform'],
            'content_type': original_content['content_type'],
            'elements': await self._parse_generated_content(
                best_refinement,
                self.platform_specs[original_content['platform']]
            ),
            'specs': original_content['specs']
        }
    
    async def _prepare_content_package(
        self,
        content: Dict,
        industry: str,
        platform: str
    ) -> Dict:
        """Prepare content package for validation."""
        return {
            'content_id': str(uuid.uuid4()),
            'trend_id': content['trend_id'],
            'industry': industry,
            'platform': platform,
            'content_type': content['content_type'],
            'elements': content['elements'],
            'specs': content['specs'],
            'metadata': {
                'creation_timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'model': 'deepseek-v2'
            }
        }
    
    async def _update_content_history(self, content: Dict):
        """Update content creation history."""
        if content['trend_id'] not in self.content_history:
            self.content_history[content['trend_id']] = []
        
        self.content_history[content['trend_id']].append({
            'content_id': content['content_id'],
            'timestamp': datetime.now(),
            'platform': content['platform'],
            'content_type': content['content_type']
        })
        
        # Keep only last 30 days of history
        cutoff = datetime.now() - timedelta(days=30)
        self.content_history[content['trend_id']] = [
            c for c in self.content_history[content['trend_id']]
            if c['timestamp'] > cutoff
        ]
