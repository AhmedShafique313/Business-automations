import asyncio
import logging
from agents.content.processors.content_processor import ContentProcessor
from agents.content.review.content_reviewer import ContentReviewer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('content_agents.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ContentAgents')

async def test_content_generation():
    """Test content generation and review workflow"""
    try:
        # Initialize agents
        templates_dir = "/mnt/VANDAN_DISK/code_stuff/projects/experiments/agents/content/templates"
        work_dir = "/mnt/VANDAN_DISK/code_stuff/projects/experiments/agents/content/review"
        processor = ContentProcessor(templates_dir)
        reviewer = ContentReviewer(work_dir)
        
        # Test different content types
        content_types = [
            'blog_post',
            'social_post',
            'email_campaign',
            'video_script',
            'product_description',
            'whitepaper'
        ]
        
        for content_type in content_types:
            logger.info(f"\n=== Testing {content_type} generation and review ===")
            
            # Generate content
            base_params = {
                'topic': 'AI and Machine Learning in Marketing',
                'target_audience': 'Marketing professionals and business owners',
                'tone': 'professional',
                'keywords': ['AI', 'marketing automation', 'machine learning', 'ROI']
            }
            
            # Content type specific parameters
            type_params = {
                'blog_post': {
                    'title': 'The Future of Marketing: AI and Machine Learning',
                    'summary': 'Discover how AI and machine learning are revolutionizing the marketing landscape',
                    'sections': [
                        {
                            'heading': 'Introduction',
                            'content': 'The marketing landscape is rapidly evolving...'
                        },
                        {
                            'heading': 'The Role of AI in Modern Marketing',
                            'content': 'Artificial Intelligence is transforming how we approach marketing...'
                        },
                        {
                            'heading': 'Machine Learning Applications',
                            'content': 'Machine learning algorithms are enabling personalized marketing at scale...'
                        }
                    ],
                    'tags': ['AI', 'Marketing', 'Technology'],
                    'seo': {
                        'keywords': ['AI marketing', 'machine learning marketing', 'marketing automation'],
                        'meta_description': 'Learn how AI and machine learning are transforming the marketing landscape'
                    }
                },
                'social_post': {
                    'platform': 'linkedin',
                    'content': 'Excited to share our latest insights on AI in marketing! 🚀\n\nLearn how machine learning is revolutionizing customer engagement and ROI. Check out our latest blog post!',
                    'hashtags': ['#AIMarketing', '#MarTech', '#DigitalTransformation']
                },
                'email_campaign': {
                    'subject': 'Transform Your Marketing with AI - Free Guide Inside',
                    'preview_text': 'Discover how AI can boost your marketing ROI',
                    'sections': [
                        {
                            'type': 'header',
                            'content': 'The Future of Marketing is Here'
                        },
                        {
                            'type': 'text',
                            'content': 'Dear {first_name},\n\nAre you ready to transform your marketing?'
                        },
                        {
                            'type': 'button',
                            'content': 'Download Free Guide'
                        }
                    ],
                    'personalization': {
                        'merge_fields': ['first_name', 'company_name'],
                        'dynamic_content': {
                            'industry_segment': ['tech', 'retail', 'finance']
                        }
                    }
                },
                'video_script': {
                    'title': 'AI Marketing Revolution: A Complete Guide',
                    'target_duration': 300,
                    'scenes': [
                        {
                            'scene_number': 1,
                            'duration': 30,
                            'setting': 'Modern office environment',
                            'action': 'Marketing team analyzing data dashboards',
                            'dialogue': 'Marketing has evolved...',
                            'visual_notes': 'Show AI visualization overlay'
                        },
                        {
                            'scene_number': 2,
                            'duration': 45,
                            'setting': 'Split screen demonstration',
                            'action': 'Comparison of traditional vs AI-powered marketing',
                            'dialogue': 'Let\'s see the difference...',
                            'visual_notes': 'Use animated graphics'
                        }
                    ],
                    'target_audience': {
                        'age_range': [25, 45],
                        'interests': ['marketing', 'technology', 'business'],
                        'demographics': {
                            'job_titles': ['Marketing Manager', 'Digital Marketer', 'CMO']
                        }
                    }
                },
                'product_description': {
                    'product_name': 'MarketingAI Pro',
                    'short_description': 'AI-powered marketing automation platform',
                    'long_description': 'MarketingAI Pro is a comprehensive marketing automation platform that leverages artificial intelligence...',
                    'features': [
                        {
                            'title': 'AI Content Generation',
                            'description': 'Generate marketing content automatically',
                            'benefit': 'Save time and resources while maintaining quality'
                        },
                        {
                            'title': 'Smart Analytics',
                            'description': 'AI-powered marketing analytics',
                            'benefit': 'Make data-driven decisions with confidence'
                        }
                    ],
                    'specifications': {
                        'dimensions': {
                            'type': 'cloud-based',
                            'deployment': 'SaaS'
                        },
                        'weight': 'N/A',
                        'materials': ['Software'],
                        'technical_specs': {
                            'supported_platforms': ['Web', 'Mobile'],
                            'integration_apis': ['REST', 'GraphQL']
                        }
                    }
                },
                'whitepaper': {
                    'title': 'The Impact of AI on Modern Marketing',
                    'executive_summary': 'This whitepaper explores how AI is transforming marketing...',
                    'sections': [
                        {
                            'title': 'Introduction',
                            'content': 'The marketing landscape is undergoing a dramatic transformation...'
                        },
                        {
                            'title': 'Research Methodology',
                            'content': 'Our research combines industry surveys and expert interviews...'
                        },
                        {
                            'title': 'Key Findings',
                            'content': 'AI adoption in marketing has shown significant ROI improvements...'
                        }
                    ],
                    'references': [
                        {
                            'title': 'AI in Marketing Survey 2023',
                            'authors': ['Smith, J.', 'Johnson, M.'],
                            'publication': 'Marketing Technology Review'
                        }
                    ],
                    'metadata': {
                        'published_date': '2023-11-25',
                        'industry': 'Marketing Technology',
                        'target_audience': ['Marketing Executives', 'Digital Marketers']
                    }
                }
            }
            
            # Combine base params with type-specific params
            content_params = {**base_params, **type_params.get(content_type, {})}
            
            logger.info(f"Generating {content_type}...")
            content = processor.generate_content(content_type, content_params)
            
            # Review content
            logger.info(f"Reviewing {content_type}...")
            review_result = await reviewer.review_content(content, content_type)
            
            # Log results
            logger.info(f"\nContent Generation Result:")
            logger.info(f"Content Type: {content_type}")
            logger.info(f"Content Length: {len(str(content['content']))} characters")
            logger.info(f"Metadata: {content.get('metadata', {})}")
            
            logger.info(f"\nReview Results:")
            logger.info(f"Quality Score: {review_result['quality']['score']:.2f}")
            logger.info(f"Compliance Score: {review_result['compliance']['score']:.2f}")
            logger.info(f"Overall Status: {'Approved' if review_result['approved'] else 'Needs Revision'}")
            
            if not review_result['approved']:
                logger.info("Failed Checks:")
                for check_type, results in review_result.items():
                    if isinstance(results, dict) and 'scores' in results:
                        for aspect, score_data in results['scores'].items():
                            if not score_data['passed']:
                                logger.info(f"- {check_type.capitalize()} > {aspect}: {score_data['score']:.2f} (Threshold: {score_data['threshold']})")
            
            logger.info("\n" + "="*50 + "\n")
            
            # Add a small delay between tests
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in content generation test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_content_generation())
