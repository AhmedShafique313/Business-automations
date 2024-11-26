"""Business Development Orchestrator.

This module orchestrates the entire business development process by:
1. Coordinating between different agents
2. Managing the maker-checker workflow
3. Tracking performance metrics
4. Learning from successful patterns
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from dataclasses import asdict

from config_manager import ConfigManager
from agents.researcher_agent import ResearcherAgent, LeadProfile
from agents.engagement_agent import EngagementAgent
from agents.content_agent import ContentAgent
from utils.asana_client import AsanaClient
from utils.metrics_tracker import MetricsTracker

class BusinessOrchestrator:
    """Orchestrates the business development process."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.researcher = ResearcherAgent()
        self.engagement = EngagementAgent()
        self.content = ContentAgent()
        self.asana = AsanaClient()
        self.metrics = MetricsTracker()
        self.logger = logging.getLogger(__name__)
        
    async def run_business_development(self, business_type: str, location: str):
        """Main business development loop."""
        try:
            # 1. Research and find leads
            leads = await self._research_market(business_type, location)
            
            # 2. Create engagement plans
            plans = await self._create_engagement_plans(leads)
            
            # 3. Execute approved plans
            await self._execute_engagement_plans(plans)
            
            # 4. Track and analyze results
            await self._analyze_performance()
            
        except Exception as e:
            self.logger.error(f"Business development failed: {str(e)}")
            raise
            
    async def _research_market(self, business_type: str, location: str) -> List[LeadProfile]:
        """Research and profile potential leads."""
        self.logger.info(f"Starting market research for {business_type} in {location}")
        
        # Create Asana project for tracking
        project_id = self.asana.create_project(f"Market Research - {business_type} {location}")
        
        # Research leads
        leads = self.researcher.research_target_market(business_type, location)
        
        # Create Asana tasks for lead verification
        for lead in leads:
            task_data = {
                'lead': asdict(lead),
                'status': 'pending_verification',
                'created_at': datetime.now().isoformat()
            }
            self.asana.create_task(project_id, f"Verify Lead: {lead.business_name}", task_data)
        
        # Wait for lead verification
        verified_leads = []
        for lead in leads:
            if await self._wait_for_verification(lead):
                verified_leads.append(lead)
                
        return verified_leads
    
    async def _create_engagement_plans(self, leads: List[LeadProfile]) -> List[Dict]:
        """Create personalized engagement plans for leads."""
        plans = []
        
        for lead in leads:
            # Generate plan
            plan = self.engagement.create_engagement_plan(lead)
            
            # Create content for each channel
            plan['content'] = await self._generate_content(lead, plan['channels'])
            
            # If plan needs approval, create Asana task
            if plan['approval_required']:
                task_data = {
                    'plan': plan,
                    'lead': asdict(lead),
                    'status': 'pending_approval'
                }
                self.asana.create_task(
                    plan['asana_task_id'],
                    f"Approve Engagement Plan: {lead.business_name}",
                    task_data
                )
                
            plans.append(plan)
            
        return plans
    
    async def _generate_content(self, lead: LeadProfile, channels: List[str]) -> Dict:
        """Generate content for each channel."""
        content = {}
        
        if 'email' in channels:
            content['email'] = self.content.generate_email_content(lead, 'initial_contact')
            
        if any(channel in channels for channel in ['instagram', 'facebook', 'linkedin']):
            for platform in ['instagram', 'facebook', 'linkedin']:
                if platform in channels:
                    content[platform] = self.content.generate_social_post(
                        platform,
                        f"Business Development for {lead.business_type}",
                        {
                            'industry': lead.business_type,
                            'location': lead.location,
                            'interests': ['business growth', 'local business', lead.business_type]
                        }
                    )
                    
        return content
    
    async def _execute_engagement_plans(self, plans: List[Dict]):
        """Execute approved engagement plans."""
        for plan in plans:
            if plan['status'] == 'pending_approval':
                approved = await self._wait_for_approval(plan)
                if not approved:
                    continue
                    
            # Execute each step in the sequence
            for step in plan['sequence']:
                if step['delay'] > 0:
                    await asyncio.sleep(step['delay'] * 86400)  # Convert days to seconds
                    
                success, message = self.engagement.execute_engagement_step(
                    plan['lead_id'],
                    step
                )
                
                if not success:
                    self.logger.warning(f"Step failed for {plan['lead_id']}: {message}")
                    await self._handle_failed_step(plan, step, message)
                    
    async def _analyze_performance(self):
        """Analyze performance and update strategies."""
        # Get metrics for all content and engagements
        metrics = self.metrics.get_all_metrics()
        
        # Analyze content performance
        for content_id, content_metrics in metrics['content'].items():
            analysis = self.content.analyze_content_performance(content_id, content_metrics)
            self.metrics.store_analysis(content_id, analysis)
            
        # Analyze engagement performance
        for lead_id, engagement_metrics in metrics['engagement'].items():
            self.engagement.learn_from_engagement(lead_id, engagement_metrics)
            
        # Update strategies based on performance
        await self._update_strategies(metrics)
        
    async def _wait_for_verification(self, lead: LeadProfile) -> bool:
        """Wait for lead verification in Asana."""
        task = self.asana.get_task_by_lead(lead)
        
        while True:
            status = self.asana.get_task_status(task['gid'])
            if status == 'verified':
                return True
            elif status == 'rejected':
                return False
                
            await asyncio.sleep(300)  # Check every 5 minutes
            
    async def _wait_for_approval(self, plan: Dict) -> bool:
        """Wait for plan approval in Asana."""
        while True:
            status = self.asana.get_task_status(plan['asana_task_id'])
            if status == 'approved':
                return True
            elif status == 'rejected':
                return False
                
            await asyncio.sleep(300)  # Check every 5 minutes
            
    async def _handle_failed_step(self, plan: Dict, step: Dict, error_message: str):
        """Handle failed engagement steps."""
        task_data = {
            'plan': plan,
            'step': step,
            'error': error_message,
            'status': 'failed'
        }
        
        self.asana.create_task(
            plan['asana_task_id'],
            f"Failed Step: {step['channel']} - {step['type']}",
            task_data
        )
        
    async def _update_strategies(self, metrics: Dict):
        """Update engagement and content strategies based on performance."""
        # Update content preferences
        if metrics['content']:
            best_performing = self.metrics.get_best_performing_content(metrics['content'])
            self.content.update_content_strategies(best_performing)
            
        # Update engagement strategies
        if metrics['engagement']:
            best_practices = self.metrics.get_best_engagement_practices(metrics['engagement'])
            self.engagement.update_engagement_strategies(best_practices)
            
        # Update configuration
        self.config.update_strategies({
            'content': best_performing,
            'engagement': best_practices
        })
