from base_agent import BaseAgent
import requests
import json
from pathlib import Path
import re
from datetime import datetime
import logging
from typing import Dict, Optional
import os
from lead_scoring_agent import LeadScoringAgent

class DataEnrichmentAgent(BaseAgent):
    def __init__(self, work_dir):
        super().__init__("DataEnrichment", work_dir)
        # Initialize API keys from environment variables
        self.clearbit_key = os.getenv('CLEARBIT_API_KEY', 'YOUR_CLEARBIT_API_KEY')
        self.hunter_key = os.getenv('HUNTER_API_KEY', 'YOUR_HUNTER_API_KEY')
        self.linkedin_token = os.getenv('LINKEDIN_TOKEN', 'YOUR_LINKEDIN_TOKEN')
        
        # Setup cache directory
        self.cache_dir = self.work_dir / 'enrichment_cache'
        self.cache_dir.mkdir(exist_ok=True)
        
        self.lead_scoring = LeadScoringAgent(work_dir)
        
    def enrich_lead_data(self, email: str, name: Optional[str] = None) -> Dict:
        """
        Enrich lead data from multiple sources
        """
        try:
            # Get enriched data from various sources
            enriched_data = self._get_enriched_data(email, name)
            
            # Track this as an engagement
            self.lead_scoring.track_engagement(
                email,
                'data_enrichment',
                {'source': 'clearbit', 'data_quality': enriched_data.get('data_quality', 0)}
            )
            
            # Get current lead score
            score_data = self.lead_scoring.calculate_lead_score(email)
            
            return {
                'enriched_data': enriched_data,
                'lead_score': score_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Lead enrichment failed: {str(e)}")
            return {
                'error': str(e),
                'email': email
            }
            
    def _get_enriched_data(self, email: str, name: Optional[str] = None) -> Dict:
        """
        Enrich lead data using multiple data sources
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(email)
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                self.log_activity('data_enrichment', 'cache_hit', {'email': email})
                return cached_data
            
            enriched_data = {
                'email': email,
                'timestamp': datetime.now().isoformat(),
                'name': name
            }
            
            # Gather data from multiple sources
            clearbit_data = self._get_clearbit_data(email)
            hunter_data = self._get_hunter_data(email)
            linkedin_data = self._get_linkedin_data(email, name)
            
            # Merge all data sources
            enriched_data.update(self._merge_data_sources(
                clearbit_data,
                hunter_data,
                linkedin_data
            ))
            
            # Add industry-specific insights for luxury home staging
            enriched_data['industry_insights'] = self._get_industry_insights(enriched_data)
            
            # Cache the results
            self._cache_data(cache_key, enriched_data)
            
            self.log_activity('data_enrichment', 'completed', {
                'email': email,
                'data_sources': ['clearbit', 'hunter', 'linkedin']
            })
            
            return enriched_data
            
        except Exception as e:
            self.log_activity('data_enrichment', 'failed', {
                'email': email,
                'error': str(e)
            })
            return {'email': email, 'error': str(e)}
            
    def _get_clearbit_data(self, email: str) -> Dict:
        """
        Get company and person data from Clearbit
        """
        try:
            headers = {'Authorization': f'Bearer {self.clearbit_key}'}
            response = requests.get(
                f'https://person.clearbit.com/v2/people/find?email={email}',
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'company': {
                        'name': data.get('company', {}).get('name'),
                        'domain': data.get('company', {}).get('domain'),
                        'industry': data.get('company', {}).get('industry'),
                        'size': data.get('company', {}).get('metrics', {}).get('employees'),
                        'location': data.get('company', {}).get('location'),
                        'linkedin_handle': data.get('company', {}).get('linkedin', {}).get('handle')
                    },
                    'person': {
                        'full_name': data.get('name', {}).get('fullName'),
                        'title': data.get('employment', {}).get('title'),
                        'seniority': data.get('employment', {}).get('seniority')
                    }
                }
        except Exception as e:
            self.logger.error(f"Clearbit API error: {str(e)}")
        return {}
        
    def _get_hunter_data(self, email: str) -> Dict:
        """
        Verify email and get additional data from Hunter
        """
        try:
            response = requests.get(
                'https://api.hunter.io/v2/email-verifier',
                params={'email': email, 'api_key': self.hunter_key}
            )
            data = response.json()
            if data.get('data'):
                return {
                    'email_verification': {
                        'status': data['data'].get('status'),
                        'score': data['data'].get('score'),
                        'position': data['data'].get('position'),
                        'company': data['data'].get('company')
                    }
                }
        except Exception as e:
            self.logger.error(f"Hunter API error: {str(e)}")
        return {}
        
    def _get_linkedin_data(self, email: str, name: Optional[str] = None) -> Dict:
        """
        Get LinkedIn profile data
        """
        try:
            if name:
                # Search for the person on LinkedIn
                headers = {'Authorization': f'Bearer {self.linkedin_token}'}
                response = requests.get(
                    'https://api.linkedin.com/v2/people/~?projection=(id,firstName,lastName,headline,location,industry)',
                    headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'linkedin': {
                            'current_role': data.get('headline'),
                            'company': data.get('industry'),
                            'location': data.get('location', {}).get('name'),
                            'industry': data.get('industry'),
                            'education': []
                        }
                    }
        except Exception as e:
            self.logger.error(f"LinkedIn API error: {str(e)}")
        return {}
        
    def _merge_data_sources(self, *data_sources: Dict) -> Dict:
        """
        Merge data from multiple sources with priority handling
        """
        merged = {}
        for data in data_sources:
            self._deep_merge(merged, data)
        return merged
        
    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """
        Deep merge two dictionaries
        """
        for k, v in dict2.items():
            if k in dict1 and isinstance(dict1[k], dict) and isinstance(v, dict):
                self._deep_merge(dict1[k], v)
            else:
                dict1[k] = v
        return dict1
        
    def _get_industry_insights(self, data: Dict) -> Dict:
        """
        Generate industry-specific insights for luxury home staging
        """
        insights = {
            'potential_value': 'medium',
            'engagement_strategy': 'standard',
            'recommended_services': []
        }
        
        # Analyze company size
        company_size = data.get('company', {}).get('size', 0)
        if company_size > 1000:
            insights['potential_value'] = 'high'
            insights['engagement_strategy'] = 'enterprise'
            
        # Analyze industry
        industry = data.get('company', {}).get('industry', '').lower()
        if any(x in industry for x in ['real estate', 'property', 'construction', 'interior']):
            insights['potential_value'] = 'high'
            insights['recommended_services'].append('Complete Home Staging')
            
        # Analyze title/seniority
        title = data.get('person', {}).get('title', '').lower()
        if any(x in title for x in ['director', 'vp', 'president', 'owner', 'partner']):
            insights['engagement_strategy'] = 'executive'
            
        return insights
        
    def _get_cache_key(self, email: str) -> str:
        """
        Generate a cache key from email
        """
        return re.sub(r'[^a-zA-Z0-9]', '_', email)
        
    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """
        Retrieve cached data if not expired
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Check if cache is less than 30 days old
                cached_time = datetime.fromisoformat(data['timestamp'])
                if (datetime.now() - cached_time).days < 30:
                    return data
        return None
        
    def _cache_data(self, cache_key: str, data: Dict):
        """
        Cache enriched data
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def analyze_lead_potential(self, enriched_data: Dict) -> Dict:
        """
        Analyze lead potential specifically for luxury home staging
        """
        score = 0
        reasons = []
        
        # Company size factor
        company_size = enriched_data.get('company', {}).get('size', 0)
        if company_size > 1000:
            score += 30
            reasons.append("Large company size indicates potential for multiple projects")
        elif company_size > 100:
            score += 20
            reasons.append("Mid-sized company with good project potential")
            
        # Industry relevance
        industry = enriched_data.get('company', {}).get('industry', '').lower()
        if 'real estate' in industry:
            score += 25
            reasons.append("Direct real estate industry involvement")
        elif any(x in industry for x in ['property', 'construction', 'interior']):
            score += 15
            reasons.append("Related industry with staging needs")
            
        # Decision maker factor
        title = enriched_data.get('person', {}).get('title', '').lower()
        if any(x in title for x in ['director', 'vp', 'president', 'owner']):
            score += 25
            reasons.append("Decision maker position")
        elif any(x in title for x in ['manager', 'lead', 'head']):
            score += 15
            reasons.append("Management position with influence")
            
        # Location factor
        location = enriched_data.get('company', {}).get('location', '').lower()
        if any(x in location for x in ['new york', 'los angeles', 'san francisco', 'miami']):
            score += 20
            reasons.append("Premium real estate market location")
            
        return {
            'score': min(score, 100),
            'reasons': reasons,
            'recommendation': self._get_recommendation(score)
        }
        
    def _get_recommendation(self, score: int) -> str:
        """
        Get recommendation based on lead score
        """
        if score >= 80:
            return "High-priority lead: Immediate personalized outreach with premium staging portfolio"
        elif score >= 60:
            return "Quality lead: Engage with custom staging solutions proposal"
        elif score >= 40:
            return "Moderate potential: Nurture with luxury staging content and case studies"
        else:
            return "Low priority: Add to general marketing nurture campaign"
