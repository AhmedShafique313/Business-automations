"""
Trend Expert Validator
Validates trends using DeepSeek-powered analysis.
"""

import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
import json
import asyncio
from dataclasses import dataclass, asdict
import numpy as np

from ..utils.deepseek_integration import DeepSeekIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationMetrics:
    """Metrics for trend validation."""
    authenticity_score: float
    sustainability_score: float
    market_fit_score: float
    scalability_score: float
    risk_score: float
    opportunity_score: float
    timing_score: float
    competitive_advantage: float
    resource_requirements: Dict[str, float]
    success_probability: float

@dataclass
class ValidationFeedback:
    """Feedback from trend validation."""
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    recommendations: List[str]
    improvement_areas: Dict[str, List[str]]

@dataclass
class ValidationResult:
    """Result of trend validation."""
    trend_id: str
    timestamp: str
    metrics: ValidationMetrics
    feedback: ValidationFeedback
    status: str
    confidence_score: float
    validator_version: str = "1.0.0"

class TrendExpert:
    """Expert system for validating trends using DeepSeek."""
    
    def __init__(self):
        """Initialize the trend expert."""
        self.deepseek = DeepSeekIntegration()
        self.validation_history: Dict[str, List[ValidationResult]] = {}
        self.validation_thresholds = {
            'authenticity': 0.7,
            'sustainability': 0.6,
            'market_fit': 0.7,
            'scalability': 0.6,
            'risk': 0.3,  # Lower is better
            'success_probability': 0.7
        }
        
    async def validate_trends(
        self,
        trends: List[Dict],
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """Validate a list of trends."""
        try:
            validated_trends = []
            validation_tasks = []
            
            # Create validation tasks
            for trend in trends:
                task = asyncio.create_task(
                    self._validate_trend(trend, context)
                )
                validation_tasks.append(task)
            
            # Wait for all validations
            validation_results = await asyncio.gather(*validation_tasks)
            
            # Process results
            for trend, validation in zip(trends, validation_results):
                if self._meets_thresholds(validation.metrics):
                    validated_trend = {
                        **trend,
                        'validation': asdict(validation)
                    }
                    validated_trends.append(validated_trend)
                    
                    # Update history
                    trend_id = trend.get('trend_id')
                    if trend_id not in self.validation_history:
                        self.validation_history[trend_id] = []
                    self.validation_history[trend_id].append(validation)
            
            return validated_trends
            
        except Exception as e:
            logger.error(f"Trend validation failed: {e}")
            raise
            
    async def get_validation_insights(
        self,
        trend_id: str
    ) -> Optional[Dict]:
        """Get validation insights for a trend."""
        try:
            if trend_id not in self.validation_history:
                return None
            
            validations = self.validation_history[trend_id]
            
            # Analyze validation history with DeepSeek
            insights = await self.deepseek.analyze_text(
                json.dumps([asdict(v) for v in validations]),
                'validation_insights'
            )
            
            return {
                'trend_id': trend_id,
                'validation_count': len(validations),
                'first_validation': asdict(validations[0]),
                'latest_validation': asdict(validations[-1]),
                'metric_trends': self._analyze_metric_trends(validations),
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Failed to get validation insights: {e}")
            raise
            
    async def _validate_trend(
        self,
        trend: Dict,
        context: Optional[Dict] = None
    ) -> ValidationResult:
        """Validate a single trend."""
        try:
            # Analyze with DeepSeek
            analysis = await self.deepseek.analyze_text(
                json.dumps(trend),
                'trend_validation',
                context
            )
            
            # Create metrics
            metrics = ValidationMetrics(
                authenticity_score=analysis['metrics']['authenticity'],
                sustainability_score=analysis['metrics']['sustainability'],
                market_fit_score=analysis['metrics']['market_fit'],
                scalability_score=analysis['metrics']['scalability'],
                risk_score=analysis['metrics']['risk'],
                opportunity_score=analysis['metrics']['opportunity'],
                timing_score=analysis['metrics']['timing'],
                competitive_advantage=analysis['metrics']['competitive_advantage'],
                resource_requirements=analysis['metrics']['resource_requirements'],
                success_probability=analysis['metrics']['success_probability']
            )
            
            # Create feedback
            feedback = ValidationFeedback(
                strengths=analysis['feedback']['strengths'],
                weaknesses=analysis['feedback']['weaknesses'],
                opportunities=analysis['feedback']['opportunities'],
                threats=analysis['feedback']['threats'],
                recommendations=analysis['feedback']['recommendations'],
                improvement_areas=analysis['feedback']['improvement_areas']
            )
            
            # Create validation result
            result = ValidationResult(
                trend_id=trend['trend_id'],
                timestamp=datetime.now().isoformat(),
                metrics=metrics,
                feedback=feedback,
                status='approved' if self._meets_thresholds(metrics) else 'rejected',
                confidence_score=analysis['confidence_score']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Trend validation failed: {e}")
            raise
            
    def _meets_thresholds(self, metrics: ValidationMetrics) -> bool:
        """Check if metrics meet validation thresholds."""
        return all([
            metrics.authenticity_score >= self.validation_thresholds['authenticity'],
            metrics.sustainability_score >= self.validation_thresholds['sustainability'],
            metrics.market_fit_score >= self.validation_thresholds['market_fit'],
            metrics.scalability_score >= self.validation_thresholds['scalability'],
            metrics.risk_score <= self.validation_thresholds['risk'],
            metrics.success_probability >= self.validation_thresholds['success_probability']
        ])
        
    def _analyze_metric_trends(
        self,
        validations: List[ValidationResult]
    ) -> Dict[str, Dict]:
        """Analyze trends in validation metrics."""
        metrics_data = {
            'authenticity': [],
            'sustainability': [],
            'market_fit': [],
            'scalability': [],
            'risk': [],
            'success_probability': []
        }
        
        # Collect metric values
        for validation in validations:
            metrics_data['authenticity'].append(validation.metrics.authenticity_score)
            metrics_data['sustainability'].append(validation.metrics.sustainability_score)
            metrics_data['market_fit'].append(validation.metrics.market_fit_score)
            metrics_data['scalability'].append(validation.metrics.scalability_score)
            metrics_data['risk'].append(validation.metrics.risk_score)
            metrics_data['success_probability'].append(
                validation.metrics.success_probability
            )
        
        # Calculate trends
        trends = {}
        for metric, values in metrics_data.items():
            values = np.array(values)
            trends[metric] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'trend': float(np.polyfit(range(len(values)), values, 1)[0]),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'latest': float(values[-1])
            }
        
        return trends
