"""Engagement Agent for managing lead interactions.

This agent is responsible for:
- Managing multi-channel outreach
- Creating personalized engagement plans
- Implementing maker-checker workflow
- Learning from interaction patterns
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
import json
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry
from redis import Redis
from prometheus_client import Counter, Histogram, Gauge
from circuitbreaker import circuit

from config_manager import ConfigManager
from utils.email_manager import EmailManager
from utils.social_media import SocialMediaManager
from utils.asana_client import AsanaClient
from utils.error_handler import handle_error
from agents.content_agent import ContentAgent
from utils.metrics_collector import MetricsCollector
from utils.memory_manager import MemoryManager

# Prometheus metrics
ENGAGEMENT_COUNTER = Counter('engagement_attempts_total', 'Total number of engagement attempts')
ENGAGEMENT_SUCCESS = Counter('engagement_success_total', 'Total number of successful engagements')
ENGAGEMENT_TIME = Histogram('engagement_duration_seconds', 'Time spent on engagement activities')
ACTIVE_PLANS = Gauge('active_engagement_plans', 'Number of active engagement plans')

@dataclass(frozen=True)
class EngagementPlan:
    """Immutable data structure for engagement planning."""
    lead_id: str
    channels: tuple[str, ...]  # Using tuple for immutability
    priority: int
    frequency: str  # daily, weekly, monthly
    next_touchpoint: datetime
    content_type: tuple[str, ...]  # Using tuple for immutability
    approval_status: str = 'pending'
    engagement_metrics: Dict = field(default_factory=dict)
    last_interaction: Optional[datetime] = None
    interaction_history: tuple = field(default_factory=tuple)  # Using tuple for immutability
    
    def __post_init__(self):
        """Validate plan data after initialization."""
        if not self.lead_id:
            raise ValueError("Lead ID is required")
        if not self.channels:
            raise ValueError("At least one channel is required")
        if self.priority not in range(1, 6):
            raise ValueError("Priority must be between 1 and 5")
        if self.frequency not in ['daily', 'weekly', 'monthly']:
            raise ValueError("Invalid frequency")

class EngagementAgent:
    """Agent responsible for lead engagement and interaction management."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.email_manager = EmailManager()
        self.social_manager = SocialMediaManager()
        self.asana_client = AsanaClient()
        self.content_agent = ContentAgent()
        self.logger = logging.getLogger(__name__)
        self.metrics = MetricsCollector()
        self.memory_manager = MemoryManager()
        
        # Initialize Redis for caching
        self.redis = Redis(
            host=self.config.get('redis_host', 'localhost'),
            port=self.config.get('redis_port', 6379),
            db=self.config.get('redis_db', 1)  # Different db than researcher
        )
        
        # Configure rate limits
        self.email_limit = self.config.get('rate_limits', {}).get('email', 50)
        self.social_limit = self.config.get('rate_limits', {}).get('social', 30)
        
        # Circuit breaker configs
        self.error_threshold = self.config.get('error_threshold', 5)
        self.recovery_timeout = self.config.get('recovery_timeout', 300)
        
    @ENGAGEMENT_TIME.time()
    async def create_engagement_plan(self, lead_profile: Dict) -> EngagementPlan:
        """Create a personalized engagement plan based on lead profile."""
        try:
            # Determine optimal channels and frequency
            channels, frequency = await self._analyze_engagement_preferences(lead_profile)
            
            # Calculate priority based on lead score and engagement history
            priority = await self._calculate_priority(lead_profile)
            
            # Create engagement plan
            plan = EngagementPlan(
                lead_id=lead_profile['id'],
                channels=tuple(channels),
                priority=priority,
                frequency=frequency,
                next_touchpoint=self._calculate_next_touchpoint(frequency),
                content_type=tuple(self._determine_content_types(channels)),
                engagement_metrics={
                    'email_open_rate': 0.0,
                    'response_rate': 0.0,
                    'social_engagement': 0.0,
                    'conversion_probability': await self._estimate_conversion_probability(lead_profile)
                }
            )
            
            # Cache the plan
            await self._cache_plan(plan)
            
            # Create Asana task for approval
            await self._create_approval_task(plan)
            
            # Update metrics
            ACTIVE_PLANS.inc()
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Failed to create engagement plan: {str(e)}")
            self.metrics.record_error('plan_creation_failure', str(e))
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    @ENGAGEMENT_TIME.time()
    async def execute_engagement_plan(self, plan: EngagementPlan) -> bool:
        """Execute approved engagement plan across channels."""
        if plan.approval_status != 'approved':
            self.logger.warning(f"Cannot execute unapproved plan for lead {plan.lead_id}")
            return False
            
        ENGAGEMENT_COUNTER.inc()
        
        try:
            success = True
            interaction_data = {}
            
            # Execute engagement actions for each channel concurrently
            tasks = []
            for channel in plan.channels:
                if channel == 'email':
                    tasks.append(self._send_email_safely(plan))
                elif channel == 'social':
                    tasks.append(self._engage_social_safely(plan))
                else:
                    self.logger.warning(f"Unsupported channel: {channel}")
                    continue
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Channel execution failed: {str(result)}")
                    success = False
                else:
                    channel = plan.channels[i]
                    interaction_data[channel] = result
                    
            # Record interaction and update metrics
            if success:
                ENGAGEMENT_SUCCESS.inc()
                plan = await self._record_interaction(plan, interaction_data)
                plan = await self._update_engagement_metrics(plan, interaction_data)
                await self._cache_plan(plan)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Plan execution failed: {str(e)}")
            self.metrics.record_error('plan_execution_failure', str(e))
            return False
        finally:
            # Clean up resources
            self.memory_manager.clear_execution_memory()
    
    @circuit(failure_threshold=5, recovery_timeout=300)
    async def _send_email_safely(self, plan: EngagementPlan) -> Dict:
        """Safely send email with circuit breaker and error handling."""
        try:
            # Check rate limit in Redis
            rate_key = f"email_rate:{datetime.now().strftime('%Y-%m-%d-%H')}"
            current_rate = self.redis.get(rate_key) or 0
            
            if int(current_rate) >= self.email_limit:
                raise Exception("Email rate limit exceeded")
            
            content = await self.content_agent.generate_email_content(plan.lead_id)
            result = await self.email_manager.send_email(
                recipient_id=plan.lead_id,
                content=content,
                template_id=await self._select_email_template(plan)
            )
            
            # Update rate limit
            self.redis.incr(rate_key)
            self.redis.expire(rate_key, 3600)  # Expire after 1 hour
            
            return {'status': 'success', 'details': result}
        except Exception as e:
            self.logger.error(f"Email sending failed: {str(e)}")
            self.metrics.record_error('email_failure', str(e))
            return {'status': 'failed', 'error': str(e)}
    
    @circuit(failure_threshold=5, recovery_timeout=300)
    async def _engage_social_safely(self, plan: EngagementPlan) -> Dict:
        """Safely engage on social media with circuit breaker."""
        try:
            # Check rate limit in Redis
            rate_key = f"social_rate:{datetime.now().strftime('%Y-%m-%d-%H')}"
            current_rate = self.redis.get(rate_key) or 0
            
            if int(current_rate) >= self.social_limit:
                raise Exception("Social media rate limit exceeded")
            
            content = await self.content_agent.generate_social_content(plan.lead_id)
            result = await self.social_manager.post_content(
                platform=await self._select_social_platform(plan),
                content=content,
                lead_id=plan.lead_id
            )
            
            # Update rate limit
            self.redis.incr(rate_key)
            self.redis.expire(rate_key, 3600)  # Expire after 1 hour
            
            return {'status': 'success', 'details': result}
        except Exception as e:
            self.logger.error(f"Social engagement failed: {str(e)}")
            self.metrics.record_error('social_failure', str(e))
            return {'status': 'failed', 'error': str(e)}
    
    @lru_cache(maxsize=1000)
    async def _analyze_engagement_preferences(self, lead_profile: Dict) -> Tuple[List[str], str]:
        """Analyze lead profile to determine optimal engagement channels and frequency."""
        channels = []
        
        # Determine channels based on available contact info and preferences
        if lead_profile.get('email'):
            channels.append('email')
        if any(lead_profile.get(social) for social in ['linkedin', 'twitter', 'instagram']):
            channels.append('social')
            
        # Determine frequency based on engagement score and business type
        score = lead_profile.get('engagement_score', 0.0)
        if score > 0.8:
            frequency = 'daily'
        elif score > 0.5:
            frequency = 'weekly'
        else:
            frequency = 'monthly'
            
        return channels, frequency
    
    async def _cache_plan(self, plan: EngagementPlan) -> None:
        """Cache engagement plan in Redis."""
        try:
            cache_key = f"plan:{plan.lead_id}"
            self.redis.setex(
                cache_key,
                self.config.get('plan_cache_ttl', 86400),
                json.dumps(plan.__dict__)
            )
        except Exception as e:
            self.logger.error(f"Failed to cache plan: {str(e)}")
    
    async def _record_interaction(self, plan: EngagementPlan, interaction_data: Dict) -> EngagementPlan:
        """Record interaction details in plan history."""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'channels': list(interaction_data.keys()),
            'results': interaction_data,
            'plan_id': id(plan)
        }
        
        # Create new plan with updated history (immutable)
        return replace(
            plan,
            interaction_history=plan.interaction_history + (interaction,),
            last_interaction=datetime.now()
        )
    
    async def _update_engagement_metrics(self, plan: EngagementPlan, interaction_data: Dict) -> EngagementPlan:
        """Update engagement metrics based on interaction results."""
        metrics = dict(plan.engagement_metrics)
        
        # Update email metrics
        if 'email' in interaction_data:
            result = interaction_data['email']
            if result['status'] == 'success':
                metrics['email_open_rate'] = await self._calculate_open_rate(plan)
                metrics['response_rate'] = await self._calculate_response_rate(plan)
                
        # Update social metrics
        if 'social' in interaction_data:
            result = interaction_data['social']
            if result['status'] == 'success':
                metrics['social_engagement'] = await self._calculate_social_engagement(plan)
                
        # Update conversion probability
        metrics['conversion_probability'] = await self._estimate_conversion_probability_from_engagement(plan)
        
        # Create new plan with updated metrics (immutable)
        return replace(plan, engagement_metrics=metrics)
    
    async def _calculate_open_rate(self, plan: EngagementPlan) -> float:
        """Calculate email open rate based on interaction history."""
        # TO DO: implement calculation logic
        return 0.0
    
    async def _calculate_response_rate(self, plan: EngagementPlan) -> float:
        """Calculate email response rate based on interaction history."""
        # TO DO: implement calculation logic
        return 0.0
    
    async def _calculate_social_engagement(self, plan: EngagementPlan) -> float:
        """Calculate social engagement rate based on interaction history."""
        # TO DO: implement calculation logic
        return 0.0
    
    async def _estimate_conversion_probability(self, lead_profile: Dict) -> float:
        """Estimate probability of conversion based on lead profile."""
        # TO DO: implement calculation logic
        return 0.0
    
    async def _estimate_conversion_probability_from_engagement(self, plan: EngagementPlan) -> float:
        """Estimate conversion probability based on engagement history."""
        # TO DO: implement calculation logic
        return 0.0
    
    async def _select_email_template(self, plan: EngagementPlan) -> str:
        """Select email template based on engagement plan."""
        # TO DO: implement selection logic
        return ""
    
    async def _select_social_platform(self, plan: EngagementPlan) -> str:
        """Select social platform based on engagement plan."""
        # TO DO: implement selection logic
        return ""
