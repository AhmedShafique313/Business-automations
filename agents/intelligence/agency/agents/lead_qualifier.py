"""
Lead Qualification Agent
Analyzes and scores potential leads using ML-based qualification criteria.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid
import numpy as np
from transformers import pipeline

from ..utils.model_manager import ModelManager
from ..storage.storage_manager import StorageManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LeadProfile:
    """Represents a potential lead's profile and engagement data."""
    id: str
    source: str  # Where the lead came from
    first_touch_point: datetime
    engagement_history: List[Dict]
    demographic_data: Dict
    behavior_metrics: Dict
    qualification_score: float = 0.0
    status: str = "new"  # new, qualified, disqualified, converted

class LeadQualifier:
    """Agent that qualifies leads using ML-based scoring."""
    
    def __init__(self):
        """Initialize the lead qualification agent."""
        self.model_manager = ModelManager()
        self.storage = StorageManager()
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        
        # Define qualification criteria weights
        self.criteria_weights = {
            'engagement_score': 0.35,
            'intent_score': 0.25,
            'demographic_fit': 0.20,
            'budget_fit': 0.20
        }
        
        # Initialize lead tracking
        self.leads: Dict[str, LeadProfile] = {}
        self.conversion_metrics: Dict[str, float] = {
            'qualification_rate': 0.0,
            'conversion_rate': 0.0,
            'average_time_to_conversion': 0.0
        }

    async def analyze_lead(self, lead_data: Dict) -> LeadProfile:
        """
        Analyze a new lead using ML models and create a lead profile.
        
        Args:
            lead_data: Raw lead data including engagement history and demographics
            
        Returns:
            LeadProfile: Analyzed and scored lead profile
        """
        lead_id = str(uuid.uuid4())
        
        # Create initial lead profile
        profile = LeadProfile(
            id=lead_id,
            source=lead_data.get('source', 'unknown'),
            first_touch_point=datetime.now(),
            engagement_history=[],
            demographic_data=lead_data.get('demographics', {}),
            behavior_metrics={}
        )
        
        # Analyze engagement data
        engagement_score = await self._calculate_engagement_score(lead_data)
        
        # Analyze intent signals
        intent_score = await self._analyze_intent(lead_data)
        
        # Calculate demographic fit
        demographic_fit = self._calculate_demographic_fit(lead_data)
        
        # Evaluate budget alignment
        budget_fit = self._evaluate_budget_fit(lead_data)
        
        # Calculate final qualification score
        qualification_score = (
            engagement_score * self.criteria_weights['engagement_score'] +
            intent_score * self.criteria_weights['intent_score'] +
            demographic_fit * self.criteria_weights['demographic_fit'] +
            budget_fit * self.criteria_weights['budget_fit']
        )
        
        profile.qualification_score = qualification_score
        profile.status = "qualified" if qualification_score >= 0.7 else "disqualified"
        
        # Store lead profile
        self.leads[lead_id] = profile
        await self.storage.store_lead_data(lead_id, profile)
        
        return profile

    async def _calculate_engagement_score(self, lead_data: Dict) -> float:
        """Calculate engagement score based on interaction history."""
        engagement_metrics = lead_data.get('engagement_metrics', {})
        
        # Weight different types of engagement
        weights = {
            'content_views': 0.2,
            'time_spent': 0.3,
            'interactions': 0.3,
            'social_shares': 0.2
        }
        
        score = 0.0
        for metric, weight in weights.items():
            value = engagement_metrics.get(metric, 0)
            normalized_value = min(value / 100.0, 1.0)  # Normalize to 0-1
            score += normalized_value * weight
            
        return score

    async def _analyze_intent(self, lead_data: Dict) -> float:
        """Analyze intent signals using sentiment analysis and behavior patterns."""
        messages = lead_data.get('messages', [])
        if not messages:
            return 0.0
            
        # Analyze sentiment of messages
        sentiments = self.sentiment_analyzer(messages)
        positive_sentiment_ratio = sum(1 for s in sentiments if s['label'] == 'POSITIVE') / len(sentiments)
        
        # Analyze behavior signals
        behavior_signals = lead_data.get('behavior_signals', {})
        intent_signals = {
            'product_page_visits': behavior_signals.get('product_page_visits', 0),
            'pricing_page_visits': behavior_signals.get('pricing_page_visits', 0),
            'download_resources': behavior_signals.get('download_resources', 0)
        }
        
        # Normalize and combine signals
        normalized_signals = {k: min(v/10.0, 1.0) for k, v in intent_signals.items()}
        behavior_score = sum(normalized_signals.values()) / len(normalized_signals)
        
        # Combine sentiment and behavior scores
        return 0.4 * positive_sentiment_ratio + 0.6 * behavior_score

    def _calculate_demographic_fit(self, lead_data: Dict) -> float:
        """Calculate how well the lead fits target demographic criteria."""
        target_demographics = self.storage.get_target_demographics()
        lead_demographics = lead_data.get('demographics', {})
        
        match_score = 0.0
        total_criteria = len(target_demographics)
        
        for criterion, target_value in target_demographics.items():
            lead_value = lead_demographics.get(criterion)
            if lead_value == target_value:
                match_score += 1.0
            elif isinstance(target_value, (list, tuple)) and lead_value in target_value:
                match_score += 0.8
                
        return match_score / total_criteria if total_criteria > 0 else 0.0

    def _evaluate_budget_fit(self, lead_data: Dict) -> float:
        """Evaluate if the lead's budget aligns with service offerings."""
        lead_budget = lead_data.get('budget_range', {})
        if not lead_budget:
            return 0.0
            
        min_budget = lead_budget.get('min', 0)
        service_tiers = self.storage.get_service_tiers()
        
        # Find the best fitting service tier
        fits = [
            1.0 if min_budget >= tier['min_budget'] else 0.5 if min_budget >= tier['min_budget'] * 0.7 else 0.0
            for tier in service_tiers
        ]
        
        return max(fits) if fits else 0.0

    async def update_lead_status(self, lead_id: str, new_status: str, conversion_data: Optional[Dict] = None):
        """Update a lead's status and track conversion metrics."""
        if lead_id not in self.leads:
            logger.error(f"Lead {lead_id} not found")
            return
            
        lead = self.leads[lead_id]
        old_status = lead.status
        lead.status = new_status
        
        if new_status == "converted" and conversion_data:
            await self._track_conversion(lead, conversion_data)
            
        await self.storage.update_lead_status(lead_id, new_status)
        logger.info(f"Updated lead {lead_id} status from {old_status} to {new_status}")

    async def _track_conversion(self, lead: LeadProfile, conversion_data: Dict):
        """Track conversion metrics for reporting and optimization."""
        conversion_time = datetime.now()
        time_to_conversion = (conversion_time - lead.first_touch_point).days
        
        # Update conversion metrics
        total_leads = len(self.leads)
        converted_leads = sum(1 for l in self.leads.values() if l.status == "converted")
        qualified_leads = sum(1 for l in self.leads.values() if l.status in ["qualified", "converted"])
        
        self.conversion_metrics.update({
            'qualification_rate': qualified_leads / total_leads if total_leads > 0 else 0.0,
            'conversion_rate': converted_leads / qualified_leads if qualified_leads > 0 else 0.0,
            'average_time_to_conversion': (
                (self.conversion_metrics['average_time_to_conversion'] * (converted_leads - 1) + time_to_conversion)
                / converted_leads if converted_leads > 0 else 0.0
            )
        })
        
        await self.storage.store_conversion_metrics(self.conversion_metrics)

    async def get_prioritized_leads(self, min_score: float = 0.7) -> List[Tuple[str, float]]:
        """Get a prioritized list of qualified leads."""
        qualified_leads = [
            (lead_id, lead.qualification_score)
            for lead_id, lead in self.leads.items()
            if lead.status == "qualified" and lead.qualification_score >= min_score
        ]
        
        return sorted(qualified_leads, key=lambda x: x[1], reverse=True)

    async def generate_qualification_report(self) -> Dict:
        """Generate a comprehensive lead qualification report."""
        return {
            'total_leads': len(self.leads),
            'qualified_leads': sum(1 for l in self.leads.values() if l.status == "qualified"),
            'conversion_metrics': self.conversion_metrics,
            'average_qualification_score': np.mean([l.qualification_score for l in self.leads.values()]),
            'top_performing_sources': self._analyze_top_sources(),
            'qualification_trends': await self._analyze_qualification_trends()
        }

    def _analyze_top_sources(self) -> Dict[str, float]:
        """Analyze which lead sources are performing best."""
        source_scores = {}
        source_counts = {}
        
        for lead in self.leads.values():
            if lead.source not in source_scores:
                source_scores[lead.source] = 0.0
                source_counts[lead.source] = 0
                
            source_scores[lead.source] += lead.qualification_score
            source_counts[lead.source] += 1
            
        return {
            source: score / count
            for source, (score, count) in 
            zip(source_scores.keys(), zip(source_scores.values(), source_counts.values()))
        }

    async def _analyze_qualification_trends(self) -> Dict:
        """Analyze trends in lead qualification over time."""
        # Implementation for trend analysis
        # This would analyze patterns in qualification scores and conversion rates over time
        pass
