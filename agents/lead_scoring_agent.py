from base_agent import BaseAgent
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

@dataclass
class Engagement:
    type: str
    timestamp: datetime
    value: float
    details: Dict

class LeadScoringAgent(BaseAgent):
    def __init__(self, work_dir):
        super().__init__("LeadScoring", work_dir)
        self.leads_dir = self.work_dir / 'leads'
        self.leads_dir.mkdir(exist_ok=True)
        self.model_dir = self.work_dir / 'models'
        self.model_dir.mkdir(exist_ok=True)
        
        # Initialize scoring weights
        self.weights = {
            'email_open': 1,
            'email_click': 3,
            'website_visit': 2,
            'form_submission': 5,
            'social_engagement': 2,
            'content_download': 4,
            'meeting_scheduled': 8,
            'proposal_viewed': 6
        }
        
        # Time decay factors (in days)
        self.time_decay = {
            'recent': 7,
            'medium': 30,
            'old': 90
        }
        
        # Initialize scaler for normalization
        self.scaler = MinMaxScaler()
        
        # Load or initialize ML model
        self.load_model()
        
    def track_engagement(self, lead_email: str, engagement_type: str, details: Dict = None):
        """Track a new engagement event"""
        try:
            lead_file = self.leads_dir / f"{lead_email.replace('@', '_at_')}.json"
            
            # Load existing data or create new
            if lead_file.exists():
                with open(lead_file, 'r') as f:
                    lead_data = json.load(f)
            else:
                lead_data = {
                    'email': lead_email,
                    'first_seen': datetime.now().isoformat(),
                    'engagements': []
                }
            
            # Add new engagement
            engagement = {
                'type': engagement_type,
                'timestamp': datetime.now().isoformat(),
                'value': self.weights.get(engagement_type, 1),
                'details': details or {}
            }
            lead_data['engagements'].append(engagement)
            
            # Save updated data
            with open(lead_file, 'w') as f:
                json.dump(lead_data, f, indent=2)
                
            # Recalculate score
            score = self.calculate_lead_score(lead_email)
            
            self.log_activity('engagement_tracked', 'success', {
                'lead': lead_email,
                'type': engagement_type,
                'score': score
            })
            
            return score
            
        except Exception as e:
            self.log_activity('engagement_tracking', 'failed', {
                'lead': lead_email,
                'error': str(e)
            })
            return None
            
    def calculate_lead_score(self, lead_email: str) -> Dict:
        """Calculate comprehensive lead score using ML model"""
        try:
            lead_file = self.leads_dir / f"{lead_email.replace('@', '_at_')}.json"
            if not lead_file.exists():
                return {'error': 'Lead not found'}
                
            with open(lead_file, 'r') as f:
                lead_data = json.load(f)
                
            # Extract features
            features = self._extract_features(lead_data)
            
            # Get base score from ML model
            base_score = self.predict_score(features)
            
            # Calculate engagement trends
            trends = self._calculate_trends(lead_data['engagements'])
            
            # Calculate urgency based on recent activities
            urgency = self._calculate_urgency(lead_data['engagements'])
            
            # Final score combining ML prediction and heuristics
            final_score = self._combine_scores(base_score, trends, urgency)
            
            # Generate insights
            insights = self._generate_insights(lead_data, final_score, trends, urgency)
            
            return {
                'email': lead_email,
                'score': final_score,
                'trends': trends,
                'urgency': urgency,
                'insights': insights,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.log_activity('score_calculation', 'failed', {
                'lead': lead_email,
                'error': str(e)
            })
            return {'error': str(e)}
            
    def _extract_features(self, lead_data: Dict) -> np.ndarray:
        """Extract features for ML model"""
        engagements = lead_data['engagements']
        now = datetime.now()
        
        features = {
            'total_engagements': len(engagements),
            'unique_engagement_types': len(set(e['type'] for e in engagements)),
            'engagement_frequency': len(engagements) / max(1, (now - datetime.fromisoformat(lead_data['first_seen'])).days),
            'high_value_actions': sum(1 for e in engagements if self.weights.get(e['type'], 0) >= 5),
            'recent_activity': sum(1 for e in engagements 
                                 if (now - datetime.fromisoformat(e['timestamp'])).days <= 7),
            'weighted_score': sum(self.weights.get(e['type'], 1) for e in engagements)
        }
        
        return np.array(list(features.values())).reshape(1, -1)
        
    def _calculate_trends(self, engagements: List[Dict]) -> Dict:
        """Calculate engagement trends over time"""
        if not engagements:
            return {'trend': 'new', 'velocity': 0}
            
        # Sort engagements by time
        sorted_engagements = sorted(engagements, 
                                  key=lambda x: datetime.fromisoformat(x['timestamp']))
        
        # Calculate engagement velocity
        time_span = (datetime.fromisoformat(sorted_engagements[-1]['timestamp']) - 
                    datetime.fromisoformat(sorted_engagements[0]['timestamp'])).days
        velocity = len(engagements) / max(1, time_span)
        
        # Calculate trend direction
        recent_count = sum(1 for e in engagements 
                         if (datetime.now() - datetime.fromisoformat(e['timestamp'])).days <= 7)
        old_count = sum(1 for e in engagements 
                       if 7 < (datetime.now() - datetime.fromisoformat(e['timestamp'])).days <= 14)
        
        if recent_count > old_count:
            trend = 'increasing'
        elif recent_count < old_count:
            trend = 'decreasing'
        else:
            trend = 'stable'
            
        return {
            'trend': trend,
            'velocity': velocity,
            'recent_count': recent_count,
            'total_count': len(engagements)
        }
        
    def _calculate_urgency(self, engagements: List[Dict]) -> float:
        """Calculate lead urgency based on recent high-value actions"""
        urgency = 0
        now = datetime.now()
        
        for engagement in engagements:
            days_ago = (now - datetime.fromisoformat(engagement['timestamp'])).days
            if days_ago <= 7:  # Recent actions have higher urgency
                urgency += self.weights.get(engagement['type'], 1) * 1.5
            elif days_ago <= 30:  # Medium-term actions
                urgency += self.weights.get(engagement['type'], 1)
                
        return min(100, urgency)
        
    def _combine_scores(self, base_score: float, trends: Dict, urgency: float) -> float:
        """Combine different scoring factors into final score"""
        # Base score weight: 50%
        # Trends weight: 30%
        # Urgency weight: 20%
        
        trend_multiplier = {
            'increasing': 1.2,
            'stable': 1.0,
            'decreasing': 0.8,
            'new': 1.0
        }
        
        trend_score = trends['velocity'] * trend_multiplier[trends['trend']]
        
        final_score = (
            0.5 * base_score +
            0.3 * min(100, trend_score * 20) +
            0.2 * urgency
        )
        
        return round(min(100, max(0, final_score)), 2)
        
    def _generate_insights(self, lead_data: Dict, score: float, 
                         trends: Dict, urgency: float) -> List[str]:
        """Generate actionable insights based on lead scoring"""
        insights = []
        
        # Score-based insights
        if score >= 80:
            insights.append("High-value lead: Immediate personal outreach recommended")
        elif score >= 60:
            insights.append("Quality lead: Engage with targeted luxury staging content")
            
        # Trend-based insights
        if trends['trend'] == 'increasing':
            insights.append("Engagement is increasing: Consider accelerating nurture campaign")
        elif trends['trend'] == 'decreasing':
            insights.append("Engagement is decreasing: Re-engagement campaign recommended")
            
        # Urgency-based insights
        if urgency >= 70:
            insights.append("High urgency: Lead shows strong buying signals")
            
        # Activity gaps
        engagement_types = set(e['type'] for e in lead_data['engagements'])
        if 'meeting_scheduled' not in engagement_types:
            insights.append("No meetings yet: Consider direct meeting invitation")
        if 'proposal_viewed' not in engagement_types:
            insights.append("No proposal interaction: Share relevant case studies")
            
        return insights
        
    def predict_score(self, features: np.ndarray) -> float:
        """Predict score using ML model"""
        try:
            # Normalize features
            normalized_features = self.scaler.transform(features)
            
            # For now, use a simple weighted sum (replace with actual ML model)
            weights = np.array([0.2, 0.15, 0.25, 0.2, 0.1, 0.1])
            score = np.dot(normalized_features, weights)[0] * 100
            
            return min(100, max(0, score))
            
        except Exception as e:
            self.logger.error(f"Prediction error: {str(e)}")
            return 50  # Default score
            
    def load_model(self):
        """Load or initialize ML model"""
        model_path = self.model_dir / 'lead_scoring_model.joblib'
        if model_path.exists():
            self.scaler = joblib.load(model_path)
        else:
            # Initialize with some default data ranges
            self.scaler.fit([[0, 0, 0, 0, 0, 0], [100, 10, 1, 20, 30, 1000]])
            joblib.dump(self.scaler, model_path)
            
    def get_lead_history(self, lead_email: str) -> Dict:
        """Get complete lead engagement history"""
        try:
            lead_file = self.leads_dir / f"{lead_email.replace('@', '_at_')}.json"
            if not lead_file.exists():
                return {'error': 'Lead not found'}
                
            with open(lead_file, 'r') as f:
                lead_data = json.load(f)
                
            return {
                'email': lead_email,
                'first_seen': lead_data['first_seen'],
                'total_engagements': len(lead_data['engagements']),
                'engagement_types': list(set(e['type'] for e in lead_data['engagements'])),
                'recent_activities': [
                    {
                        'type': e['type'],
                        'timestamp': e['timestamp'],
                        'details': e['details']
                    }
                    for e in sorted(lead_data['engagements'], 
                                  key=lambda x: datetime.fromisoformat(x['timestamp']),
                                  reverse=True)[:5]
                ],
                'score_history': self._calculate_score_history(lead_data['engagements'])
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    def _calculate_score_history(self, engagements: List[Dict]) -> List[Dict]:
        """Calculate score progression over time"""
        if not engagements:
            return []
            
        score_history = []
        cumulative_engagements = []
        
        for engagement in sorted(engagements, 
                               key=lambda x: datetime.fromisoformat(x['timestamp'])):
            cumulative_engagements.append(engagement)
            score = self._combine_scores(
                self.predict_score(self._extract_features({'engagements': cumulative_engagements})),
                self._calculate_trends(cumulative_engagements),
                self._calculate_urgency(cumulative_engagements)
            )
            
            score_history.append({
                'timestamp': engagement['timestamp'],
                'score': score,
                'event': engagement['type']
            })
            
        return score_history
