from typing import Dict, Any, List
import asyncio
import logging

# Configure logging
logger = logging.getLogger(__name__)

class BusinessOptimizer:
    async def generate_recommendations(
        self,
        website_analysis: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates business optimization recommendations based on website analysis.
        """
        logger.info("Starting recommendation generation")
        recommendations = {
            "website_improvements": await self._analyze_website_improvements(website_analysis),
            "marketing_suggestions": await self._generate_marketing_suggestions(website_analysis),
            "content_strategy": await self._develop_content_strategy(website_analysis),
            "technical_improvements": await self._suggest_technical_improvements(website_analysis),
            "priority_actions": []
        }
        
        # Determine priority actions
        recommendations["priority_actions"] = await self._determine_priority_actions(recommendations)
        logger.info(f"Generated {len(recommendations['priority_actions'])} priority actions")
        
        return recommendations

    async def _analyze_website_improvements(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Analyzing website improvements needed")
        improvements = []
        
        # Check meta description
        if not analysis.get("meta_description"):
            logger.info("Missing meta description - adding recommendation")
            improvements.append({
                "type": "meta_description",
                "priority": "high",
                "description": "Add a meta description to improve SEO",
                "impact": "Improves search engine visibility and click-through rates"
            })
            
        # Check images
        images = analysis.get("images", {})
        if images.get("total", 0) > 0 and images.get("with_alt", 0) < images.get("total", 0):
            logger.info(f"Found {images.get('total', 0) - images.get('with_alt', 0)} images missing alt text")
            improvements.append({
                "type": "image_optimization",
                "priority": "medium",
                "description": "Add alt text to all images",
                "impact": "Improves accessibility and SEO"
            })
            
        # Check social media presence
        if not analysis.get("social_media"):
            logger.info("No social media links found - adding recommendation")
            improvements.append({
                "type": "social_media",
                "priority": "medium",
                "description": "Add social media links to improve online presence",
                "impact": "Increases brand visibility and customer engagement"
            })
            
        logger.info(f"Generated {len(improvements)} website improvement recommendations")
        return improvements

    async def _generate_marketing_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Generating marketing suggestions")
        suggestions = []
        
        # Social media marketing
        social_platforms = analysis.get("social_media", {})
        missing_platforms = {'facebook', 'instagram', 'linkedin'} - set(social_platforms.keys())
        if missing_platforms:
            logger.info(f"Missing social platforms: {missing_platforms}")
            suggestions.append({
                "type": "social_media_marketing",
                "priority": "high",
                "description": f"Establish presence on {', '.join(missing_platforms)}",
                "impact": "Expands reach and engagement with potential customers"
            })
            
        # Content marketing
        headers = analysis.get("headers", {})
        if sum(headers.values()) < 5:
            logger.info("Limited content structure detected")
            suggestions.append({
                "type": "content_structure",
                "priority": "medium",
                "description": "Improve content structure with proper headings",
                "impact": "Better user experience and SEO performance"
            })
            
        logger.info(f"Generated {len(suggestions)} marketing suggestions")
        return suggestions

    async def _develop_content_strategy(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Developing content strategy recommendations")
        strategy = []
        
        # Blog content
        strategy.append({
            "type": "blog_content",
            "priority": "medium",
            "description": "Start a blog with industry insights and company updates",
            "frequency": "Weekly",
            "topics": [
                "Industry trends",
                "Company news",
                "Product updates",
                "Customer success stories"
            ]
        })
        
        # Social media content
        strategy.append({
            "type": "social_media_content",
            "priority": "high",
            "description": "Regular social media updates",
            "frequency": "Daily",
            "content_types": [
                "Industry news",
                "Behind-the-scenes content",
                "Product showcases",
                "Customer testimonials"
            ]
        })
        
        logger.info(f"Generated {len(strategy)} content strategy recommendations")
        return strategy

    async def _suggest_technical_improvements(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Analyzing technical improvements")
        improvements = []
        
        # Performance improvements
        perf_metrics = analysis.get("performance_metrics", {})
        if perf_metrics.get("load_time", 0) > 2.0:
            logger.info(f"Slow load time detected: {perf_metrics.get('load_time', 0):.2f}s")
            improvements.append({
                "type": "performance",
                "priority": "high",
                "description": "Improve website load time",
                "current_value": f"{perf_metrics.get('load_time', 0):.2f}s",
                "target": "Under 2 seconds",
                "suggestions": [
                    "Optimize images",
                    "Enable caching",
                    "Minify CSS/JS",
                    "Use a CDN"
                ]
            })
            
        logger.info(f"Generated {len(improvements)} technical improvement recommendations")
        return improvements

    async def _determine_priority_actions(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Determining priority actions")
        priority_actions = []
        
        # Collect all high-priority items
        for category, items in recommendations.items():
            if isinstance(items, list):
                for item in items:
                    if item.get("priority") == "high":
                        priority_actions.append({
                            "category": category,
                            "action": item["description"],
                            "impact": item.get("impact", "High impact on business growth")
                        })
        
        # Sort by impact (if available)
        priority_actions.sort(key=lambda x: len(x.get("impact", "")), reverse=True)
        
        logger.info(f"Selected top {min(5, len(priority_actions))} priority actions")
        return priority_actions[:5]  # Return top 5 priority actions
