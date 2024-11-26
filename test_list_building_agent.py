import asyncio
import logging
from agents.list_building_agent import ListBuildingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('list_building_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ListBuildingTest')

async def test_list_building():
    """Test list building agent functionality"""
    try:
        # Initialize agent
        agent = ListBuildingAgent()
        
        # Test lead search
        logger.info("Testing lead search...")
        search_params = {
            'industry': 'Technology',
            'location': 'United States',
            'company_size': '50-200',
            'keywords': ['software', 'AI', 'machine learning']
        }
        leads = await agent.search_leads(search_params)
        logger.info(f"Found {len(leads)} leads")
        
        # Test lead validation
        logger.info("\nTesting lead validation...")
        for lead in leads[:5]:  # Test first 5 leads
            is_valid = await agent.validate_lead(lead)
            logger.info(f"Lead {lead['name']} validation: {'Valid' if is_valid else 'Invalid'}")
        
        # Test lead enrichment
        logger.info("\nTesting lead enrichment...")
        for lead in leads[:5]:
            enriched_lead = await agent.enrich_lead(lead)
            logger.info(f"Enriched lead data for {lead['name']}:")
            logger.info(f"- Company Size: {enriched_lead.get('company_size')}")
            logger.info(f"- Industry: {enriched_lead.get('industry')}")
            logger.info(f"- Technologies: {', '.join(enriched_lead.get('technologies', []))}")
        
        # Test list segmentation
        logger.info("\nTesting list segmentation...")
        segments = await agent.segment_leads(leads)
        for segment_name, segment_leads in segments.items():
            logger.info(f"Segment '{segment_name}': {len(segment_leads)} leads")
        
        # Test list export
        logger.info("\nTesting list export...")
        export_result = await agent.export_leads(leads, format='csv')
        logger.info(f"Exported leads to: {export_result['file_path']}")
        
        # Cleanup
        logger.info("\nCleaning up...")
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"Error in list building test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_list_building())
