import asyncio
from pathlib import Path
import sys
import os

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agents.email_manager import EmailManager

async def setup_templates():
    email_manager = EmailManager(os.path.join(project_root, 'credentials.json'))
    
    # Initial Introduction Template
    intro_template = {
        'name': 'agent_introduction',
        'subject': 'Elevate Your Real Estate Business with AI',
        'html_content': """
        <html>
        <body>
            <p>Hi {{var:agent_name}},</p>
            
            <p>{{var:personalization}}</p>
            
            <p>I'm reaching out because {{var:value_proposition}}. Our platform helps agents like you:</p>
            
            <ul>
                <li>Save 20+ hours per week on lead generation and follow-ups</li>
                <li>Increase response rates by 3x with AI-powered personalization</li>
                <li>Generate high-quality leads through automated market analysis</li>
                <li>Track and nurture prospects with intelligent engagement scoring</li>
            </ul>
            
            <p>{{var:call_to_action}}</p>
            
            <p>Looking forward to connecting!</p>
            
            <p>Best regards,<br>
            [Your Name]</p>
        </body>
        </html>
        """
    }
    
    # Follow-up Template 1
    followup_1 = {
        'name': 'agent_followup_1',
        'subject': 'Quick Follow-up: AI-Powered Real Estate Growth',
        'html_content': """
        <html>
        <body>
            <p>Hi {{var:agent_name}},</p>
            
            <p>{{var:personalization}}</p>
            
            <p>I wanted to highlight a few specific ways our AI platform could help grow your business:</p>
            
            <ul>
                <li>Automated market analysis to identify high-potential leads</li>
                <li>Smart CRM that prioritizes your most promising prospects</li>
                <li>Personalized communication sequences that maintain engagement</li>
            </ul>
            
            <p>{{var:call_to_action}}</p>
            
            <p>Best regards,<br>
            [Your Name]</p>
        </body>
        </html>
        """
    }
    
    # Follow-up Template 2
    followup_2 = {
        'name': 'agent_followup_2',
        'subject': 'See How Other Agents Are Growing with AI',
        'html_content': """
        <html>
        <body>
            <p>Hi {{var:agent_name}},</p>
            
            <p>{{var:personalization}}</p>
            
            <p>I thought you might be interested in seeing some real results from agents using our platform:</p>
            
            <ul>
                <li>Sarah M. increased her monthly leads by 240% in 3 months</li>
                <li>John D. saved 25 hours per week on prospecting and follow-ups</li>
                <li>The Thompson Team doubled their luxury property closings</li>
            </ul>
            
            <p>{{var:value_proposition}}</p>
            
            <p>{{var:call_to_action}}</p>
            
            <p>Best regards,<br>
            [Your Name]</p>
        </body>
        </html>
        """
    }
    
    # Follow-up Template 3
    followup_3 = {
        'name': 'agent_followup_3',
        'subject': 'Last Call: Special Offer for AI Platform',
        'html_content': """
        <html>
        <body>
            <p>Hi {{var:agent_name}},</p>
            
            <p>{{var:personalization}}</p>
            
            <p>I wanted to extend a special offer: Sign up this week and receive:</p>
            
            <ul>
                <li>3 months of premium features at no extra cost</li>
                <li>Personalized onboarding and strategy session</li>
                <li>Priority access to new AI features</li>
            </ul>
            
            <p>{{var:value_proposition}}</p>
            
            <p>{{var:call_to_action}}</p>
            
            <p>Best regards,<br>
            [Your Name]</p>
        </body>
        </html>
        """
    }
    
    templates = [intro_template, followup_1, followup_2, followup_3]
    
    for template in templates:
        try:
            result = await email_manager.create_template(
                name=template['name'],
                subject=template['subject'],
                html_content=template['html_content']
            )
            print(f"Successfully created template: {template['name']}")
            print(f"Template ID: {result.get('ID')}")
        except Exception as e:
            print(f"Error creating template {template['name']}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(setup_templates())
