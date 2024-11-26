"""Content Generation Agent for creating personalized content.

This agent is responsible for:
- Generating personalized email content
- Creating social media posts
- Writing blog articles and SEO content
- Managing GMB posts and updates
- Analyzing content performance
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from config_manager import ConfigManager
from utils.seo_analyzer import SEOAnalyzer
from utils.content_optimizer import ContentOptimizer
from utils.gmb_client import GMBClient
from .researcher_agent import LeadProfile

class ContentAgent:
    """Agent responsible for content generation and optimization."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.seo = SEOAnalyzer()
        self.optimizer = ContentOptimizer()
        self.gmb = GMBClient()
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI
        openai.api_key = self.config.get('openai_api_key')
        
    def generate_email_content(self, lead: LeadProfile, content_type: str) -> str:
        """Generate personalized email content."""
        prompt = self._create_email_prompt(lead, content_type)
        
        response = self._generate_content(
            prompt,
            system_prompt="You are an expert business development specialist crafting personalized emails.",
            max_tokens=500
        )
        
        # Optimize content
        optimized = self.optimizer.optimize_email(response, lead)
        return optimized
    
    def generate_social_post(self, platform: str, topic: str, target_audience: Dict) -> str:
        """Generate platform-specific social media content."""
        prompt = self._create_social_prompt(platform, topic, target_audience)
        
        response = self._generate_content(
            prompt,
            system_prompt=f"You are a {platform} marketing specialist creating engaging content.",
            max_tokens=300
        )
        
        # Optimize for platform
        optimized = self.optimizer.optimize_social(response, platform)
        return optimized
    
    def generate_blog_post(self, topic: str, keywords: List[str], target_audience: Dict) -> Dict:
        """Generate SEO-optimized blog content."""
        outline_prompt = self._create_blog_outline_prompt(topic, keywords, target_audience)
        
        outline = self._generate_content(
            outline_prompt,
            system_prompt="You are an SEO content strategist creating article outlines.",
            max_tokens=300
        )
        
        content_prompt = self._create_blog_content_prompt(topic, outline, keywords)
        content = self._generate_content(
            content_prompt,
            system_prompt="You are an expert content writer creating engaging blog posts.",
            max_tokens=2000
        )
        
        # SEO optimization
        optimized = self.optimizer.optimize_blog(content, keywords)
        seo_score = self.seo.analyze_content(optimized, keywords)
        
        return {
            'title': topic,
            'content': optimized,
            'seo_score': seo_score,
            'keywords': keywords,
            'outline': outline
        }
    
    def create_gmb_post(self, post_type: str, business_data: Dict) -> Dict:
        """Create Google My Business post."""
        prompt = self._create_gmb_prompt(post_type, business_data)
        
        content = self._generate_content(
            prompt,
            system_prompt="You are a local business marketing specialist.",
            max_tokens=300
        )
        
        # Optimize for GMB
        optimized = self.optimizer.optimize_gmb(content, post_type)
        
        return {
            'content': optimized,
            'type': post_type,
            'schedule_time': self._get_optimal_posting_time(post_type)
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _generate_content(self, prompt: str, system_prompt: str, max_tokens: int) -> str:
        """Generate content using OpenAI."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Content generation failed: {str(e)}")
            raise
    
    def _create_email_prompt(self, lead: LeadProfile, content_type: str) -> str:
        """Create prompt for email content generation."""
        return f"""
        Create a personalized {content_type} email for a {lead.business_type} professional.
        
        Business Name: {lead.business_name}
        Location: {lead.location}
        Previous Interactions: {len(lead.interaction_history) if lead.interaction_history else 0}
        
        Key Points:
        - Acknowledge their expertise in {lead.business_type}
        - Reference their location: {lead.location}
        - Include social proof relevant to their industry
        - Clear call to action
        
        Tone: Professional but conversational
        Length: 2-3 short paragraphs
        """
    
    def _create_social_prompt(self, platform: str, topic: str, target_audience: Dict) -> str:
        """Create prompt for social media content."""
        return f"""
        Create a {platform} post about {topic}.
        
        Target Audience:
        - Industry: {target_audience.get('industry')}
        - Location: {target_audience.get('location')}
        - Interests: {', '.join(target_audience.get('interests', []))}
        
        Key Requirements:
        - Platform-appropriate tone and style
        - Engaging hook
        - Relevant hashtags
        - Call to action
        
        Content Type: {platform} post
        """
    
    def _create_blog_outline_prompt(self, topic: str, keywords: List[str], target_audience: Dict) -> str:
        """Create prompt for blog outline."""
        return f"""
        Create a detailed outline for a blog post about {topic}.
        
        Target Keywords: {', '.join(keywords)}
        
        Target Audience:
        - Industry: {target_audience.get('industry')}
        - Pain Points: {', '.join(target_audience.get('pain_points', []))}
        
        Include:
        - H1 title
        - 3-4 main sections (H2)
        - 2-3 subsections (H3) per main section
        - Key points to cover in each section
        """
    
    def _create_gmb_prompt(self, post_type: str, business_data: Dict) -> str:
        """Create prompt for GMB post."""
        return f"""
        Create a Google My Business post for a {business_data['type']} business.
        
        Business Details:
        - Name: {business_data['name']}
        - Location: {business_data['location']}
        - Specialties: {', '.join(business_data['specialties'])}
        
        Post Type: {post_type}
        Include:
        - Attention-grabbing headline
        - Relevant local keywords
        - Clear value proposition
        - Call to action
        """
    
    def _get_optimal_posting_time(self, post_type: str) -> datetime:
        """Determine optimal posting time based on engagement data."""
        # Implementation would analyze historical engagement data
        # For now, return current time + 1 day at 10 AM
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    def analyze_content_performance(self, content_id: str, metrics: Dict) -> Dict:
        """Analyze content performance and generate insights."""
        analysis = {
            'engagement_rate': self._calculate_engagement_rate(metrics),
            'conversion_rate': self._calculate_conversion_rate(metrics),
            'sentiment_score': self._analyze_sentiment(metrics.get('comments', [])),
            'recommendations': self._generate_recommendations(metrics)
        }
        
        # Log analysis for learning
        self.logger.info(f"Content performance analysis for {content_id}: {analysis}")
        
        return analysis
    
    def _calculate_engagement_rate(self, metrics: Dict) -> float:
        """Calculate content engagement rate."""
        total_reach = metrics.get('reach', 0)
        if total_reach == 0:
            return 0.0
            
        engagements = (
            metrics.get('likes', 0) +
            metrics.get('comments', 0) +
            metrics.get('shares', 0) +
            metrics.get('clicks', 0)
        )
        
        return (engagements / total_reach) * 100
    
    def _calculate_conversion_rate(self, metrics: Dict) -> float:
        """Calculate content conversion rate."""
        total_views = metrics.get('views', 0)
        if total_views == 0:
            return 0.0
            
        conversions = metrics.get('conversions', 0)
        return (conversions / total_views) * 100
    
    def _analyze_sentiment(self, comments: List[str]) -> float:
        """Analyze sentiment of engagement."""
        if not comments:
            return 0.0
            
        # Implementation would use sentiment analysis
        # For now, return neutral sentiment
        return 0.5
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate content improvement recommendations."""
        recommendations = []
        
        engagement_rate = self._calculate_engagement_rate(metrics)
        if engagement_rate < 2.0:
            recommendations.append("Consider more engaging hooks and calls to action")
            
        conversion_rate = self._calculate_conversion_rate(metrics)
        if conversion_rate < 1.0:
            recommendations.append("Strengthen value proposition and offer clarity")
            
        if metrics.get('bounce_rate', 0) > 70:
            recommendations.append("Improve content relevance and readability")
            
        return recommendations
