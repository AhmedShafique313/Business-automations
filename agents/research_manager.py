from typing import Dict, List
import json
import os
from datetime import datetime
import logging

class ResearchManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_research(self, task_gid: str, agent_data: Dict) -> Dict:
        """Process research for an agent, combining new and existing data."""
        try:
            # Initialize research data
            research = {
                'name': agent_data.get('name', ''),
                'brokerage': agent_data.get('brokerage', ''),
                'office': agent_data.get('office', ''),
                'location': agent_data.get('location', ''),
                'contact_info': {},
                'social_profiles': {},
                'listings': [],
                'personality': {},
                'value_props': [],
                'personalization_points': [],
                'suggested_approach': None,
                'data_quality_score': 0
            }

            # Load cached research if available
            cached_data = self._load_cached_research(agent_data.get('name', ''))
            if cached_data:
                research = self._merge_research_data(research, cached_data)

            # Update research with new data
            research = self._update_research_data(research, agent_data)

            # Cache the results
            self._cache_research_results(agent_data.get('name', ''), research)

            return research

        except Exception as e:
            self.logger.error(f"Error processing research: {str(e)}")
            return research

    def _load_cached_research(self, agent_name: str) -> Dict:
        """Load research data from cache."""
        try:
            cache_file = f"research_cache/{agent_name.lower().replace(' ', '_')}.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading cached research: {str(e)}")
        return {}

    def _update_research_data(self, research: Dict, agent_data: Dict) -> Dict:
        """Update research data with new findings."""
        try:
            # Update social profiles if found
            if agent_data.get('social_profiles'):
                research['social_profiles'].update(agent_data['social_profiles'])
                research['data_quality_score'] += 2

            # Update contact info if found
            if agent_data.get('contact_info'):
                research['contact_info'].update(agent_data['contact_info'])
                research['data_quality_score'] += 2

            # Update listings if found
            if agent_data.get('listings'):
                research['listings'] = list(set(research['listings'] + agent_data['listings']))
                research['data_quality_score'] += 2

            # Update personality if found
            if agent_data.get('personality'):
                research['personality'].update(agent_data['personality'])
                research['data_quality_score'] += 2

            # Update campaign insights if found
            if agent_data.get('value_props'):
                research['value_props'] = list(set(research['value_props'] + agent_data['value_props']))
                research['data_quality_score'] += 1

            if agent_data.get('personalization_points'):
                research['personalization_points'] = list(set(research['personalization_points'] + agent_data['personalization_points']))
                research['data_quality_score'] += 1

            return research

        except Exception as e:
            self.logger.error(f"Error updating research data: {str(e)}")
            return research

    def _merge_research_data(self, new_data: Dict, existing_data: Dict) -> Dict:
        """Merge new research data with existing data."""
        if not existing_data:
            return new_data

        merged = new_data.copy()
        
        for key, value in existing_data.items():
            if key not in merged or not merged[key]:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                for k, v in value.items():
                    if k not in merged[key] or not merged[key][k]:
                        merged[key][k] = v
            elif isinstance(value, list) and isinstance(merged[key], list):
                merged[key] = list(set(merged[key] + value))

        return merged

    def _cache_research_results(self, agent_name: str, research: Dict) -> None:
        """Cache research results for future use."""
        try:
            os.makedirs("research_cache", exist_ok=True)
            cache_file = f"research_cache/{agent_name.lower().replace(' ', '_')}.json"
            
            # Backup existing cache
            if os.path.exists(cache_file):
                backup_file = f"{cache_file}.bak"
                try:
                    os.replace(cache_file, backup_file)
                except Exception as e:
                    self.logger.error(f"Error creating cache backup: {str(e)}")

            # Write new cache
            with open(cache_file, 'w') as f:
                json.dump(research, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error caching research results: {str(e)}")
            # Restore backup if available
            if os.path.exists(f"{cache_file}.bak"):
                try:
                    os.replace(f"{cache_file}.bak", cache_file)
                except Exception as backup_e:
                    self.logger.error(f"Error restoring cache backup: {str(backup_e)}")
