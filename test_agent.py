from ai_agent import AIAgent
import time

def test_agent():
    print("Initializing AI Agent...")
    agent = AIAgent()
    
    # Test 1: Screen Capture and Analysis
    print("\nTest 1: Screen Capture and Analysis")
    print("Capturing screen...")
    screen = agent.capture_screen()
    if screen is not None:
        print("Screen captured successfully!")
        print("Analyzing screen content...")
        text = agent.analyze_screen_content(screen)
        print(f"Text found on screen: {text}")
    
    # Test 2: AI Response
    print("\nTest 2: AI Response")
    prompt = "What are the three most important things to consider when writing Python code?"
    print(f"Getting AI response for prompt: {prompt}")
    response = agent.get_ai_response(prompt)
    print(f"AI Response: {response}")
    
    # Test 3: Web Analysis
    print("\nTest 3: Web Analysis")
    url = "https://example.com"
    print(f"Analyzing webpage: {url}")
    content = agent.analyze_webpage(url)
    if content:
        print("Successfully retrieved webpage content!")
        print(f"Page title: {content.title.string if content.title else 'No title found'}")

if __name__ == "__main__":
    test_agent()
