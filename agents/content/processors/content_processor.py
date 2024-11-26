"""
Content Processor
Handles content generation, validation, and processing.
"""

import json
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
import jsonschema
from datetime import datetime

class ContentProcessor:
    """Processes and validates content based on templates."""
    
    def __init__(self, templates_dir: Union[str, Path]):
        """Initialize the content processor."""
        self.templates_dir = Path(templates_dir)
        self.logger = logging.getLogger('ContentProcessor')
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict:
        """Load content templates."""
        try:
            template_file = self.templates_dir / 'content_templates.json'
            if not template_file.exists():
                raise FileNotFoundError(f"Template file not found: {template_file}")
            
            with open(template_file) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load templates: {str(e)}")
            raise
    
    def validate_content(self, content: Dict, content_type: str) -> bool:
        """Validate content against its template."""
        try:
            if content_type not in self.templates:
                raise ValueError(f"Unknown content type: {content_type}")
            
            template = self.templates[content_type]
            jsonschema.validate(
                instance=content,
                schema={"type": "object", "properties": template["structure"]}
            )
            return True
            
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"Content validation failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False
    
    def generate_content(self, content_type: str, parameters: Dict) -> Dict:
        """Generate content based on template and parameters."""
        try:
            if content_type not in self.templates:
                raise ValueError(f"Unknown content type: {content_type}")
            
            template = self.templates[content_type]
            
            # Generate content based on type
            content_generators = {
                'blog_post': self._generate_blog_post,
                'social_post': self._generate_social_post,
                'email_campaign': self._generate_email_campaign,
                'video_script': self._generate_video_script,
                'product_description': self._generate_product_description,
                'whitepaper': self._generate_whitepaper
            }
            
            generator = content_generators.get(content_type)
            if not generator:
                raise ValueError(f"Content generation not implemented for type: {content_type}")
            
            content = generator(parameters)
            
            # Validate generated content
            if not self.validate_content(content, content_type):
                raise ValueError("Generated content failed validation")
            
            return content
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {str(e)}")
            raise
    
    def _generate_blog_post(self, parameters: Dict) -> Dict:
        """Generate a blog post."""
        try:
            title = parameters.get('title', 'Untitled Blog Post')
            summary = parameters.get('summary', 'A blog post about...')
            keywords = parameters.get('keywords', [])
            
            # Generate sections
            sections = [
                {
                    "heading": "Introduction",
                    "content": f"Introduction to {title}..."
                },
                {
                    "heading": "Main Content",
                    "content": "Main content of the blog post..."
                },
                {
                    "heading": "Conclusion",
                    "content": "In conclusion..."
                }
            ]
            
            # Generate SEO metadata
            seo = {
                "keywords": keywords,
                "meta_description": summary[:160]  # Standard meta description length
            }
            
            return {
                "title": title,
                "summary": summary,
                "sections": sections,
                "tags": keywords[:5],  # Use top 5 keywords as tags
                "seo": seo
            }
            
        except Exception as e:
            self.logger.error(f"Blog post generation failed: {str(e)}")
            raise
    
    def _generate_social_post(self, parameters: Dict) -> Dict:
        """Generate a social media post."""
        try:
            platform = parameters.get('platform', 'twitter')
            message = parameters.get('message', '')
            hashtags = parameters.get('hashtags', [])
            media = parameters.get('media', [])
            
            # Get platform-specific constraints
            max_length = self.templates['social_post']['structure']['content']['max_length'][platform]
            
            # Truncate content if needed
            content = message[:max_length]
            
            return {
                "platform": platform,
                "content": content,
                "media": media,
                "hashtags": hashtags
            }
            
        except Exception as e:
            self.logger.error(f"Social post generation failed: {str(e)}")
            raise
    
    def _generate_email_campaign(self, parameters: Dict) -> Dict:
        """Generate an email campaign."""
        try:
            subject = parameters.get('subject', 'New Campaign')
            preview = parameters.get('preview_text', '')
            sections_data = parameters.get('sections', [])
            personalization = parameters.get('personalization', {})
            
            # Generate sections
            sections = []
            for section in sections_data:
                section_type = section.get('type', 'text')
                content = section.get('content', '')
                sections.append({
                    "type": section_type,
                    "content": content
                })
            
            # Ensure required sections exist
            if not any(s['type'] == 'header' for s in sections):
                sections.insert(0, {
                    "type": "header",
                    "content": subject
                })
            
            if not any(s['type'] == 'footer' for s in sections):
                sections.append({
                    "type": "footer",
                    "content": "Unsubscribe | View in browser"
                })
            
            return {
                "subject": subject,
                "preview_text": preview,
                "sections": sections,
                "personalization": {
                    "merge_fields": personalization.get('merge_fields', []),
                    "dynamic_content": personalization.get('dynamic_content', {})
                }
            }
            
        except Exception as e:
            self.logger.error(f"Email campaign generation failed: {str(e)}")
            raise
    
    def _generate_video_script(self, parameters: Dict) -> Dict:
        """Generate a video script."""
        try:
            title = parameters.get('title', 'Untitled Video')
            target_duration = parameters.get('target_duration', 300)  # 5 minutes default
            target_audience = parameters.get('target_audience', {})
            
            # Generate scenes
            scenes = [
                {
                    "scene_number": 1,
                    "duration": 30,
                    "setting": "Opening Scene",
                    "action": "Fade in to main subject",
                    "dialogue": f"Welcome to {title}",
                    "visual_notes": "Use engaging opening visuals"
                },
                {
                    "scene_number": 2,
                    "duration": target_duration - 60,  # Main content
                    "setting": "Main Content",
                    "action": "Series of key points with visual aids",
                    "dialogue": "Main content script...",
                    "visual_notes": "Include graphics and demonstrations"
                },
                {
                    "scene_number": 3,
                    "duration": 30,
                    "setting": "Closing Scene",
                    "action": "Call to action and farewell",
                    "dialogue": "Thanks for watching! Don't forget to like and subscribe",
                    "visual_notes": "Display social media handles and website"
                }
            ]
            
            return {
                "title": title,
                "target_duration": target_duration,
                "scenes": scenes,
                "target_audience": {
                    "age_range": target_audience.get('age_range', ["18-35"]),
                    "interests": target_audience.get('interests', ["general"]),
                    "demographics": target_audience.get('demographics', {})
                }
            }
            
        except Exception as e:
            self.logger.error(f"Video script generation failed: {str(e)}")
            raise
    
    def _generate_product_description(self, parameters: Dict) -> Dict:
        """Generate a product description."""
        try:
            product_name = parameters.get('product_name', 'Product Name')
            features = parameters.get('features', [])
            specs = parameters.get('specifications', {})
            
            # Generate description sections
            short_desc = f"Introducing {product_name} - a revolutionary product designed to enhance your experience."
            long_desc = f"""
            {product_name} is a cutting-edge solution that combines innovation with practicality.
            This product offers unparalleled performance and reliability, making it the perfect choice
            for those who demand excellence.
            """
            
            # Generate features if none provided
            if not features:
                features = [
                    {
                        "title": "Quality",
                        "description": "Premium build quality and materials",
                        "benefit": "Long-lasting durability and reliability"
                    },
                    {
                        "title": "Innovation",
                        "description": "Cutting-edge technology",
                        "benefit": "Enhanced user experience"
                    },
                    {
                        "title": "Value",
                        "description": "Competitive pricing",
                        "benefit": "Excellent return on investment"
                    }
                ]
            
            return {
                "product_name": product_name,
                "short_description": short_desc.strip(),
                "long_description": long_desc.strip(),
                "features": features,
                "specifications": {
                    "dimensions": specs.get('dimensions', {"length": "0", "width": "0", "height": "0"}),
                    "weight": specs.get('weight', "0"),
                    "materials": specs.get('materials', ["Standard materials"]),
                    "technical_specs": specs.get('technical_specs', {})
                },
                "seo": {
                    "keywords": [product_name.lower(), "quality", "innovation"],
                    "meta_description": short_desc[:160],
                    "search_terms": [product_name.lower(), "buy " + product_name.lower()]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Product description generation failed: {str(e)}")
            raise
    
    def _generate_whitepaper(self, parameters: Dict) -> Dict:
        """Generate a whitepaper."""
        try:
            title = parameters.get('title', 'Industry Whitepaper')
            topic = parameters.get('topic', 'Industry Analysis')
            research_data = parameters.get('research_data', {})
            
            # Generate executive summary
            executive_summary = f"""
            This comprehensive whitepaper explores {topic}, providing detailed analysis and insights
            into current trends, challenges, and opportunities. Through extensive research and
            expert analysis, we present actionable recommendations for stakeholders.
            """
            
            # Generate sections
            sections = [
                {
                    "heading": "Introduction",
                    "content": f"Overview of {topic} and its significance...",
                    "subsections": [],
                    "citations": []
                },
                {
                    "heading": "Market Analysis",
                    "content": "Detailed analysis of current market conditions...",
                    "subsections": [
                        "Market Size and Growth",
                        "Key Players",
                        "Trends"
                    ],
                    "citations": ["Industry Report 2023"]
                },
                {
                    "heading": "Challenges and Opportunities",
                    "content": "Analysis of key challenges and opportunities...",
                    "subsections": [
                        "Current Challenges",
                        "Emerging Opportunities",
                        "Risk Analysis"
                    ],
                    "citations": []
                },
                {
                    "heading": "Recommendations",
                    "content": "Strategic recommendations based on findings...",
                    "subsections": [],
                    "citations": []
                }
            ]
            
            # Generate research data if not provided
            if not research_data:
                research_data = {
                    "methodology": "Mixed-method research approach combining quantitative and qualitative analysis",
                    "findings": [
                        "Key finding 1",
                        "Key finding 2",
                        "Key finding 3"
                    ],
                    "data_sources": [
                        "Industry surveys",
                        "Expert interviews",
                        "Market analysis"
                    ]
                }
            
            return {
                "title": title,
                "executive_summary": executive_summary.strip(),
                "sections": sections,
                "research_data": research_data,
                "graphics": [
                    {
                        "title": "Market Growth Trend",
                        "type": "line_chart",
                        "data": {"years": [2020, 2021, 2022], "values": [100, 120, 150]},
                        "caption": "Market growth over the past three years"
                    }
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Whitepaper generation failed: {str(e)}")
            raise
    
    def process_content(self, content: Dict, content_type: str) -> Dict:
        """Process content for final delivery."""
        try:
            # Validate content
            if not self.validate_content(content, content_type):
                raise ValueError("Content validation failed")
            
            # Add metadata
            processed_content = {
                **content,
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "content_type": content_type,
                    "version": "1.0"
                }
            }
            
            return processed_content
            
        except Exception as e:
            self.logger.error(f"Content processing failed: {str(e)}")
            raise
