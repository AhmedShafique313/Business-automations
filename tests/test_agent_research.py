import pytest
from agents.asana_manager import AsanaManager
from agents.email_manager import EmailManager

@pytest.mark.asyncio
async def test_agent_research():
    """Test agent research functionality"""
    # Test data
    agent_data = {
        'name': 'John Smith',
        'email': 'john@example.com',
        'brokerage': 'Luxury Realty Toronto',
        'location': 'Forest Hill',
        'description': '''
        Luxury real estate specialist with 15 years of experience.
        Focusing on high-end properties in Forest Hill and Rosedale.
        Multiple $2M+ sales in 2023. Investment property expert.
        Founded in 2008. Instagram: @johnsmith_luxury
        ''',
        'instagram_handle': 'johnsmith_luxury'
    }
    
    # Initialize managers
    asana_manager = AsanaManager()
    email_manager = EmailManager()
    
    # Test research methods
    sales_data = asana_manager._get_recent_sales(agent_data)
    price_point = asana_manager._estimate_price_point(agent_data)
    specializations = asana_manager._identify_specializations(agent_data)
    experience = asana_manager._calculate_experience(agent_data)
    social_data = asana_manager._analyze_social_presence(agent_data)
    
    # Print results
    print("\nAgent Research Results:")
    print(f"Sales Data: {sales_data}")
    print(f"Price Point: {price_point}")
    print(f"Specializations: {specializations}")
    print(f"Experience: {experience}")
    print(f"Social Data: {social_data}")
    
    # Test email functionality
    success = email_manager.send_introduction_email(agent_data)
    print(f"\nEmail sent: {success}")
    
    if success:
        # Test engagement tracking
        metrics = email_manager.track_email_engagement(agent_data)
        print("\nEmail Engagement Metrics:")
        print(f"Sent: {metrics['sent']}")
        print(f"Delivered: {metrics['delivered']}")
        print(f"Opens: {metrics['opens']}")
        print(f"Clicks: {metrics['clicks']}")
        print(f"Engagement Score: {metrics['engagement_score']}")
        
        # Test follow-up
        follow_up_success = email_manager.send_follow_up_email(agent_data, 1)
        print(f"\nFollow-up email sent: {follow_up_success}")

if __name__ == '__main__':
    pytest.main(['-v', 'test_agent_research.py'])
