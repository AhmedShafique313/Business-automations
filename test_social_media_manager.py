import asyncio
import logging
from agents.social_media_manager import SocialMediaManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('social_media_manager.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('SocialMediaTest')

async def test_social_media_manager():
    """Test social media manager functionality"""
    try:
        # Initialize agent
        agent = SocialMediaManager()
        
        # Test content calendar creation
        logger.info("Testing content calendar creation...")
        calendar_params = {
            'start_date': '2023-11-01',
            'end_date': '2023-11-30',
            'platforms': ['linkedin', 'twitter', 'facebook'],
            'post_frequency': {
                'linkedin': 3,  # posts per week
                'twitter': 5,
                'facebook': 3
            },
            'content_mix': {
                'promotional': 0.2,
                'educational': 0.4,
                'engagement': 0.3,
                'curated': 0.1
            }
        }
        calendar = await agent.create_content_calendar(calendar_params)
        logger.info(f"Created content calendar with {len(calendar['posts'])} posts")
        
        # Test content generation
        logger.info("\nTesting content generation...")
        content_params = {
            'topic': 'AI in Marketing',
            'tone': 'professional',
            'target_audience': 'Marketing professionals',
            'call_to_action': 'Learn more about our AI solutions'
        }
        
        for platform in ['linkedin', 'twitter', 'facebook']:
            content = await agent.generate_social_content(platform, content_params)
            logger.info(f"\nGenerated content for {platform}:")
            logger.info(f"- Text: {content['text'][:100]}...")
            logger.info(f"- Hashtags: {', '.join(content['hashtags'])}")
            if content.get('media'):
                logger.info(f"- Media: {content['media']}")
        
        # Test post scheduling
        logger.info("\nTesting post scheduling...")
        for post in calendar['posts'][:3]:  # Test with first 3 posts
            schedule_result = await agent.schedule_post(post)
            logger.info(f"Scheduled post for {post['platform']} at {schedule_result['scheduled_time']}")
        
        # Test hashtag analysis
        logger.info("\nTesting hashtag analysis...")
        hashtags = await agent.analyze_hashtags('AI Marketing')
        logger.info("Top hashtags:")
        for hashtag in hashtags[:5]:
            logger.info(f"- {hashtag['tag']}: {hashtag['score']} engagement score")
        
        # Test engagement monitoring
        logger.info("\nTesting engagement monitoring...")
        engagement_metrics = await agent.monitor_engagement({
            'start_date': '2023-11-01',
            'end_date': '2023-11-07',
            'platforms': ['linkedin', 'twitter', 'facebook']
        })
        
        for platform, metrics in engagement_metrics.items():
            logger.info(f"\n{platform.capitalize()} Engagement:")
            logger.info(f"- Impressions: {metrics['impressions']}")
            logger.info(f"- Engagements: {metrics['engagements']}")
            logger.info(f"- Engagement Rate: {metrics['engagement_rate']}%")
        
        # Test performance analysis
        logger.info("\nTesting performance analysis...")
        performance = await agent.analyze_performance({
            'timeframe': 'last_7_days',
            'metrics': ['engagement', 'reach', 'clicks'],
            'platforms': ['linkedin', 'twitter', 'facebook']
        })
        
        logger.info("Performance Analysis:")
        for platform, metrics in performance.items():
            logger.info(f"\n{platform.capitalize()}:")
            logger.info(f"- Best performing post: {metrics['top_post']['text'][:50]}...")
            logger.info(f"- Engagement rate: {metrics['engagement_rate']}%")
            logger.info(f"- Click-through rate: {metrics['click_through_rate']}%")
        
        # Test content optimization
        logger.info("\nTesting content optimization...")
        optimization_suggestions = await agent.optimize_content({
            'platform': 'linkedin',
            'content': 'Check out our latest AI marketing solutions!',
            'performance_data': performance['linkedin']
        })
        
        logger.info("Content Optimization Suggestions:")
        for suggestion in optimization_suggestions:
            logger.info(f"- {suggestion['type']}: {suggestion['suggestion']}")
        
        # Cleanup
        logger.info("\nCleaning up...")
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"Error in social media manager test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_social_media_manager())
