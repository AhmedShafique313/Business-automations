"""Researcher Agent for intelligent lead generation.

This agent is responsible for:
- Finding potential leads through online research
- Gathering contact information and social media profiles
- Building detailed lead profiles with business insights
- Identifying engagement opportunities across platforms
"""

import logging
import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry
from redis import Redis
from prometheus_client import Counter, Histogram

from config_manager import ConfigManager
from utils.web_scraper import WebScraper
from utils.social_media import SocialMediaScanner
from utils.lead_enricher import LeadEnricher
from utils.error_handler import handle_error
from utils.memory_manager import MemoryManager
from utils.metrics_collector import MetricsCollector

# Prometheus metrics
LEAD_COUNTER = Counter('leads_discovered_total', 'Total number of leads discovered')
ENRICHMENT_TIME = Histogram('lead_enrichment_seconds', 'Time spent enriching leads')
QUALITY_SCORE = Histogram('lead_quality_score', 'Distribution of lead quality scores')

@dataclass(frozen=True)
class LeadProfile:
    """Immutable data structure for a business lead."""
    email: str
    name: str
    business_name: str
    phone: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    business_type: Optional[str] = None
    location: Optional[str] = None
    engagement_score: float = 0.0
    last_interaction: Optional[datetime] = None
    interaction_history: tuple = field(default_factory=tuple)  # Using tuple for immutability
    tags: frozenset = field(default_factory=frozenset)  # Using frozenset for immutability
    verification_status: str = 'pending'
    data_quality_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate lead data after initialization."""
        if not self._validate_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        if not self.name or not self.business_name:
            raise ValueError("Name and business name are required")
            
    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

class ResearcherAgent:
    """Agent responsible for lead research and profiling."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.scraper = WebScraper()
        self.social_scanner = SocialMediaScanner()
        self.lead_enricher = LeadEnricher()
        self.logger = logging.getLogger(__name__)
        self.memory_manager = MemoryManager()
        self.metrics = MetricsCollector()
        
        # Initialize Redis connection
        self.redis = Redis(
            host=self.config.get('redis_host', 'localhost'),
            port=self.config.get('redis_port', 6379),
            db=self.config.get('redis_db', 0)
        )
        
        # Configure rate limits from config
        self.rate_limit = self.config.get('rate_limits', {}).get('research', 100)
        self.rate_period = self.config.get('rate_limits', {}).get('research_period', 3600)
        
        # Initialize seen identifiers cache
        self.seen_identifiers: Set[str] = set()
        
    async def research_target_market(self, business_type: str, location: str) -> List[LeadProfile]:
        """Conduct comprehensive market research for target business type."""
        self.logger.info(f"Starting market research for {business_type} in {location}")
        
        try:
            # Concurrent lead discovery from multiple sources
            tasks = [
                self._safe_search(self.scraper.search_google_my_business, business_type, location, "Google My Business"),
                self._safe_search(self.social_scanner.find_business_profiles, business_type, location, "Social Media"),
                self._safe_search(self.scraper.search_business_directories, business_type, location, "Business Directories")
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and merge results
            valid_results = [r for r in results if not isinstance(r, Exception)]
            all_leads = self._merge_lead_sources(valid_results)
            
            # Process leads in batches to manage memory
            batch_size = self.config.get('batch_size', 50)
            enriched_leads = []
            
            for i in range(0, len(all_leads), batch_size):
                batch = all_leads[i:i + batch_size]
                batch_results = await asyncio.gather(
                    *[self._enrich_lead_safely(lead) for lead in batch]
                )
                valid_leads = [lead for lead in batch_results if lead and self._validate_lead_data(lead)]
                enriched_leads.extend(valid_leads)
                
                # Clear memory after each batch
                self.memory_manager.clear_batch_memory()
            
            # Update metrics
            LEAD_COUNTER.inc(len(enriched_leads))
            for lead in enriched_leads:
                QUALITY_SCORE.observe(lead.data_quality_score)
            
            return enriched_leads
            
        except Exception as e:
            self.logger.error(f"Market research failed: {str(e)}")
            self.metrics.record_error('research_failure', str(e))
            raise
        finally:
            # Clear memory after processing
            self.memory_manager.clear_research_memory()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def _safe_search(self, search_func, business_type: str, location: str, source: str) -> List[Dict]:
        """Safely execute a search function with error handling."""
        try:
            # Check cache first
            cache_key = f"{source}:{business_type}:{location}"
            cached_result = self.redis.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute search with timeout
            result = await asyncio.wait_for(
                search_func(business_type, location),
                timeout=self.config.get('search_timeout', 30)
            )
            
            # Cache result with expiration
            self.redis.setex(
                cache_key,
                self.config.get('cache_ttl', 3600),
                json.dumps(result)
            )
            
            return result
        except asyncio.TimeoutError:
            self.logger.error(f"{source} search timed out")
            self.metrics.record_error('search_timeout', source)
            return []
        except Exception as e:
            self.logger.error(f"{source} search failed: {str(e)}")
            self.metrics.record_error('search_failure', f"{source}: {str(e)}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    @limits(calls=50, period=3600)  # More conservative rate limit for enrichment
    @sleep_and_retry
    @ENRICHMENT_TIME.time()
    async def _enrich_lead_safely(self, lead: Dict) -> Optional[LeadProfile]:
        """Safely enrich lead data with rate limiting and retries."""
        try:
            # Check cache first
            cache_key = f"lead:{self._create_lead_identifier(lead)}"
            cached_lead = self.redis.get(cache_key)
            if cached_lead:
                return LeadProfile(**json.loads(cached_lead))
            
            enriched_data = await self.lead_enricher.enrich_lead_data(lead)
            lead_profile = LeadProfile(
                **enriched_data,
                engagement_score=self._calculate_initial_score(enriched_data),
                data_quality_score=self._calculate_data_quality(enriched_data)
            )
            
            # Cache enriched lead
            self.redis.setex(
                cache_key,
                self.config.get('lead_cache_ttl', 86400),  # 24 hours default
                json.dumps(lead_profile.__dict__)
            )
            
            return lead_profile
        except Exception as e:
            self.logger.error(f"Lead enrichment failed: {str(e)}")
            self.metrics.record_error('enrichment_failure', str(e))
            return None
    
    @lru_cache(maxsize=1000)
    def _create_lead_identifier(self, lead: Dict) -> str:
        """Create a unique identifier for a lead using multiple fields."""
        identifier_parts = []
        
        # Use multiple fields to create a more robust identifier
        if lead.get('email'):
            identifier_parts.append(lead['email'].lower())
        if lead.get('phone'):
            identifier_parts.append(str(lead['phone']).replace(' ', '').replace('-', ''))
        if lead.get('website'):
            identifier_parts.append(lead['website'].lower().replace('http://', '').replace('https://', '').rstrip('/'))
        if lead.get('business_name'):
            identifier_parts.append(lead['business_name'].lower())
            
        return '|'.join(identifier_parts)
    
    def _merge_lead_sources(self, lead_lists: List[List[Dict]]) -> List[Dict]:
        """Merge and deduplicate leads from multiple sources."""
        merged_leads = []
        
        for lead_list in lead_lists:
            for lead in lead_list:
                identifier = self._create_lead_identifier(lead)
                
                if identifier not in self.seen_identifiers:
                    self.seen_identifiers.add(identifier)
                    merged_leads.append(lead)
                    
                    # Prevent memory growth
                    if len(self.seen_identifiers) > self.config.get('max_seen_identifiers', 100000):
                        self.seen_identifiers.clear()
        
        return merged_leads
    
    def _validate_lead_data(self, lead: LeadProfile) -> bool:
        """Validate lead data quality and completeness."""
        required_fields = {'email', 'name', 'business_name'}
        
        # Check required fields
        if not all(hasattr(lead, field) and getattr(lead, field) for field in required_fields):
            return False
            
        # Validate email format (basic check)
        if not '@' in lead.email or not '.' in lead.email:
            return False
            
        # Check data quality score
        if lead.data_quality_score < self.config.get('min_data_quality_score', 0.3):
            return False
            
        return True
    
    def _calculate_data_quality(self, lead: LeadProfile) -> float:
        """Calculate data quality score based on completeness and validity."""
        score = 0.0
        total_fields = 0
        
        # Check each field for completeness and validity
        for field, value in vars(lead).items():
            if field in ['interaction_history', 'tags', 'last_updated']:
                continue
                
            total_fields += 1
            if value:
                score += 1
                
                # Additional points for validated data
                if field == 'email' and '@' in str(value) and '.' in str(value):
                    score += 0.5
                elif field == 'phone' and len(str(value)) >= 10:
                    score += 0.5
                elif field == 'website' and ('http://' in str(value) or 'https://' in str(value)):
                    score += 0.5
                    
        return min(score / total_fields, 1.0)
    
    def _calculate_initial_score(self, lead: LeadProfile) -> float:
        """Calculate initial engagement score based on available data."""
        score = 0.0
        
        # Basic information completeness
        if lead.email:
            score += 0.2
        if lead.phone:
            score += 0.2
        if lead.website:
            score += 0.1
            
        # Social media presence
        if lead.instagram:
            score += 0.1
        if lead.facebook:
            score += 0.1
        if lead.linkedin:
            score += 0.1
            
        # Business validation
        if lead.business_name and lead.location:
            score += 0.2
            
        return min(score, 1.0)
    
    async def update_lead_profile(self, lead: LeadProfile, interaction_data: Dict) -> LeadProfile:
        """Update lead profile with new interaction data."""
        if not lead.interaction_history:
            lead.interaction_history = []
            
        interaction_data['timestamp'] = datetime.now().isoformat()
        lead.interaction_history = lead.interaction_history + (interaction_data,)
        lead.last_interaction = datetime.now()
        
        # Recalculate engagement score based on interaction
        lead.engagement_score = self._calculate_engagement_score(lead)
        
        return lead
    
    def _calculate_engagement_score(self, lead: LeadProfile) -> float:
        """Calculate engagement score based on interaction history."""
        base_score = self._calculate_initial_score(lead)
        
        if not lead.interaction_history:
            return base_score
            
        interaction_score = 0.0
        recent_interactions = [i for i in lead.interaction_history 
                             if datetime.now() - datetime.fromisoformat(i['timestamp']) 
                             <= timedelta(days=30)]
        
        for interaction in recent_interactions:
            if interaction['type'] == 'email_opened':
                interaction_score += 0.1
            elif interaction['type'] == 'email_clicked':
                interaction_score += 0.2
            elif interaction['type'] == 'website_visit':
                interaction_score += 0.3
            elif interaction['type'] == 'form_submission':
                interaction_score += 0.4
            elif interaction['type'] == 'meeting_scheduled':
                interaction_score += 0.5
                
        return min(base_score + interaction_score, 1.0)
