import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json

from .case_study_analyzer import CaseStudyAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitors and reports on agent performance across the system."""
    
    def __init__(self, config_path: str):
        """Initialize the performance monitor."""
        self.config = self._load_config(config_path)
        self.analyzer = CaseStudyAnalyzer(config_path)
        self.scheduler = BackgroundScheduler()
        self.metrics_history = {}
        self.initialize_scheduler()
    
    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def initialize_scheduler(self) -> None:
        """Initialize the scheduler for periodic monitoring and reporting."""
        # Schedule weekly performance report
        self.scheduler.add_job(
            self.generate_weekly_report,
            CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_report'
        )
        
        # Schedule daily metrics collection
        self.scheduler.add_job(
            self.collect_daily_metrics,
            CronTrigger(hour=0, minute=0),
            id='daily_metrics'
        )
        
        # Start the scheduler
        self.scheduler.start()
    
    def collect_daily_metrics(self) -> Dict:
        """Collect daily performance metrics from all agents."""
        metrics = {}
        
        try:
            # Collect metrics from each agent type
            metrics.update(self._collect_content_metrics())
            metrics.update(self._collect_engagement_metrics())
            metrics.update(self._collect_conversion_metrics())
            metrics.update(self._collect_audience_metrics())
            
            # Store metrics in history
            date_key = datetime.now().strftime('%Y-%m-%d')
            self.metrics_history[date_key] = metrics
            
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to collect daily metrics: {e}")
            return {}
    
    def _collect_content_metrics(self) -> Dict:
        """Collect content-related performance metrics."""
        return {
            'content': {
                'posts_created': 0,  # To be implemented
                'content_quality_score': 0.0,  # To be implemented
                'engagement_rate': 0.0,  # To be implemented
                'reach': 0  # To be implemented
            }
        }
    
    def _collect_engagement_metrics(self) -> Dict:
        """Collect engagement-related performance metrics."""
        return {
            'engagement': {
                'likes': 0,  # To be implemented
                'comments': 0,  # To be implemented
                'shares': 0,  # To be implemented
                'saves': 0  # To be implemented
            }
        }
    
    def _collect_conversion_metrics(self) -> Dict:
        """Collect conversion-related performance metrics."""
        return {
            'conversion': {
                'leads_generated': 0,  # To be implemented
                'conversion_rate': 0.0,  # To be implemented
                'revenue_generated': 0.0  # To be implemented
            }
        }
    
    def _collect_audience_metrics(self) -> Dict:
        """Collect audience-related performance metrics."""
        return {
            'audience': {
                'follower_growth': 0,  # To be implemented
                'audience_engagement_rate': 0.0,  # To be implemented
                'audience_retention_rate': 0.0  # To be implemented
            }
        }
    
    def generate_weekly_report(self) -> None:
        """Generate and send weekly performance report."""
        try:
            # Get metrics for the past week
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            weekly_metrics = self._aggregate_weekly_metrics(start_date, end_date)
            
            # Generate report using case study analyzer
            self.analyzer.generate_performance_report(
                weekly_metrics,
                email="gagan@designgaga.ca"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
    
    def _aggregate_weekly_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Aggregate metrics for the specified date range."""
        metrics = {}
        
        # Filter metrics within date range
        date_range_metrics = {
            date: metrics for date, metrics in self.metrics_history.items()
            if start_date <= datetime.strptime(date, '%Y-%m-%d') <= end_date
        }
        
        if not date_range_metrics:
            return {}
        
        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame.from_dict(date_range_metrics, orient='index')
        
        # Aggregate metrics
        metrics = {
            'content': {
                'total_posts': df['content.posts_created'].sum(),
                'avg_quality_score': df['content.content_quality_score'].mean(),
                'avg_engagement_rate': df['content.engagement_rate'].mean(),
                'total_reach': df['content.reach'].sum()
            },
            'engagement': {
                'total_likes': df['engagement.likes'].sum(),
                'total_comments': df['engagement.comments'].sum(),
                'total_shares': df['engagement.shares'].sum(),
                'total_saves': df['engagement.saves'].sum()
            },
            'conversion': {
                'total_leads': df['conversion.leads_generated'].sum(),
                'avg_conversion_rate': df['conversion.conversion_rate'].mean(),
                'total_revenue': df['conversion.revenue_generated'].sum()
            },
            'audience': {
                'net_follower_growth': df['audience.follower_growth'].sum(),
                'avg_engagement_rate': df['audience.audience_engagement_rate'].mean(),
                'avg_retention_rate': df['audience.audience_retention_rate'].mean()
            }
        }
        
        return metrics
    
    def _format_report_email(self, report: Dict) -> str:
        """Format the performance report as an HTML email."""
        html = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .metric { margin: 10px 0; }
                    .metric-title { font-weight: bold; }
                    .recommendation { margin: 5px 0; }
                    .status-good { color: green; }
                    .status-warning { color: orange; }
                    .status-bad { color: red; }
                </style>
            </head>
            <body>
                <h2>Weekly Performance Report</h2>
                <h3>Performance Metrics</h3>
        """
        
        # Add metrics
        for category, metrics in report['metrics'].items():
            html += f"<div class='metric-category'><h4>{category.title()}</h4>"
            for metric, value in metrics.items():
                status_class = self._get_metric_status_class(value, metric)
                html += f"""
                    <div class='metric'>
                        <span class='metric-title'>{metric.replace('_', ' ').title()}:</span>
                        <span class='{status_class}'>{value}</span>
                    </div>
                """
            html += "</div>"
        
        # Add recommendations
        html += "<h3>Recommendations</h3>"
        for category, recs in report['recommendations'].items():
            html += f"<h4>{recs['title']}</h4><ul>"
            for rec in recs['recommendations']:
                html += f"<li class='recommendation'>{rec}</li>"
            html += "</ul>"
        
        # Add next actions
        html += "<h3>Priority Actions</h3><ul>"
        for action in report['next_actions']:
            html += f"<li>{action}</li>"
        html += "</ul></body></html>"
        
        return html
    
    def _get_metric_status_class(self, value: float, metric: str) -> str:
        """Determine the status class for a metric value."""
        # Implement logic to determine if metric is good/warning/bad
        return 'status-good'  # Placeholder
    
    def _send_email(self, recipient: str, subject: str, html_content: str) -> None:
        """Send an email with the performance report."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config['email']['sender']
            msg['To'] = recipient
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.config['email']['smtp_server'], 
                            self.config['email']['smtp_port']) as server:
                server.starttls()
                server.login(
                    self.config['email']['username'],
                    self.config['email']['password']
                )
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
