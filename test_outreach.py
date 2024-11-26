from asana_tasks import DesignGagaTasks
from datetime import datetime, timedelta

def test_asana():
    # Initialize Asana task manager
    asana_manager = DesignGagaTasks()
    
    print("\n🚀 Testing Asana task creation...")
    
    # Set up sections
    print("\n📂 Setting up sections...")
    sections = asana_manager.setup_sections()
    
    # Create test tasks
    print("\n📝 Creating test tasks...")
    
    # Email follow-up task
    email_task = {
        'name': 'Email Follow-up: Test Real Estate Agent',
        'notes': '''
        Contact Details:
        - Name: Test Real Estate Agent
        - Type: real_estate_agent
        - Email: test@example.com
        - Area: Toronto
        
        Task Details:
        - Type: email
        - Template: introduction
        - Scheduled: Tomorrow
        ''',
        'due_on': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'assignee': None
    }
    
    asana_manager.create_task(sections['Customer Engagement'], email_task)
    print("✅ Created email follow-up task")
    
    # SMS follow-up task
    sms_task = {
        'name': 'SMS Follow-up: Test Real Estate Agent',
        'notes': '''
        Contact Details:
        - Name: Test Real Estate Agent
        - Type: real_estate_agent
        - Phone: +1234567890
        - Area: Toronto
        
        Task Details:
        - Type: sms
        - Template: follow_up
        - Scheduled: Day after tomorrow
        ''',
        'due_on': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
        'assignee': None
    }
    
    asana_manager.create_task(sections['Customer Engagement'], sms_task)
    print("✅ Created SMS follow-up task")
    
    print("\n✨ Test completed! Check your Asana project for the new tasks.")

if __name__ == "__main__":
    test_asana()
