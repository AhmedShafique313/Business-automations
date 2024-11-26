import os
from dotenv import load_dotenv
from asana_tasks import DesignGagaTasks
from business_generator import BusinessGenerator
from task_executor import TaskExecutor
from credentials import CredentialsManager
import threading
import time
import sys

def main():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize credentials manager
        print("Initializing credentials...")
        creds_manager = CredentialsManager()
        
        # Initialize business generator and Asana tasks
        print("Setting up Asana integration...")
        business_generator = BusinessGenerator()
        asana_tasks = DesignGagaTasks()
        
        # Set up Asana workspace and tasks
        print("\nCreating Asana project and tasks...")
        asana_tasks.setup_all_tasks()
        
        print("\n✅ Business generation system is now active!")
        print("\nThe following tasks have been created in Asana:")
        print("1. Lead Generation")
        print("   - Monitor Real Estate Listings")
        print("   - Real Estate Agent Outreach")
        print("\n2. Social Media Management")
        print("   - Generate Social Media Content")
        print("   - Social Media Engagement")
        print("\n3. Email Campaigns")
        print("   - Real Estate Agent Email Campaign")
        print("   - Property Owner Newsletter")
        print("\n4. Market Analysis")
        print("   - Market Trend Analysis")
        print("   - Competitor Analysis")
        print("\n5. Partnership Development")
        print("   - Real Estate Agency Partnerships")
        print("   - Interior Designer Network")
        
        print("\nStarting automated task execution...")
        
        # Initialize and start task executor in a separate thread
        executor = TaskExecutor()
        executor_thread = threading.Thread(target=executor.schedule_daily_updates)
        executor_thread.daemon = True
        executor_thread.start()
        
        print("\n📅 Tasks will be automatically executed and updated daily:")
        print("• 09:00 - Monitor Real Estate Listings")
        print("• 10:00 - Generate Social Media Content")
        print("• 11:00 - Real Estate Agent Outreach")
        print("• 14:00 - Market Trend Analysis")
        print("• 15:00 - Real Estate Agent Email Campaign")
        
        print("\n🔗 Check your Asana workspace to view tasks and daily updates:")
        print("https://app.asana.com/")
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down task executor...")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nPlease check:")
        print("1. Your Asana credentials are correct")
        print("2. You have internet connection")
        print("3. Asana API is accessible")
        sys.exit(1)

if __name__ == "__main__":
    main()
