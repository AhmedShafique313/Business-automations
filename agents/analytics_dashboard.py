import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import json
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class MetricConfig:
    name: str
    type: str
    source: str
    refresh_rate: str
    threshold_warning: float
    threshold_critical: float
    industry_benchmark: float

class AnalyticsDashboard:
    def __init__(self, config_path: str, work_dir: str):
        self.work_dir = Path(work_dir)
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, MetricTracker] = {}
        self.initialize_metrics()

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def initialize_metrics(self):
        """Initialize metric trackers based on configuration."""
        metric_types = {
            'conversion': ConversionMetric,
            'engagement': EngagementMetric,
            'revenue': RevenueMetric,
            'social': SocialMetric,
            'local': LocalMetric
        }

        for metric_config in self.config['metrics']:
            metric_type = metric_config['type']
            if metric_type in metric_types:
                self.metrics[metric_config['name']] = metric_types[metric_type](
                    MetricConfig(**metric_config)
                )

    def update_metrics(self):
        """Update all metrics with latest data."""
        for metric in self.metrics.values():
            try:
                metric.update()
                self.logger.info(f"Updated metric: {metric.config.name}")
            except Exception as e:
                self.logger.error(f"Error updating metric {metric.config.name}: {str(e)}")

    def generate_report(self, report_type: str = 'full') -> dict:
        """Generate comprehensive analytics report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'insights': [],
            'recommendations': []
        }

        for metric in self.metrics.values():
            report['metrics'][metric.config.name] = {
                'current_value': metric.current_value,
                'trend': metric.calculate_trend(),
                'status': metric.get_status(),
                'benchmark_comparison': metric.compare_to_benchmark()
            }

        report['insights'] = self.generate_insights(report['metrics'])
        report['recommendations'] = self.generate_recommendations(report['metrics'])

        return report

    def generate_insights(self, metrics_data: dict) -> List[str]:
        """Generate actionable insights from metrics data."""
        insights = []
        
        # Analyze trends
        for metric_name, data in metrics_data.items():
            if data['trend'] > 0.1:
                insights.append(f"Strong positive trend in {metric_name}: {data['trend']:.2f}% increase")
            elif data['trend'] < -0.1:
                insights.append(f"Concerning decline in {metric_name}: {data['trend']:.2f}% decrease")

        # Compare to benchmarks
        for metric_name, data in metrics_data.items():
            benchmark_diff = data['benchmark_comparison']
            if abs(benchmark_diff) > 0.2:
                comparison = "above" if benchmark_diff > 0 else "below"
                insights.append(f"{metric_name} is significantly {comparison} industry benchmark")

        return insights

    def generate_recommendations(self, metrics_data: dict) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []
        
        # Analyze metric status
        for metric_name, data in metrics_data.items():
            if data['status'] == 'critical':
                recommendations.append(f"Urgent attention needed for {metric_name}")
                recommendations.append(self.get_improvement_steps(metric_name))
            elif data['status'] == 'warning':
                recommendations.append(f"Consider optimizing {metric_name}")
                recommendations.append(self.get_improvement_steps(metric_name))

        return recommendations

    def get_improvement_steps(self, metric_name: str) -> str:
        """Get specific improvement steps for a metric."""
        improvement_strategies = {
            'conversion_rate': """
                1. Analyze user journey for friction points
                2. A/B test landing pages
                3. Optimize call-to-action placement
                4. Improve form design
                5. Add social proof elements
            """,
            'engagement_rate': """
                1. Increase posting frequency
                2. Test different content types
                3. Improve response time
                4. Run engagement campaigns
                5. Leverage user-generated content
            """,
            'revenue_per_customer': """
                1. Implement upselling strategies
                2. Create package deals
                3. Launch loyalty program
                4. Optimize pricing strategy
                5. Introduce premium services
            """
        }
        return improvement_strategies.get(metric_name, "Custom improvement plan needed")

    def create_visualization(self, metric_name: str, time_range: str = '30d') -> go.Figure:
        """Create interactive visualization for a metric."""
        metric = self.metrics.get(metric_name)
        if not metric:
            raise ValueError(f"Metric {metric_name} not found")

        # Get historical data
        data = metric.get_historical_data(time_range)
        
        # Create figure
        fig = go.Figure()
        
        # Add metric line
        fig.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data['value'],
            name=metric_name,
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Add benchmark line
        fig.add_trace(go.Scatter(
            x=data['timestamp'],
            y=[metric.config.industry_benchmark] * len(data['timestamp']),
            name='Industry Benchmark',
            line=dict(color='#2ca02c', dash='dash')
        ))
        
        # Customize layout
        fig.update_layout(
            title=f"{metric_name} Over Time",
            xaxis_title="Date",
            yaxis_title="Value",
            template="plotly_white",
            showlegend=True
        )
        
        return fig

class MetricTracker(ABC):
    def __init__(self, config: MetricConfig):
        self.config = config
        self.current_value: Optional[float] = None
        self.historical_data: List[Dict] = []
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def update(self):
        """Update metric with latest data."""
        pass

    @abstractmethod
    def get_historical_data(self, time_range: str) -> pd.DataFrame:
        """Get historical data for the metric."""
        pass

    def calculate_trend(self) -> float:
        """Calculate trend as percentage change."""
        if len(self.historical_data) < 2:
            return 0.0
        
        latest = self.historical_data[-1]['value']
        previous = self.historical_data[-2]['value']
        return ((latest - previous) / previous) * 100

    def get_status(self) -> str:
        """Get metric status based on thresholds."""
        if self.current_value is None:
            return 'unknown'
        
        if self.current_value <= self.config.threshold_critical:
            return 'critical'
        elif self.current_value <= self.config.threshold_warning:
            return 'warning'
        return 'good'

    def compare_to_benchmark(self) -> float:
        """Compare current value to industry benchmark."""
        if self.current_value is None:
            return 0.0
        return ((self.current_value - self.config.industry_benchmark) / 
                self.config.industry_benchmark) * 100

class ConversionMetric(MetricTracker):
    """Tracks conversion-related metrics."""

    def update(self):
        """Update conversion rate metric."""
        try:
            # Get latest conversion data from analytics
            analytics_data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', datetime.now() - timedelta(days=1))]
            )
            
            # Calculate conversion rate
            total_visitors = analytics_data['visitors'].sum()
            total_conversions = analytics_data['conversions'].sum()
            
            if total_visitors > 0:
                self.current_value = (total_conversions / total_visitors) * 100
            else:
                self.current_value = 0
                
            # Update historical data
            self.historical_data.append({
                'timestamp': datetime.now(),
                'value': self.current_value
            })
            
        except Exception as e:
            self.logger.error(f"Error updating conversion metric: {e}")
            raise

    def get_historical_data(self, time_range: str) -> pd.DataFrame:
        """Get historical conversion data."""
        try:
            days = int(time_range.replace('d', ''))
            start_date = datetime.now() - timedelta(days=days)
            
            data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', start_date)]
            )
            
            # Calculate daily conversion rates
            daily_data = data.groupby(pd.Grouper(key='timestamp', freq='D')).agg({
                'visitors': 'sum',
                'conversions': 'sum'
            }).reset_index()
            
            daily_data['value'] = (daily_data['conversions'] / daily_data['visitors']) * 100
            return daily_data[['timestamp', 'value']]
            
        except Exception as e:
            self.logger.error(f"Error getting historical conversion data: {e}")
            return pd.DataFrame()


class EngagementMetric(MetricTracker):
    """Tracks engagement-related metrics."""

    def update(self):
        """Update engagement metric."""
        try:
            # Get latest engagement data
            engagement_data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', datetime.now() - timedelta(days=1))]
            )
            
            # Calculate engagement rate
            total_interactions = engagement_data['interactions'].sum()
            total_impressions = engagement_data['impressions'].sum()
            
            if total_impressions > 0:
                self.current_value = (total_interactions / total_impressions) * 100
            else:
                self.current_value = 0
                
            # Update historical data
            self.historical_data.append({
                'timestamp': datetime.now(),
                'value': self.current_value
            })
            
        except Exception as e:
            self.logger.error(f"Error updating engagement metric: {e}")
            raise

    def get_historical_data(self, time_range: str) -> pd.DataFrame:
        """Get historical engagement data."""
        try:
            days = int(time_range.replace('d', ''))
            start_date = datetime.now() - timedelta(days=days)
            
            data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', start_date)]
            )
            
            # Calculate daily engagement rates
            daily_data = data.groupby(pd.Grouper(key='timestamp', freq='D')).agg({
                'interactions': 'sum',
                'impressions': 'sum'
            }).reset_index()
            
            daily_data['value'] = (daily_data['interactions'] / daily_data['impressions']) * 100
            return daily_data[['timestamp', 'value']]
            
        except Exception as e:
            self.logger.error(f"Error getting historical engagement data: {e}")
            return pd.DataFrame()


class RevenueMetric(MetricTracker):
    """Tracks revenue-related metrics."""

    def update(self):
        """Update revenue metric."""
        try:
            # Get latest revenue data
            revenue_data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', datetime.now() - timedelta(days=1))]
            )
            
            # Calculate average revenue per customer
            total_revenue = revenue_data['revenue'].sum()
            total_customers = revenue_data['customers'].sum()
            
            if total_customers > 0:
                self.current_value = total_revenue / total_customers
            else:
                self.current_value = 0
                
            # Update historical data
            self.historical_data.append({
                'timestamp': datetime.now(),
                'value': self.current_value
            })
            
        except Exception as e:
            self.logger.error(f"Error updating revenue metric: {e}")
            raise

    def get_historical_data(self, time_range: str) -> pd.DataFrame:
        """Get historical revenue data."""
        try:
            days = int(time_range.replace('d', ''))
            start_date = datetime.now() - timedelta(days=days)
            
            data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', start_date)]
            )
            
            # Calculate daily revenue per customer
            daily_data = data.groupby(pd.Grouper(key='timestamp', freq='D')).agg({
                'revenue': 'sum',
                'customers': 'sum'
            }).reset_index()
            
            daily_data['value'] = daily_data['revenue'] / daily_data['customers']
            return daily_data[['timestamp', 'value']]
            
        except Exception as e:
            self.logger.error(f"Error getting historical revenue data: {e}")
            return pd.DataFrame()


class SocialMetric(MetricTracker):
    """Tracks social media metrics."""

    def update(self):
        """Update social media metric."""
        try:
            # Get latest social media data
            social_data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', datetime.now() - timedelta(days=1))]
            )
            
            # Calculate social media engagement score
            engagement_weights = {
                'likes': 1,
                'comments': 2,
                'shares': 3,
                'saves': 4
            }
            
            weighted_engagement = sum(
                social_data[metric].sum() * weight
                for metric, weight in engagement_weights.items()
            )
            
            total_posts = social_data['posts'].sum()
            
            if total_posts > 0:
                self.current_value = weighted_engagement / total_posts
            else:
                self.current_value = 0
                
            # Update historical data
            self.historical_data.append({
                'timestamp': datetime.now(),
                'value': self.current_value
            })
            
        except Exception as e:
            self.logger.error(f"Error updating social media metric: {e}")
            raise

    def get_historical_data(self, time_range: str) -> pd.DataFrame:
        """Get historical social media data."""
        try:
            days = int(time_range.replace('d', ''))
            start_date = datetime.now() - timedelta(days=days)
            
            data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', start_date)]
            )
            
            # Calculate daily social media engagement scores
            engagement_weights = {
                'likes': 1,
                'comments': 2,
                'shares': 3,
                'saves': 4
            }
            
            daily_data = data.groupby(pd.Grouper(key='timestamp', freq='D')).agg({
                **{metric: 'sum' for metric in engagement_weights.keys()},
                'posts': 'sum'
            }).reset_index()
            
            daily_data['value'] = sum(
                daily_data[metric] * weight
                for metric, weight in engagement_weights.items()
            ) / daily_data['posts']
            
            return daily_data[['timestamp', 'value']]
            
        except Exception as e:
            self.logger.error(f"Error getting historical social media data: {e}")
            return pd.DataFrame()


class LocalMetric(MetricTracker):
    """Tracks local business metrics."""

    def update(self):
        """Update local business metric."""
        try:
            # Get latest local business data
            local_data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', datetime.now() - timedelta(days=1))]
            )
            
            # Calculate local business score
            metric_weights = {
                'gmb_views': 1,
                'gmb_actions': 2,
                'local_reviews': 3,
                'direction_requests': 2
            }
            
            weighted_score = sum(
                local_data[metric].sum() * weight
                for metric, weight in metric_weights.items()
            )
            
            total_days = len(local_data['timestamp'].unique())
            
            if total_days > 0:
                self.current_value = weighted_score / total_days
            else:
                self.current_value = 0
                
            # Update historical data
            self.historical_data.append({
                'timestamp': datetime.now(),
                'value': self.current_value
            })
            
        except Exception as e:
            self.logger.error(f"Error updating local business metric: {e}")
            raise

    def get_historical_data(self, time_range: str) -> pd.DataFrame:
        """Get historical local business data."""
        try:
            days = int(time_range.replace('d', ''))
            start_date = datetime.now() - timedelta(days=days)
            
            data = pd.read_parquet(
                self.config.source,
                filters=[('timestamp', '>=', start_date)]
            )
            
            # Calculate daily local business scores
            metric_weights = {
                'gmb_views': 1,
                'gmb_actions': 2,
                'local_reviews': 3,
                'direction_requests': 2
            }
            
            daily_data = data.groupby(pd.Grouper(key='timestamp', freq='D')).agg({
                metric: 'sum' for metric in metric_weights.keys()
            }).reset_index()
            
            daily_data['value'] = sum(
                daily_data[metric] * weight
                for metric, weight in metric_weights.items()
            )
            
            return daily_data[['timestamp', 'value']]
            
        except Exception as e:
            self.logger.error(f"Error getting historical local business data: {e}")
            return pd.DataFrame()
