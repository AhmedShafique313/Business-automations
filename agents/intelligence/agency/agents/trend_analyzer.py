"""
Trend Analyzer Agent
Analyzes social media trends and viral content patterns using DeepSeek.
"""

import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path
import aiohttp
import numpy as np
from dataclasses import dataclass, asdict
import uuid

from ..utils.deepseek_integration import DeepSeekIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrendMetrics:
    """Metrics for trend analysis."""
    engagement_rate: float
    growth_rate: float
    virality_score: float
    longevity_score: float
    cross_platform_presence: float
    industry_relevance: Dict[str, float]
    demographic_fit: Dict[str, float]
    sentiment_score: float
    conversion_potential: float
    brand_safety_score: float

@dataclass
class TrendSource:
    """Source of a trend."""
    platform: str
    url: Optional[str]
    post_id: Optional[str]
    author: Optional[str]
    timestamp: str
    engagement: Dict[str, Union[int, float]]
    reach: Optional[int]

@dataclass
class TrendPattern:
    """Pattern detected in trend."""
    pattern_type: str
    frequency: float
    impact_score: float
    examples: List[str]
    context: Dict[str, str]

@dataclass
class Trend:
    """Represents a viral trend."""
    trend_id: str
    title: str
    description: str
    category: str
    keywords: List[str]
    metrics: TrendMetrics
    sources: List[TrendSource]
    patterns: List[TrendPattern]
    created_at: str
    updated_at: str
    expiry: str
    status: str
    score: float

class TrendAnalyzer:
    """Agent for analyzing viral trends using DeepSeek."""
    
    def __init__(self):
        """Initialize the trend analyzer."""
        self.deepseek = DeepSeekIntegration()
        self.trends_cache: Dict[str, List[Trend]] = {}
        self.pattern_database: Dict[str, List[TrendPattern]] = {}
        
        # Platform-specific engagement thresholds
        self.engagement_thresholds = {
            'linkedin': {
                'views': 5000,
                'likes': 500,
                'comments': 50,
                'shares': 100
            },
            'medium': {
                'claps': 500,
                'comments': 50,
                'saves': 100,
                'shares': 50
            },
            'instagram': {
                'likes': 5000,
                'comments': 200,
                'saves': 1000,
                'shares': 500
            },
            'youtube': {
                'views': 50000,
                'likes': 5000,
                'comments': 300,
                'shares': 200
            }
        }
        
        # Research-specific metrics
        self.research_metrics = {
            'citations': {
                'high': 100,
                'medium': 50,
                'low': 10
            },
            'impact_factor': {
                'high': 10.0,
                'medium': 5.0,
                'low': 1.0
            }
        }
    
    async def analyze_trends(self, industry: str, platforms: Optional[List[str]] = None) -> List[Trend]:
        """Analyze current trends across platforms."""
        if industry in self.trends_cache:
            logger.info(f"Using cached trends for {industry}")
            return self.trends_cache[industry]
        
        if not platforms:
            platforms = list(self.engagement_thresholds.keys())
        
        try:
            # First try to fetch research trends from cache
            trends = self.trends_cache.get(industry, [])
            
            if not trends:
                # If no trends in cache, analyze the ones we have
                logger.info(f"No trends in cache for {industry}, analyzing available trends")
                raw_trends = await self._fetch_trends(platforms)
                patterns = self._extract_patterns(raw_trends)
                self._update_pattern_database(patterns)
                
                trends = []
                for trend_data in raw_trends:
                    trend = await self._analyze_trend(trend_data, industry)
                    if trend:
                        trends.append(trend)
            
            # Filter and sort trends
            valid_trends = []
            for trend in trends:
                if await self.validate_trend(trend):
                    valid_trends.append(trend)
            
            # Sort by score (descending)
            valid_trends.sort(key=lambda x: x.score, reverse=True)
            
            # Cache the results
            self.trends_cache[industry] = valid_trends
            
            return valid_trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return []
    
    async def validate_trend(self, trend: Trend) -> bool:
        """Validate a trend's potential."""
        try:
            # Check if it's a research trend
            is_research = any(source.platform in ['arXiv', 'PubMed'] for source in trend.sources)
            
            if is_research:
                # Research trends have different validation criteria
                citations = max(source.engagement.get('citations', 0) for source in trend.sources)
                impact = max(source.engagement.get('impact_factor', 0.0) for source in trend.sources)
                
                # Research trends should meet minimum thresholds
                if citations < self.research_metrics['citations']['low']:
                    return False
                if impact < self.research_metrics['impact_factor']['low']:
                    return False
                
                # Research trends should be recent (within last 6 months)
                latest_timestamp = max(datetime.fromisoformat(source.timestamp) for source in trend.sources)
                if (datetime.now() - latest_timestamp).days > 180:
                    return False
                
                return True
            
            # For non-research trends, use regular validation
            for source in trend.sources:
                if not self._is_trend_suitable(trend, source.platform):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating trend: {e}")
            return False
    
    async def _fetch_trends(self, platforms: List[str]) -> List[Dict]:
        """Fetch raw trend data from platforms."""
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_platform_trends(session, platform) for platform in platforms]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            trends = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error fetching trends: {result}")
                    continue
                trends.extend(result)
            
            return trends
    
    async def _fetch_platform_trends(self, session: aiohttp.ClientSession, platform: str) -> List[Dict]:
        """Fetch trends from a specific platform."""
        if platform in ['arXiv', 'PubMed']:
            # For research platforms, return cached data if available
            return self.trends_cache.get(platform, [])
        
        # For other platforms, implement platform-specific fetching
        # This is a placeholder - implement actual API calls here
        return []
    
    def _extract_patterns(self, raw_trends: List[Dict]) -> List[TrendPattern]:
        """Extract patterns from raw trend data."""
        patterns = []
        
        try:
            # Group trends by type
            research_trends = [t for t in raw_trends if t.get('source') in ['arXiv', 'PubMed']]
            social_trends = [t for t in raw_trends if t.get('source') not in ['arXiv', 'PubMed']]
            
            # Extract patterns from research trends
            if research_trends:
                research_pattern = TrendPattern(
                    pattern_type="research_insight",
                    frequency=len(research_trends) / len(raw_trends),
                    impact_score=0.85,  # Research content typically has high impact
                    examples=[
                        "Present research findings",
                        "Explain practical applications",
                        "Show real-world impact"
                    ],
                    context={
                        "tone": "educational",
                        "style": "authoritative",
                        "approach": "data-driven"
                    }
                )
                patterns.append(research_pattern)
            
            # Extract patterns from social trends
            if social_trends:
                social_pattern = TrendPattern(
                    pattern_type="social_engagement",
                    frequency=len(social_trends) / len(raw_trends),
                    impact_score=0.75,
                    examples=[
                        "Share key insights",
                        "Demonstrate applications",
                        "Engage with audience"
                    ],
                    context={
                        "tone": "conversational",
                        "style": "engaging",
                        "approach": "interactive"
                    }
                )
                patterns.append(social_pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return []
    
    async def _analyze_trend(self, trend_data: Dict, industry: str) -> Optional[Trend]:
        """Analyze a trend using DeepSeek."""
        try:
            # Check if it's a research trend
            is_research = trend_data.get('source') in ['arXiv', 'PubMed']
            
            # Create base metrics
            metrics = TrendMetrics(
                engagement_rate=0.8 if is_research else 0.7,
                growth_rate=0.7,
                virality_score=0.75,
                longevity_score=0.9 if is_research else 0.7,
                cross_platform_presence=0.8,
                industry_relevance={industry: 0.9},
                demographic_fit={"18-35": 0.7, "35-50": 0.8, "50+": 0.6},
                sentiment_score=0.8,
                conversion_potential=0.7,
                brand_safety_score=0.95 if is_research else 0.85
            )
            
            # Create source
            source = TrendSource(
                platform=trend_data['source'],
                url=trend_data.get('url'),
                post_id=trend_data.get('post_id'),
                author=trend_data.get('author'),
                timestamp=trend_data.get('timestamp', datetime.now().isoformat()),
                engagement=trend_data.get('engagement', {"views": 5000, "citations": 100}),
                reach=trend_data.get('reach', 10000)
            )
            
            # Create pattern
            pattern = TrendPattern(
                pattern_type="research_insight" if is_research else "social_engagement",
                frequency=0.8,
                impact_score=0.85 if is_research else 0.75,
                examples=[
                    "Present research findings" if is_research else "Share key insights",
                    "Explain practical applications",
                    "Show real-world impact"
                ],
                context={
                    "tone": "educational" if is_research else "conversational",
                    "style": "authoritative" if is_research else "engaging",
                    "approach": "data-driven" if is_research else "interactive"
                }
            )
            
            # Create trend
            trend = Trend(
                trend_id=str(uuid.uuid4()),
                title=trend_data['title'],
                description=trend_data['description'],
                category=industry,
                keywords=trend_data.get('keywords', []),
                metrics=metrics,
                sources=[source],
                patterns=[pattern],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                expiry=(datetime.now() + timedelta(days=30 if is_research else 7)).isoformat(),
                status="active",
                score=0.85 if is_research else 0.75
            )
            
            return trend
            
        except Exception as e:
            logger.error(f"Error analyzing trend: {e}")
            return None
    
    async def get_trend_recommendations(
        self,
        industry: str,
        platform: str,
        content_type: Optional[str] = None
    ) -> List[Dict]:
        """Get trend recommendations for content creation."""
        try:
            # Get cached trends or analyze new ones
            if industry not in self.trends_cache:
                await self.analyze_trends(industry, [platform])
            
            trends = self.trends_cache[industry]
            
            # Filter and score trends for the platform
            recommendations = []
            for trend in trends:
                if await self._is_trend_suitable(trend, platform, content_type):
                    recommendation = {
                        'trend': asdict(trend),
                        'content_suggestions': await self._generate_content_suggestions(
                            trend,
                            platform,
                            content_type
                        ),
                        'estimated_impact': await self._estimate_trend_impact(
                            trend,
                            platform
                        )
                    }
                    recommendations.append(recommendation)
            
            return sorted(
                recommendations,
                key=lambda x: x['estimated_impact']['overall_score'],
                reverse=True
            )
            
        except Exception as e:
            logger.error(f"Failed to get trend recommendations: {e}")
            raise
            
    async def validate_trend(self, trend: Trend) -> Dict:
        """Validate a trend's potential."""
        try:
            # Analyze with DeepSeek
            validation = await self.deepseek.analyze_text(
                json.dumps(asdict(trend)),
                'trend_validation',
                {
                    'patterns': self.pattern_database,
                    'thresholds': self.engagement_thresholds
                }
            )
            
            return validation
            
        except Exception as e:
            logger.error(f"Trend validation failed: {e}")
            raise
            
    async def _fetch_trends(self, platforms: List[str]) -> List[Dict]:
        """Fetch raw trend data from platforms."""
        try:
            raw_trends = []
            async with aiohttp.ClientSession() as session:
                for platform in platforms:
                    platform_trends = await self._fetch_platform_trends(
                        session,
                        platform
                    )
                    raw_trends.extend(platform_trends)
            return raw_trends
            
        except Exception as e:
            logger.error(f"Failed to fetch trends: {e}")
            raise
            
    async def _fetch_platform_trends(
        self,
        session: aiohttp.ClientSession,
        platform: str
    ) -> List[Dict]:
        """Fetch trends from a specific platform."""
        # TODO: Implement actual API calls
        # For now, return mock data
        return [
            {
                'platform': platform,
                'title': f'Trending topic on {platform}',
                'engagement': {
                    'views': 150000,
                    'likes': 15000,
                    'shares': 2000,
                    'comments': 800
                }
            }
        ]
            
    async def _extract_patterns(self, raw_trends: List[Dict]) -> List[TrendPattern]:
        """Extract patterns from raw trend data."""
        try:
            # Analyze patterns with DeepSeek
            patterns_text = await self.deepseek.generate_content(
                self._create_pattern_analysis_prompt(raw_trends),
                max_length=1000,
                temperature=0.3
            )
            
            # Parse patterns
            patterns = []
            pattern_data = json.loads(patterns_text[0])
            for p in pattern_data['patterns']:
                pattern = TrendPattern(
                    pattern_type=p['type'],
                    frequency=p['frequency'],
                    impact_score=p['impact_score'],
                    examples=p['examples'],
                    context=p['context']
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern extraction failed: {e}")
            raise
            
    def _update_pattern_database(self, new_patterns: List[TrendPattern]):
        """Update pattern database with new patterns."""
        for pattern in new_patterns:
            if pattern.pattern_type not in self.pattern_database:
                self.pattern_database[pattern.pattern_type] = []
            
            self.pattern_database[pattern.pattern_type].append(pattern)
            
            # Keep only recent patterns
            self.pattern_database[pattern.pattern_type] = sorted(
                self.pattern_database[pattern.pattern_type],
                key=lambda x: x.frequency * x.impact_score,
                reverse=True
            )[:100]  # Keep top 100 patterns per type
            
    async def _analyze_trend(self, trend_data: Dict, industry: str) -> Trend:
        """Analyze a trend using DeepSeek."""
        try:
            # Generate comprehensive analysis
            analysis = await self.deepseek.analyze_text(
                json.dumps(trend_data),
                'trend_analysis',
                {'industry': industry}
            )
            
            # Create trend metrics
            metrics = TrendMetrics(
                engagement_rate=analysis['metrics']['engagement_rate'],
                growth_rate=analysis['metrics']['growth_rate'],
                virality_score=analysis['metrics']['virality_score'],
                longevity_score=analysis['metrics']['longevity_score'],
                cross_platform_presence=analysis['metrics']['cross_platform_presence'],
                industry_relevance=analysis['metrics']['industry_relevance'],
                demographic_fit=analysis['metrics']['demographic_fit'],
                sentiment_score=analysis['metrics']['sentiment_score'],
                conversion_potential=analysis['metrics']['conversion_potential'],
                brand_safety_score=analysis['metrics']['brand_safety_score']
            )
            
            # Create trend source
            source = TrendSource(
                platform=trend_data['platform'],
                url=trend_data.get('url'),
                post_id=trend_data.get('post_id'),
                author=trend_data.get('author'),
                timestamp=datetime.now().isoformat(),
                engagement=trend_data['engagement'],
                reach=trend_data.get('reach')
            )
            
            # Calculate expiry
            expiry = datetime.now() + timedelta(days=analysis['estimated_lifespan'])
            
            # Create trend object
            trend = Trend(
                trend_id=str(uuid.uuid4()),
                title=trend_data['title'],
                description=analysis['description'],
                category=analysis['category'],
                keywords=analysis['keywords'],
                metrics=metrics,
                sources=[source],
                patterns=analysis['patterns'],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                expiry=expiry.isoformat(),
                status='active',
                score=analysis['overall_score']
            )
            
            return trend
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            raise
            
    async def _is_trend_suitable(
        self,
        trend: Trend,
        platform: str,
        content_type: Optional[str] = None
    ) -> bool:
        """Check if a trend is suitable for a platform."""
        try:
            # Check with DeepSeek
            analysis = await self.deepseek.analyze_text(
                json.dumps(asdict(trend)),
                'platform_fit',
                {
                    'platform': platform,
                    'content_type': content_type
                }
            )
            
            return analysis['is_suitable'] and analysis['fit_score'] >= 0.7
            
        except Exception as e:
            logger.error(f"Suitability check failed: {e}")
            return False
            
    async def _generate_content_suggestions(
        self,
        trend: Trend,
        platform: str,
        content_type: Optional[str] = None
    ) -> List[Dict]:
        """Generate content suggestions for a trend."""
        try:
            # Generate suggestions with DeepSeek
            suggestions_text = await self.deepseek.generate_content(
                self._create_suggestion_prompt(trend, platform, content_type),
                max_length=1000,
                temperature=0.7,
                num_return_sequences=3
            )
            
            # Parse suggestions
            suggestions = []
            for text in suggestions_text:
                suggestion = json.loads(text)
                suggestions.append({
                    'angle': suggestion['angle'],
                    'hook': suggestion['hook'],
                    'key_elements': suggestion['key_elements'],
                    'estimated_performance': suggestion['estimated_performance']
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate content suggestions: {e}")
            raise
            
    async def _estimate_trend_impact(
        self,
        trend: Trend,
        platform: str
    ) -> Dict:
        """Estimate potential impact of a trend."""
        try:
            # Analyze with DeepSeek
            impact = await self.deepseek.analyze_text(
                json.dumps(asdict(trend)),
                'impact_estimation',
                {'platform': platform}
            )
            
            return {
                'overall_score': impact['overall_score'],
                'engagement_potential': impact['engagement_potential'],
                'conversion_potential': impact['conversion_potential'],
                'brand_lift_potential': impact['brand_lift_potential'],
                'risks': impact['risks'],
                'opportunities': impact['opportunities']
            }
            
        except Exception as e:
            logger.error(f"Impact estimation failed: {e}")
            raise
            
    def _create_pattern_analysis_prompt(self, trends: List[Dict]) -> str:
        """Create prompt for pattern analysis."""
        return f"""
            Analyze the following trends to identify patterns:
            
            Trends:
            {json.dumps(trends, indent=2)}
            
            Identify:
            1. Common patterns in content structure
            2. Engagement patterns
            3. Timing patterns
            4. Cross-platform patterns
            
            Format the response as a JSON object with:
            1. Pattern type
            2. Frequency
            3. Impact score
            4. Examples
            5. Context
            """
            
    def _create_suggestion_prompt(
        self,
        trend: Trend,
        platform: str,
        content_type: Optional[str]
    ) -> str:
        """Create prompt for content suggestions."""
        return f"""
            Generate content suggestions for the following trend:
            
            Trend:
            {json.dumps(asdict(trend), indent=2)}
            
            Platform: {platform}
            Content Type: {content_type if content_type else 'any'}
            
            Provide 3 unique content angles that:
            1. Leverage the trend's viral elements
            2. Fit the platform's best practices
            3. Maximize engagement potential
            4. Maintain brand safety
            
            Format each suggestion as a JSON object with:
            1. Content angle
            2. Hook
            3. Key elements
            4. Estimated performance metrics
            """
