"""
Campaign Validator
Implements the checker part of maker-checker pattern for campaign validation.
"""

import logging
from typing import Dict, List, Optional
import asyncio
from datetime import datetime

from ..utils.deepseek_integration import DeepSeekIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CampaignValidator:
    """Validates marketing campaigns."""
    
    def __init__(self):
        """Initialize the validator."""
        self.deepseek = DeepSeekIntegration()
        self.validation_history: Dict[str, List[Dict]] = {}
    
    async def validate_campaign(
        self,
        campaign: Dict,
        context: Optional[Dict] = None
    ) -> Dict:
        """Validate a campaign before execution."""
        try:
            campaign_id = campaign['campaign_id']
            validation_result = {
                'campaign_id': campaign_id,
                'timestamp': datetime.now().isoformat(),
                'validations': {}
            }
            
            # Resource Validation
            resources = await self._validate_resources(campaign)
            validation_result['validations']['resources'] = resources
            
            # Platform Requirements
            platform_reqs = await self._validate_platform_requirements(campaign)
            validation_result['validations']['platform_requirements'] = platform_reqs
            
            # Campaign Viability
            viability = await self._assess_campaign_viability(campaign)
            validation_result['validations']['viability'] = viability
            
            # Budget Compliance
            budget = await self._validate_budget(campaign)
            validation_result['validations']['budget'] = budget
            
            # Store validation history
            if campaign_id not in self.validation_history:
                self.validation_history[campaign_id] = []
            self.validation_history[campaign_id].append(validation_result)
            
            # Overall validation decision
            validation_result['is_valid'] = all([
                resources['passed'],
                platform_reqs['passed'],
                viability['passed'],
                budget['passed']
            ])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Campaign validation failed: {e}")
            raise
    
    async def _validate_resources(self, campaign: Dict) -> Dict:
        """Validate resource availability for campaign."""
        required_resources = self._calculate_required_resources(campaign)
        available_resources = await self._get_available_resources()
        
        resource_check = {
            'passed': True,
            'issues': []
        }
        
        for resource, required in required_resources.items():
            if required > available_resources.get(resource, 0):
                resource_check['passed'] = False
                resource_check['issues'].append({
                    'resource': resource,
                    'required': required,
                    'available': available_resources.get(resource, 0)
                })
        
        return resource_check
    
    async def _validate_platform_requirements(self, campaign: Dict) -> Dict:
        """Validate campaign meets platform-specific requirements."""
        platform_check = {
            'passed': True,
            'issues': []
        }
        
        for platform in campaign['platforms']:
            requirements = await self._get_platform_requirements(platform)
            for req in requirements:
                if not self._meets_requirement(campaign, req):
                    platform_check['passed'] = False
                    platform_check['issues'].append({
                        'platform': platform,
                        'requirement': req['type'],
                        'details': req['details']
                    })
        
        return platform_check
    
    async def _assess_campaign_viability(self, campaign: Dict) -> Dict:
        """Assess overall campaign viability using DeepSeek."""
        analysis = await self.deepseek.analyze_text(
            str(campaign),
            'campaign_viability'
        )
        
        return {
            'passed': analysis['viability_score'] >= 0.7,
            'score': analysis['viability_score'],
            'insights': analysis['viability_insights']
        }
    
    async def _validate_budget(self, campaign: Dict) -> Dict:
        """Validate campaign budget allocation."""
        budget_check = {
            'passed': True,
            'issues': []
        }
        
        allocated = self._calculate_budget_allocation(campaign)
        available = await self._get_available_budget()
        
        if allocated > available:
            budget_check['passed'] = False
            budget_check['issues'].append({
                'type': 'budget_exceeded',
                'allocated': allocated,
                'available': available
            })
        
        return budget_check
    
    def _calculate_required_resources(self, campaign: Dict) -> Dict:
        """Calculate required resources for campaign."""
        return {
            'content_creators': len(campaign['platforms']) * 2,
            'analysts': len(campaign['platforms']),
            'storage_gb': len(campaign['platforms']) * 5
        }
    
    async def _get_available_resources(self) -> Dict:
        """Get currently available resources."""
        # This would typically fetch from a resource management system
        return {
            'content_creators': 10,
            'analysts': 5,
            'storage_gb': 100
        }
    
    async def _get_platform_requirements(self, platform: str) -> List[Dict]:
        """Get requirements for specific platform."""
        # This would typically fetch from a database or config
        return [
            {
                'type': 'content_format',
                'details': {'supported': ['video', 'image'] if platform == 'instagram' else ['video']}
            },
            {
                'type': 'duration',
                'details': {'max': 60 if platform == 'tiktok' else 90}
            }
        ]
    
    def _meets_requirement(self, campaign: Dict, requirement: Dict) -> bool:
        """Check if campaign meets a specific requirement."""
        if requirement['type'] == 'content_format':
            return all(ct in requirement['details']['supported'] 
                      for ct in campaign.get('content_types', []))
        elif requirement['type'] == 'duration':
            return campaign.get('duration', 0) <= requirement['details']['max']
        return True
    
    def _calculate_budget_allocation(self, campaign: Dict) -> float:
        """Calculate total budget allocation for campaign."""
        base_cost = 1000  # Base cost per platform
        return len(campaign['platforms']) * base_cost
