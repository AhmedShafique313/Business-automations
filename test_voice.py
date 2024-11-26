from ai_agent import AIAgent
import time

def test_voice_agent():
    print("Initializing AI Agent with voice capabilities...")
    agent = AIAgent()
    
    # Initial greeting
    agent.speak("Hello! I'm your AI assistant. I can help you with various tasks.")
    
    print("\nVoice Commands Examples:")
    print("1. 'Take screenshot' - Captures and analyzes screen content")
    print("2. 'Browse website' - Visits and analyzes a website")
    print("3. 'Click' - Performs a mouse click")
    print("4. Ask any question - Get AI-powered responses")
    
    print("\nListening for your commands... (Press Ctrl+C to exit)")
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    test_voice_agent()
