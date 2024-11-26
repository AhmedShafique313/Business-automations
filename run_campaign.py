import asyncio
from agents.whatsapp_campaign import WhatsAppCampaign

async def main():
    campaign = WhatsAppCampaign()
    
    # Define your message sequence
    message_sequence = [
        {
            'type': 'template',
            'template_name': 'design_gaga_intro',
            'language': 'en_US',
            'parameters': [
                "{name}",      # Agent name
                "{location}"   # Location
            ],
            'delay_hours': 0
        },
        {
            'type': 'text',
            'text': "Hi {name}, I wanted to follow up and share that our staged properties in {location} "
                   "typically sell for 10-15% above market value. I'd love to show you our portfolio "
                   "and discuss how we can help your listings stand out.",
            'delay_hours': 24
        },
        {
            'type': 'text',
            'text': "Hi {name}, just checking if you had a chance to consider our staging services. "
                   "We currently have availability in {location} and are offering a special rate for "
                   "first-time collaborations. Would you be open to a quick chat?",
            'delay_hours': 48
        }
    ]
    
    # Your target list
    target_list = [
        {
            'name': input("Enter agent name: "),
            'phone': input("Enter WhatsApp number (with country code, e.g., +1234567890): "),
            'location': input("Enter location: "),
            'specialty': 'Real Estate Agent'
        }
    ]
    
    # Create campaign
    campaign_id = campaign.create_campaign(
        name="Home Staging Outreach",
        message_sequence=message_sequence,
        target_list=target_list
    )
    
    print(f"\nStarting campaign: {campaign_id}")
    print("\nCampaign will:")
    print("1. Send approved Design Gaga introduction template")
    print("2. Send portfolio and value proposition after 24 hours")
    print("3. Send special offer for first-time collaboration after 48 hours")
    print("\nProgress will be logged in whatsapp_campaign.log")
    
    # Run campaign
    await campaign.run_campaign(campaign_id)

if __name__ == "__main__":
    asyncio.run(main())
