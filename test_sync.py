from agents.sync_tasks import TaskSyncManager

def test_agent_sync():
    # Create sample agent data
    agent_data = {
        "name": "John Smith",
        "email": "john.smith@luxuryrealty.com",
        "phone": "+1 (416) 555-0123",
        "agency": "Luxury Realty Toronto",
        "status": "In Progress",
        "communications": [
            {
                "date": "2024-01-23",
                "platform": "Email",
                "status": "Initial Contact",
                "details": "Sent introduction email about Design Gaga's services"
            },
            {
                "date": "2024-01-24",
                "platform": "LinkedIn",
                "status": "Connected",
                "details": "Connected on LinkedIn and shared portfolio"
            }
        ],
        "properties": [
            {
                "address": "123 Luxury Ave, Toronto",
                "price": "$2,500,000",
                "status": "Active Listing"
            }
        ],
        "notes": "Specializes in luxury condos in downtown Toronto. Shows strong interest in design services."
    }

    # Initialize sync manager and update task
    sync_manager = TaskSyncManager()
    success = sync_manager.update_agent_communication(agent_data)
    
    if success:
        print("Successfully updated agent task in Asana")
    else:
        print("Failed to update agent task")

if __name__ == "__main__":
    test_agent_sync()
