import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CaseStudyAnalyzer:
    """Analyzes successful case studies and identifies winning patterns."""
    
    def __init__(self, config_path: str):
        """Initialize the analyzer with configuration."""
        self.config = self._load_config(config_path)
        self.success_patterns = {}
        self.performance_metrics = {}
    
    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def analyze_case_studies(self, case_studies: List[Dict]) -> Dict:
        """
        Analyze successful case studies to identify winning patterns.
        
        Args:
            case_studies: List of case study data
            
        Returns:
            Dictionary containing identified patterns
        """
        patterns = {
            'content': self._analyze_content_patterns(case_studies),
            'timing': self._analyze_timing_patterns(case_studies),
            'engagement': self._analyze_engagement_patterns(case_studies),
            'audience': self._analyze_audience_patterns(case_studies),
            'conversion': self._analyze_conversion_patterns(case_studies)
        }
        
        self.success_patterns = patterns
        return patterns
    
    def _analyze_content_patterns(self, case_studies: List[Dict]) -> Dict:
        """Analyze content-related patterns."""
        content_data = []
        for case in case_studies:
            content_metrics = {
                'post_length': case.get('content_length', 0),
                'image_count': case.get('image_count', 0),
                'video_count': case.get('video_count', 0),
                'hashtag_count': case.get('hashtag_count', 0),
                'engagement_rate': case.get('engagement_rate', 0),
                'conversion_rate': case.get('conversion_rate', 0)
            }
            content_data.append(content_metrics)
        
        df = pd.DataFrame(content_data)
        
        # Normalize data
        scaler = StandardScaler()
        normalized_data = scaler.fit_transform(df)
        
        # Perform clustering to identify patterns
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(normalized_data)
        
        # Find the best performing cluster
        cluster_performance = {}
        for i in range(3):
            cluster_mask = clusters == i
            cluster_performance[i] = df[cluster_mask]['conversion_rate'].mean()
        
        best_cluster = max(cluster_performance.items(), key=lambda x: x[1])[0]
        best_patterns = df[clusters == best_cluster].mean()
        
        return {
            'optimal_post_length': int(best_patterns['post_length']),
            'optimal_image_count': round(best_patterns['image_count'], 1),
            'optimal_video_count': round(best_patterns['video_count'], 1),
            'optimal_hashtag_count': int(best_patterns['hashtag_count'])
        }
    
    def _analyze_timing_patterns(self, case_studies: List[Dict]) -> Dict:
        """Analyze timing-related patterns."""
        df = pd.DataFrame(case_studies)
        
        best_hours = df.groupby('hour')['engagement_rate'].mean().nlargest(3).index.tolist()
        best_days = df.groupby('day_of_week')['engagement_rate'].mean().nlargest(3).index.tolist()
        
        return {
            'optimal_posting_hours': best_hours,
            'optimal_posting_days': best_days
        }
    
    def _analyze_engagement_patterns(self, case_studies: List[Dict]) -> Dict:
        """Analyze engagement-related patterns."""
        df = pd.DataFrame(case_studies)
        
        engagement_cols = ['likes_ratio', 'comments_ratio', 'shares_ratio', 'saves_ratio']
        
        # Perform PCA to identify key engagement factors
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(df[engagement_cols])
        
        # Find correlation with engagement rate
        correlations = df[engagement_cols + ['engagement_rate']].corr()['engagement_rate'].sort_values(ascending=False)
        
        return {
            'key_engagement_metrics': correlations.index[1:4].tolist(),
            'engagement_importance': correlations[1:4].tolist()
        }
    
    def _analyze_audience_patterns(self, case_studies: List[Dict]) -> Dict:
        """Analyze audience-related patterns."""
        df = pd.DataFrame(case_studies)
        
        # Analyze age groups
        top_age_groups = df.groupby('age_group')['engagement_rate'].mean().nlargest(2).index.tolist()
        
        # Analyze genders
        top_genders = df.groupby('gender')['engagement_rate'].mean().nlargest(2).index.tolist()
        
        # Analyze locations
        top_locations = df.groupby('location')['engagement_rate'].mean().nlargest(3).index.tolist()
        
        # Analyze interests
        all_interests = [interest for case in case_studies for interest in case.get('interests', [])]
        interest_counts = pd.Series(all_interests).value_counts()
        top_interests = interest_counts.nlargest(5).index.tolist()
        
        return {
            'top_age_groups': top_age_groups,
            'top_genders': top_genders,
            'top_locations': top_locations,
            'top_interests': top_interests
        }
    
    def _analyze_conversion_patterns(self, case_studies: List[Dict]) -> Dict:
        """Analyze conversion-related patterns."""
        conversion_data = []
        for case in case_studies:
            funnel = case.get('conversion_funnel', {})
            conversion_data.append({
                'awareness_rate': funnel.get('awareness_rate', 0),
                'consideration_rate': funnel.get('consideration_rate', 0),
                'action_rate': funnel.get('action_rate', 0),
                'retention_rate': funnel.get('retention_rate', 0),
                'overall_conversion': case.get('conversion_rate', 0)
            })
        
        df = pd.DataFrame(conversion_data)
        
        # Calculate funnel benchmarks
        benchmarks = {
            'awareness': {
                'min': df['awareness_rate'].quantile(0.25),
                'target': df['awareness_rate'].quantile(0.75),
                'best': df['awareness_rate'].max()
            },
            'consideration': {
                'min': df['consideration_rate'].quantile(0.25),
                'target': df['consideration_rate'].quantile(0.75),
                'best': df['consideration_rate'].max()
            },
            'action': {
                'min': df['action_rate'].quantile(0.25),
                'target': df['action_rate'].quantile(0.75),
                'best': df['action_rate'].max()
            },
            'retention': {
                'min': df['retention_rate'].quantile(0.25),
                'target': df['retention_rate'].quantile(0.75),
                'best': df['retention_rate'].max()
            }
        }
        
        return benchmarks
    
    def _extract_top_interests(self, df: pd.DataFrame) -> List[str]:
        """Extract top performing interests from audience data."""
        all_interests = []
        conversion_rates = []
        
        for _, row in df.iterrows():
            interests = row['interests']
            conv_rate = row['conversion_rate']
            for interest in interests:
                all_interests.append(interest)
                conversion_rates.append(conv_rate)
        
        interest_df = pd.DataFrame({
            'interest': all_interests,
            'conversion_rate': conversion_rates
        })
        
        return interest_df.groupby('interest')['conversion_rate'].mean().nlargest(5).index.tolist()
    
    def generate_recommendations(self) -> Dict:
        """Generate actionable recommendations based on patterns."""
        if not self.success_patterns:
            return {}
        
        recommendations = {
            'content': {
                'title': 'Content Strategy',
                'recommendations': [
                    f"Aim for posts with {self.success_patterns['content']['optimal_post_length']} characters",
                    f"Include {self.success_patterns['content']['optimal_image_count']} images per post",
                    f"Use {self.success_patterns['content']['optimal_hashtag_count']} relevant hashtags"
                ]
            },
            'timing': {
                'title': 'Posting Schedule',
                'recommendations': [
                    f"Post during peak hours: {', '.join(map(str, self.success_patterns['timing']['optimal_posting_hours']))}",
                    f"Focus on key days: {', '.join(map(str, self.success_patterns['timing']['optimal_posting_days']))}"
                ]
            },
            'engagement': {
                'title': 'Engagement Strategy',
                'recommendations': [
                    f"Focus on {metric} to drive conversions" 
                    for metric in self.success_patterns['engagement']['key_engagement_metrics']
                ]
            },
            'audience': {
                'title': 'Audience Targeting',
                'recommendations': [
                    f"Primary age groups: {', '.join(self.success_patterns['audience']['top_age_groups'])}",
                    f"Key locations: {', '.join(self.success_patterns['audience']['top_locations'])}",
                    f"Top interests: {', '.join(self.success_patterns['audience']['top_interests'])}"
                ]
            }
        }
        
        return recommendations
    
    def generate_performance_report(self, 
                                  current_metrics: Dict,
                                  email: str = "gagan@designgaga.ca") -> None:
        """
        Generate and send weekly performance report.
        
        Args:
            current_metrics: Current performance metrics
            email: Email address to send report to
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self._compare_metrics(current_metrics),
            'recommendations': self.generate_recommendations(),
            'next_actions': self._generate_next_actions(current_metrics)
        }
        
        # Save report
        report_path = f"reports/performance_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Send email (implement email sending logic)
        self._send_report_email(report, email)
    
    def _compare_metrics(self, current_metrics: Dict) -> Dict:
        """Compare current metrics with benchmarks."""
        comparisons = {}
        for metric, value in current_metrics.items():
            if metric in self.success_patterns.get('conversion', {}):
                benchmark = self.success_patterns['conversion'][metric]
                comparisons[metric] = {
                    'current': value,
                    'benchmark': benchmark['target'],
                    'performance': (value / benchmark['target']) * 100,
                    'status': 'above_target' if value >= benchmark['target'] else 'below_target'
                }
        return comparisons
    
    def _generate_next_actions(self, current_metrics: Dict) -> List[str]:
        """Generate prioritized next actions based on current performance."""
        actions = []
        comparisons = self._compare_metrics(current_metrics)
        
        for metric, comparison in comparisons.items():
            if comparison['status'] == 'below_target':
                actions.append(f"Improve {metric} (Currently at {comparison['performance']:.1f}% of target)")
        
        return sorted(actions, key=lambda x: float(x.split('(')[1].split('%')[0]))
    
    def _send_report_email(self, report: Dict, email: str) -> None:
        """Send performance report via email."""
        # Implement email sending logic here
        pass
