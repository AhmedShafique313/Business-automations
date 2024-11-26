import pandas as pd
from agents.asana_manager import AsanaManager
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ImportAgents')

def clean_description(desc):
    """Clean and format the description."""
    if pd.isna(desc):
        return ""
    return desc.replace('\n', ' ').strip()

def format_agent_data(row):
    """Format agent data for Asana task."""
    description = f"""
# Agent Details
- **Name**: {row['name']}
- **Brokerage**: {row.get('brokerage', 'N/A')}
- **Location**: {row.get('location', 'N/A')}
- **Source**: {row.get('source', 'N/A')}
- **Found On**: {row.get('date_found', 'N/A')}

# Description
{clean_description(row.get('description', ''))}

# Profile URL
{row.get('profile_url', 'N/A')}
"""
    return {
        'name': f"Agent: {row['name']}",
        'description': description.strip(),
        'status': 'new'
    }

def main():
    """Import agents to Asana."""
    try:
        # Initialize Asana manager
        asana = AsanaManager()
        
        # Read agents from CSV
        logger.info("Reading agents from CSV...")
        agents_df = pd.read_csv('luxury_agents_database.csv')
        
        # Filter out invalid entries
        agents_df = agents_df[agents_df['name'].notna()]
        
        # Import each agent
        logger.info(f"Importing {len(agents_df)} agents to Asana...")
        for _, row in agents_df.iterrows():
            try:
                agent_data = format_agent_data(row)
                asana.create_task_for_agent(agent_data)
                logger.info(f"Created task for {row['name']}")
            except Exception as e:
                logger.error(f"Error creating task for {row['name']}: {str(e)}")
        
        logger.info("Import complete!")
        
    except Exception as e:
        logger.error(f"Error importing agents: {str(e)}")

if __name__ == "__main__":
    main()
