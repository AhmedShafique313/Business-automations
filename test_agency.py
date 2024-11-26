"""
Test script for the AI Marketing Agency Platform
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.agent_orchestrator import AgentOrchestrator

async def test_viral_campaign():
    """Test viral campaign creation and analysis."""
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create campaign for tech industry
    campaign = await orchestrator.create_viral_campaign(
        industry="technology",
        platforms=["tiktok", "instagram"],
        content_types=["video", "image"],
        context={
            "target_audience": "tech enthusiasts",
            "brand_voice": "innovative and engaging",
            "key_themes": ["AI", "future tech", "innovation"]
        }
    )
    
    print("\n=== Campaign Created ===")
    print(json.dumps(campaign, indent=2))
    
    # Get campaign insights
    insights = await orchestrator.get_campaign_insights(campaign['campaign_id'])
    
    print("\n=== Campaign Insights ===")
    print(json.dumps(insights, indent=2))
    
    # Update campaign
    updated_campaign = await orchestrator.update_campaign(
        campaign['campaign_id'],
        {
            "content_types": ["video"],
            "platforms": ["tiktok", "youtube_shorts"]
        }
    )
    
    print("\n=== Updated Campaign ===")
    print(json.dumps(updated_campaign, indent=2))

if __name__ == "__main__":
    asyncio.run(test_viral_campaign())
