import asyncio
from pathlib import Path
import sys
import os

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agents.email_manager import EmailManager

async def test_template():
    email_manager = EmailManager(os.path.join(project_root, 'credentials.json'))
    
    # Test template with minimal formatting
    test_template = {
        'name': 'test_template',
        'subject': 'Test Email',
        'html_content': """
        <p>Hi {{var:agent_name}},</p>
        <p>This is a test email.</p>
        <p>Best regards,<br>[Your Name]</p>
        """
    }
    
    try:
        result = await email_manager.create_template(
            name=test_template['name'],
            subject=test_template['subject'],
            html_content=test_template['html_content']
        )
        print(f"Successfully created template: {test_template['name']}")
        print(f"Template ID: {result.get('ID')}")
    except Exception as e:
        print(f"Error creating template: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_template())
