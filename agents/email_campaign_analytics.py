"""Email campaign analytics and A/B testing system."""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from enum import Enum

@dataclass
class EmailMetrics:
    """Email campaign metrics."""
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    replied: int = 0
    bounced: int = 0
    unsubscribed: int = 0
    
    @property
    def open_rate(self) -> float:
        """Calculate email open rate."""
        return (self.opened / self.delivered * 100) if self.delivered > 0 else 0
    
    @property
    def click_rate(self) -> float:
        """Calculate click-through rate."""
        return (self.clicked / self.opened * 100) if self.opened > 0 else 0
    
    @property
    def reply_rate(self) -> float:
        """Calculate reply rate."""
        return (self.replied / self.delivered * 100) if self.delivered > 0 else 0

class VariantType(Enum):
    """Types of email variants for A/B testing."""
    SUBJECT = "subject"
    CONTENT = "content"
    SEND_TIME = "send_time"
    SENDER_NAME = "sender_name"

@dataclass
class ABTestVariant:
    """A/B test variant configuration."""
    variant_type: VariantType
    variant_name: str
    content: str
    metrics: EmailMetrics = EmailMetrics()

class EmailAnalytics:
    """Handles email campaign analytics and A/B testing."""
    
    def __init__(self, storage_path: str = "email_analytics.json"):
        """Initialize analytics system."""
        self.storage_path = storage_path
        self.campaigns: Dict[str, Dict[str, ABTestVariant]] = {}
        self.load_analytics()
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        self.logger = logging.getLogger("EmailAnalytics")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def load_analytics(self):
        """Load analytics data from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for campaign_id, variants in data.items():
                    self.campaigns[campaign_id] = {
                        name: ABTestVariant(**variant) 
                        for name, variant in variants.items()
                    }
        except FileNotFoundError:
            self.logger.info(f"No existing analytics file found at {self.storage_path}")
    
    def save_analytics(self):
        """Save analytics data to storage."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.campaigns, f, default=lambda x: x.__dict__)
    
    def create_ab_test(
        self,
        campaign_id: str,
        variant_type: VariantType,
        variants: Dict[str, str]
    ) -> None:
        """Create a new A/B test campaign."""
        if campaign_id in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} already exists")
        
        self.campaigns[campaign_id] = {
            name: ABTestVariant(variant_type, name, content)
            for name, content in variants.items()
        }
        self.logger.info(f"Created A/B test campaign {campaign_id} with {len(variants)} variants")
        self.save_analytics()
    
    def update_metrics(
        self,
        campaign_id: str,
        variant_name: str,
        metric_type: str,
        value: int = 1
    ) -> None:
        """Update metrics for a specific campaign variant."""
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        if variant_name not in self.campaigns[campaign_id]:
            raise ValueError(f"Variant {variant_name} not found in campaign {campaign_id}")
        
        variant = self.campaigns[campaign_id][variant_name]
        if hasattr(variant.metrics, metric_type):
            current_value = getattr(variant.metrics, metric_type)
            setattr(variant.metrics, metric_type, current_value + value)
            self.logger.info(
                f"Updated {metric_type} for campaign {campaign_id}, "
                f"variant {variant_name} to {current_value + value}"
            )
            self.save_analytics()
        else:
            raise ValueError(f"Invalid metric type: {metric_type}")
    
    def get_campaign_results(self, campaign_id: str) -> Dict:
        """Get comprehensive results for a campaign."""
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        variants = self.campaigns[campaign_id]
        results = {
            "campaign_id": campaign_id,
            "variants": {},
            "winner": None,
            "confidence_level": None
        }
        
        # Calculate metrics for each variant
        for name, variant in variants.items():
            results["variants"][name] = {
                "metrics": variant.metrics.__dict__,
                "rates": {
                    "open_rate": variant.metrics.open_rate,
                    "click_rate": variant.metrics.click_rate,
                    "reply_rate": variant.metrics.reply_rate
                }
            }
        
        # Determine winner based on click-through rate
        max_ctr = max(
            v["rates"]["click_rate"] 
            for v in results["variants"].values()
        )
        winners = [
            name for name, data in results["variants"].items()
            if data["rates"]["click_rate"] == max_ctr
        ]
        
        if len(winners) == 1:
            results["winner"] = winners[0]
            # Calculate confidence level using basic statistical method
            total_clicks = sum(
                v.metrics.clicked 
                for v in variants.values()
            )
            winner_clicks = variants[winners[0]].metrics.clicked
            confidence = (winner_clicks / total_clicks * 100) if total_clicks > 0 else 0
            results["confidence_level"] = confidence
        
        return results
    
    def get_analytics_report(self, days: int = 30) -> Dict:
        """Generate analytics report for all campaigns."""
        cutoff_date = datetime.now() - timedelta(days=days)
        report = {
            "total_campaigns": len(self.campaigns),
            "total_emails_sent": 0,
            "average_open_rate": 0,
            "average_click_rate": 0,
            "average_reply_rate": 0,
            "best_performing_campaigns": [],
            "variant_performance": {}
        }
        
        total_delivered = 0
        total_opened = 0
        total_clicked = 0
        total_replied = 0
        
        for campaign_id, variants in self.campaigns.items():
            campaign_metrics = EmailMetrics()
            for variant in variants.values():
                campaign_metrics.sent += variant.metrics.sent
                campaign_metrics.delivered += variant.metrics.delivered
                campaign_metrics.opened += variant.metrics.opened
                campaign_metrics.clicked += variant.metrics.clicked
                campaign_metrics.replied += variant.metrics.replied
                
                total_delivered += variant.metrics.delivered
                total_opened += variant.metrics.opened
                total_clicked += variant.metrics.clicked
                total_replied += variant.metrics.replied
            
            report["total_emails_sent"] += campaign_metrics.sent
            report["best_performing_campaigns"].append({
                "campaign_id": campaign_id,
                "open_rate": campaign_metrics.open_rate,
                "click_rate": campaign_metrics.click_rate,
                "reply_rate": campaign_metrics.reply_rate
            })
        
        # Calculate averages
        if total_delivered > 0:
            report["average_open_rate"] = (total_opened / total_delivered) * 100
            report["average_click_rate"] = (total_clicked / total_opened) * 100 if total_opened > 0 else 0
            report["average_reply_rate"] = (total_replied / total_delivered) * 100
        
        # Sort best performing campaigns by click rate
        report["best_performing_campaigns"].sort(
            key=lambda x: x["click_rate"],
            reverse=True
        )
        
        return report
