from datetime import datetime, timedelta
import asana
import os
from credentials_manager import CredentialsManager

class DesignGagaTasks:
    def __init__(self):
        # Initialize credentials manager and get Asana credentials
        creds_manager = CredentialsManager()
        asana_creds = creds_manager.get_credentials('ASANA')
        
        # Use the access token from credentials
        self.client = asana.Client.access_token(asana_creds['access_token'])
        self.workspace_gid = asana_creds['workspace_id']
        self.company_name = os.getenv('COMPANY_NAME', 'Design Gaga')
        self.project_gid = self._get_or_create_project(f"{self.company_name} Business Generation")
        
    def _get_or_create_project(self, project_name):
        """Get or create the business generation project"""
        try:
            # List all projects in the workspace
            projects = list(self.client.projects.get_projects({'workspace': self.workspace_gid}))
            
            # Try to find existing project
            for project in projects:
                if project['name'] == project_name:
                    print(f"Found existing project: {project_name}")
                    return project['gid']
            
            # Create new project if it doesn't exist
            print(f"Creating new project: {project_name}")
            new_project = self.client.projects.create_project({
                'name': project_name,
                'workspace': self.workspace_gid,
                'notes': f'Automated business generation tasks for {self.company_name}',
                'default_view': 'list',
                'color': 'light-green'
            })
            return new_project['gid']
            
        except Exception as e:
            print(f"Error in project creation: {str(e)}")
            raise

    def setup_sections(self):
        """Create sections for different business generation activities"""
        sections = [
            "List Building",  # New section for list building agents
            "Lead Generation",
            "Client Engagement",
            "Content Creation",
            "Marketing & Social Media",
            "Business Development"
        ]
        
        section_gids = {}
        for section_name in sections:
            try:
                print(f"Creating new section: {section_name}")
                new_section = self.client.sections.create_section_for_project(
                    self.project_gid,
                    {'name': section_name}
                )
                section_gids[section_name] = new_section['gid']
            except Exception as e:
                print(f"Error creating section {section_name}: {str(e)}")
                
        return section_gids

    def create_list_building_tasks(self, section_gid):
        """Create tasks for list building agents"""
        tasks = [
            {
                'name': 'Build Real Estate Agent Database - Luxury Market',
                'notes': '''
                Target: High-end real estate agents
                Focus Areas:
                - Identify agents specializing in luxury properties
                - Research top-performing agents in target areas
                - Track recent luxury property sales
                
                Data Points to Collect:
                - Agent Name
                - Brokerage
                - Contact Information
                - Recent Luxury Listings
                - Social Media Presence
                - Transaction History
                
                Tools:
                - MLS Database
                - LinkedIn Sales Navigator
                - Real Estate Websites
                - Social Media Platforms
                ''',
                'due_on': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            },
            {
                'name': 'Research Active Real Estate Teams',
                'notes': '''
                Target: Real Estate Teams with High Volume
                Research Focus:
                - Team size and structure
                - Monthly transaction volume
                - Areas of operation
                - Marketing strategies
                
                Data Collection:
                - Team Lead Contact Info
                - Team Performance Metrics
                - Marketing Channels Used
                - Current Home Staging Partnerships
                
                Sources:
                - Brokerage Websites
                - Team Websites
                - Social Media
                - Industry Reports
                ''',
                'due_on': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            }
        ]
        
        for task in tasks:
            print(f"Creating task: {task['name']}")
            self.client.tasks.create_task({
                'name': task['name'],
                'notes': task['notes'],
                'projects': [self.project_gid],
                'section': section_gid,
                'due_on': task['due_on']
            })

    def create_lead_generation_tasks(self, section_gid):
        """Create tasks for lead generation agents"""
        tasks = [
            {
                'name': 'Identify High-Potential Real Estate Partnerships',
                'notes': '''
                Objective: Find and qualify potential real estate agent partners
                
                Actions:
                - Analyze recent luxury property listings
                - Review agent social media presence
                - Assess current staging practices
                - Evaluate partnership potential
                
                Qualification Criteria:
                - Monthly listing volume
                - Price range of listings
                - Current staging solutions
                - Marketing investment level
                ''',
                'due_on': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            },
            {
                'name': 'Generate Warm Leads from Social Media',
                'notes': '''
                Platform Focus:
                - Instagram
                - LinkedIn
                - Facebook Groups
                
                Actions:
                - Engage with agent content
                - Comment on relevant posts
                - Share valuable staging insights
                - Direct message qualified leads
                
                Tracking:
                - Engagement rates
                - Response rates
                - Lead quality scores
                ''',
                'due_on': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            }
        ]
        
        for task in tasks:
            print(f"Creating task: {task['name']}")
            self.client.tasks.create_task({
                'name': task['name'],
                'notes': task['notes'],
                'projects': [self.project_gid],
                'section': section_gid,
                'due_on': task['due_on']
            })

    def create_client_engagement_tasks(self, section_gid):
        """Create tasks for client engagement agents"""
        tasks = [
            {
                'name': 'Automated Follow-up Sequence',
                'notes': '''
                Communication Channels:
                - Email
                - LinkedIn
                - Phone
                
                Sequence Steps:
                1. Initial connection
                2. Value proposition
                3. Portfolio showcase
                4. Case study sharing
                5. Meeting request
                
                Content Focus:
                - ROI of home staging
                - Recent success stories
                - Market trends
                - Staging tips
                ''',
                'due_on': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            },
            {
                'name': 'Relationship Nurturing Campaign',
                'notes': '''
                Engagement Activities:
                - Share market insights
                - Provide staging tips
                - Offer exclusive content
                - Send personalized updates
                
                Tracking Metrics:
                - Response rates
                - Content engagement
                - Meeting conversions
                - Partnership progress
                ''',
                'due_on': (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d')
            }
        ]
        
        for task in tasks:
            print(f"Creating task: {task['name']}")
            self.client.tasks.create_task({
                'name': task['name'],
                'notes': task['notes'],
                'projects': [self.project_gid],
                'section': section_gid,
                'due_on': task['due_on']
            })

    def create_content_tasks(self, section_gid):
        """Create tasks for content creation agents"""
        tasks = [
            {
                'name': 'Create Before/After Portfolio Content',
                'notes': '''
                Content Types:
                - Photo galleries
                - Video walkthroughs
                - Time-lapse transformations
                
                Key Elements:
                - Professional photography
                - Staging process highlights
                - Design elements showcase
                - ROI statistics
                
                Distribution:
                - Website portfolio
                - Social media
                - Email campaigns
                - Agent presentations
                ''',
                'due_on': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            },
            {
                'name': 'Develop Educational Content Series',
                'notes': '''
                Topics:
                - Home staging best practices
                - ROI of professional staging
                - Market trends analysis
                - Design psychology
                
                Formats:
                - Blog posts
                - Video tutorials
                - Infographics
                - Case studies
                
                Distribution Channels:
                - Blog
                - YouTube
                - Social media
                - Email newsletter
                ''',
                'due_on': (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')
            }
        ]
        
        for task in tasks:
            print(f"Creating task: {task['name']}")
            self.client.tasks.create_task({
                'name': task['name'],
                'notes': task['notes'],
                'projects': [self.project_gid],
                'section': section_gid,
                'due_on': task['due_on']
            })

    def create_marketing_tasks(self, section_gid):
        """Create tasks for marketing agents"""
        tasks = [
            {
                'name': 'Launch Targeted Ad Campaigns',
                'notes': '''
                Platforms:
                - Facebook/Instagram Ads
                - LinkedIn Ads
                - Google Ads
                
                Campaign Focus:
                - Real estate agent targeting
                - Portfolio showcasing
                - Success stories
                - ROI demonstrations
                
                Metrics:
                - Click-through rates
                - Lead generation
                - Cost per acquisition
                - ROI tracking
                ''',
                'due_on': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            },
            {
                'name': 'Social Media Engagement Strategy',
                'notes': '''
                Platforms:
                - Instagram
                - LinkedIn
                - Facebook Groups
                
                Content Mix:
                - Before/After showcases
                - Design tips
                - Market insights
                - Client testimonials
                
                Engagement Tasks:
                - Daily posting
                - Comment responses
                - Story updates
                - Live sessions
                ''',
                'due_on': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            }
        ]
        
        for task in tasks:
            print(f"Creating task: {task['name']}")
            self.client.tasks.create_task({
                'name': task['name'],
                'notes': task['notes'],
                'projects': [self.project_gid],
                'section': section_gid,
                'due_on': task['due_on']
            })

    def create_business_development_tasks(self, section_gid):
        """Create tasks for business development agents"""
        tasks = [
            {
                'name': 'Analyze Market Opportunities',
                'notes': '''
                Research Areas:
                - Market trends
                - Competitor analysis
                - Pricing strategies
                - Service expansion
                
                Focus Points:
                - Luxury market segment
                - Virtual staging demand
                - Partnership opportunities
                - Technology integration
                
                Deliverables:
                - Market report
                - Growth recommendations
                - Strategic partnerships
                - Service innovations
                ''',
                'due_on': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            },
            {
                'name': 'Develop Strategic Partnerships',
                'notes': '''
                Target Partners:
                - Real estate brokerages
                - Interior designers
                - Property photographers
                - Home improvement services
                
                Partnership Models:
                - Referral programs
                - Co-marketing
                - Service bundling
                - Joint ventures
                
                Action Items:
                - Partner identification
                - Proposal development
                - Negotiation strategy
                - Agreement structure
                ''',
                'due_on': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
            }
        ]
        
        for task in tasks:
            print(f"Creating task: {task['name']}")
            self.client.tasks.create_task({
                'name': task['name'],
                'notes': task['notes'],
                'projects': [self.project_gid],
                'section': section_gid,
                'due_on': task['due_on']
            })

    def setup_all_tasks(self):
        """Set up all sections and tasks"""
        try:
            print("\n🚀 Setting up project structure...")
            
            # Create sections
            sections = self.setup_sections()
            
            # Create tasks for each section
            print("\n📝 Creating tasks for each section...")
            
            self.create_list_building_tasks(sections['List Building'])
            self.create_lead_generation_tasks(sections['Lead Generation'])
            self.create_client_engagement_tasks(sections['Client Engagement'])
            self.create_content_tasks(sections['Content Creation'])
            self.create_marketing_tasks(sections['Marketing & Social Media'])
            self.create_business_development_tasks(sections['Business Development'])
            
            print("\n✅ All tasks created successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error in setup_all_tasks: {str(e)}")
            return False

if __name__ == "__main__":
    tasks = DesignGagaTasks()
    tasks.setup_all_tasks()
