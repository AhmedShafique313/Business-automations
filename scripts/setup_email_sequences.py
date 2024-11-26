"""Set up initial email sequences for the campaign."""
import asyncio
import os
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from agents.email_manager import EmailManager
from agents.email_campaign_analytics import EmailAnalytics
from agents.email_sequence_manager import (
    EmailSequenceManager,
    SequenceStep,
    SequenceStatus
)

async def setup_sequences():
    """Set up initial email sequences."""
    # Initialize managers
    email_manager = EmailManager(os.path.join(project_root, 'credentials.json'))
    analytics = EmailAnalytics()
    sequence_manager = EmailSequenceManager(email_manager, analytics)
    
    # Define welcome sequence
    welcome_sequence = [
        SequenceStep(
            step_id="welcome_1",
            template_id=None,
            subject="Welcome to Design Gaga - Let's Transform Your Real Estate Business",
            content="""
            <html>
            <body>
                <p>Hi {{name}},</p>
                
                <p>Welcome to Design Gaga! We're excited to help you transform your real estate business with our AI-powered design tools.</p>
                
                <p>Here's what you can expect in the coming days:</p>
                <ul>
                    <li>Personalized design recommendations</li>
                    <li>Tips for optimizing your listings</li>
                    <li>Success stories from other agents</li>
                </ul>
                
                <p>To get started, check out our quick tutorial video: [Link]</p>
                
                <p>Best regards,<br>
                The Design Gaga Team</p>
            </body>
            </html>
            """,
            delay_days=0
        ),
        SequenceStep(
            step_id="welcome_2",
            template_id=None,
            subject="Your First Design Project with Design Gaga",
            content="""
            <html>
            <body>
                <p>Hi {{name}},</p>
                
                <p>Ready to create your first stunning design? Here's a simple guide to get you started:</p>
                
                <ol>
                    <li>Log in to your dashboard</li>
                    <li>Click "New Project"</li>
                    <li>Choose from our premium templates</li>
                    <li>Customize with your branding</li>
                </ol>
                
                <p>Need help? Reply to this email or schedule a demo: [Link]</p>
                
                <p>Best regards,<br>
                The Design Gaga Team</p>
            </body>
            </html>
            """,
            delay_days=2
        ),
        SequenceStep(
            step_id="welcome_3",
            template_id=None,
            subject="Exclusive Tips for Luxury Real Estate Marketing",
            content="""
            <html>
            <body>
                <p>Hi {{name}},</p>
                
                <p>We've put together some exclusive tips for marketing luxury properties:</p>
                
                <ul>
                    <li>Professional photography best practices</li>
                    <li>Virtual staging techniques</li>
                    <li>Social media marketing strategies</li>
                    <li>Email campaign templates</li>
                </ul>
                
                <p>Download our free guide here: [Link]</p>
                
                <p>Best regards,<br>
                The Design Gaga Team</p>
            </body>
            </html>
            """,
            delay_days=4,
            ab_test=True,
            variants={
                "variant_a": "Download our free guide here: [Link]",
                "variant_b": "Get your complimentary luxury marketing guide: [Link]"
            }
        )
    ]
    
    # Define re-engagement sequence
    reengagement_sequence = [
        SequenceStep(
            step_id="reengagement_1",
            template_id=None,
            subject="We Miss You at Design Gaga",
            content="""
            <html>
            <body>
                <p>Hi {{name}},</p>
                
                <p>We noticed you haven't logged in recently. Here's what's new:</p>
                
                <ul>
                    <li>New luxury property templates</li>
                    <li>Enhanced AI-powered design tools</li>
                    <li>Improved social media integration</li>
                </ul>
                
                <p>Log in now to explore: [Link]</p>
                
                <p>Best regards,<br>
                The Design Gaga Team</p>
            </body>
            </html>
            """,
            delay_days=0
        ),
        SequenceStep(
            step_id="reengagement_2",
            template_id=None,
            subject="Special Offer Just for You",
            content="""
            <html>
            <body>
                <p>Hi {{name}},</p>
                
                <p>We'd love to have you back! Here's a special offer:</p>
                
                <p>Get 20% off your next month when you reactivate your account.</p>
                
                <p>Use code: WELCOME20</p>
                
                <p>Best regards,<br>
                The Design Gaga Team</p>
            </body>
            </html>
            """,
            delay_days=3,
            ab_test=True,
            variants={
                "variant_a": "Get 20% off your next month",
                "variant_b": "Save 20% instantly"
            }
        )
    ]
    
    # Create sequences
    sequence_manager.create_sequence("welcome", welcome_sequence)
    sequence_manager.create_sequence("reengagement", reengagement_sequence)
    
    return sequence_manager

if __name__ == "__main__":
    asyncio.run(setup_sequences())
