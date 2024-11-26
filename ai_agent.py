import pyautogui
import cv2
import numpy as np
import pytesseract
from pynput import keyboard, mouse
import openai
from PIL import Image, ImageGrab
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import time
import logging
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import tempfile
import threading
from task_manager import TaskManager
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from pythonjsonlogger import jsonlogger

class AIAgent:
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4"  # or "gpt-3.5-turbo" for lower cost
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Initialize screen control
        pyautogui.FAILSAFE = True
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Initialize input controllers
        self.keyboard_controller = keyboard.Controller()
        self.mouse_controller = mouse.Controller()
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Calibrate the recognizer for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        self.task_manager = TaskManager()
        
        self.logger.info("AI Agent initialized successfully")
        
        # Start voice command listener in background
        self.voice_command_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        self.voice_command_thread.start()

    def setup_logging(self):
        """Setup JSON logging with detailed error tracking"""
        logHandler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            timestamp=True
        )
        logHandler.setFormatter(formatter)
        self.logger = logging.getLogger('AIAgent')
        self.logger.addHandler(logHandler)
        self.logger.setLevel(logging.INFO)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_completion(self, prompt, temperature=0.7, max_tokens=1000):
        """Get completion from OpenAI with retry logic"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error getting AI response: {str(e)}", 
                            extra={
                                'prompt': prompt,
                                'temperature': temperature,
                                'max_tokens': max_tokens,
                                'error': str(e)
                            })
            raise

    def listen_for_commands(self):
        """Continuously listen for voice commands"""
        while True:
            try:
                command = self.listen()
                if command:
                    response = self.handle_voice_command(command)
                    self.speak(response)
            except Exception as e:
                self.logger.error(f"Error in voice command loop: {str(e)}")
            time.sleep(0.1)  # Small delay to prevent high CPU usage

    def listen(self):
        """Listen for voice input and convert to text"""
        try:
            with self.microphone as source:
                self.logger.info("Listening for voice input...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
            text = self.recognizer.recognize_google(audio)
            self.logger.info(f"Recognized text: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            self.logger.info("Could not understand audio")
            return None
        except Exception as e:
            self.logger.error(f"Error in speech recognition: {str(e)}")
            return None

    def speak(self, text):
        """Convert text to speech and play it"""
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_filename = fp.name
                
            # Generate speech
            tts = gTTS(text=text, lang='en')
            tts.save(temp_filename)
            
            # Play the audio
            playsound(temp_filename)
            
            # Clean up the temporary file
            os.unlink(temp_filename)
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {str(e)}")

    def handle_voice_command(self, command):
        """Process voice commands and return response"""
        try:
            # Add task management commands
            if "manage instagram" in command.lower():
                parameters = {
                    "username": os.getenv("INSTAGRAM_USERNAME"),
                    "password": os.getenv("INSTAGRAM_PASSWORD"),
                    "actions": ["like_posts", "follow_users"],
                    "content": []  # Add content if needed
                }
                self.task_manager.add_task("instagram", parameters)
                return "I've started managing your Instagram account. I'll handle liking posts and following users automatically."
            
            elif "monitor website" in command.lower():
                # Extract URL from command or use default
                url = "https://example.com"  # Replace with actual URL extraction
                parameters = {"url": url}
                self.task_manager.add_task("website_monitor", parameters, schedule_type="interval", interval=300)
                return f"I'll monitor {url} every 5 minutes for changes or issues."
            
            elif "manage email" in command.lower():
                parameters = {
                    "email": os.getenv("EMAIL_ADDRESS"),
                    "password": os.getenv("EMAIL_PASSWORD"),
                    "rules": ["sort_inbox", "reply_to_important"]
                }
                self.task_manager.add_task("email_management", parameters)
                return "I'll manage your email account, sorting messages and handling important replies."
            
            elif "stop all tasks" in command.lower():
                self.task_manager.stop_all_tasks()
                return "I've stopped all running tasks."
            
            elif "list tasks" in command.lower():
                tasks = self.task_manager.tasks
                if tasks:
                    task_list = "\n".join([f"- {task_id}: {task.task_type}" for task_id, task in tasks.items()])
                    return f"Currently running tasks:\n{task_list}"
                else:
                    return "No tasks are currently running."
            
            # Get AI response for the command
            response = self.get_completion(f"User said: {command}. Please provide a brief and helpful response.")
            
            # Process specific commands
            lower_command = command.lower()
            
            if "take screenshot" in lower_command:
                screen = self.capture_screen()
                text = self.analyze_screen_content(screen)
                return f"I took a screenshot and found the following text: {text}"
            
            elif "browse" in lower_command and "website" in lower_command:
                url = "https://example.com"  # Default URL, can be extracted from command
                content = self.analyze_webpage(url)
                return f"I browsed the website and found its title: {content.title.string if content.title else 'No title found'}"
            
            elif "click" in lower_command:
                x, y = self.screen_width // 2, self.screen_height // 2  # Default to center
                self.click(x, y)
                return "I clicked at the specified location"
            
            return response if response else "I'm not sure how to help with that"
            
        except Exception as e:
            self.logger.error(f"Error processing voice command: {str(e)}")
            return "Sorry, I encountered an error processing your command"

    def capture_screen(self, region=None):
        """Capture the screen or a specific region"""
        try:
            screenshot = ImageGrab.grab(bbox=region)
            return np.array(screenshot)
        except Exception as e:
            self.logger.error(f"Error capturing screen: {str(e)}")
            return None

    def analyze_screen_content(self, image):
        """Analyze screen content using OCR"""
        try:
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error analyzing screen content: {str(e)}")
            return ""

    def click(self, x, y):
        """Perform mouse click at specified coordinates"""
        try:
            pyautogui.click(x, y)
            self.logger.info(f"Clicked at coordinates ({x}, {y})")
        except Exception as e:
            self.logger.error(f"Error performing click: {str(e)}")

    def type_text(self, text):
        """Type text using keyboard"""
        try:
            pyautogui.write(text)
            self.logger.info(f"Typed text: {text}")
        except Exception as e:
            self.logger.error(f"Error typing text: {str(e)}")

    def browse_web(self, url):
        """Browse web using Selenium"""
        try:
            driver = webdriver.Firefox()
            driver.get(url)
            return driver
        except Exception as e:
            self.logger.error(f"Error browsing web: {str(e)}")
            return None

    def analyze_webpage(self, url):
        """Analyze webpage content"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except Exception as e:
            self.logger.error(f"Error analyzing webpage: {str(e)}")
            return None

    def start(self):
        """Start the AI agent and restore previous tasks"""
        self.task_manager.start_all_tasks()
        self.voice_command_thread.start()

if __name__ == "__main__":
    agent = AIAgent()
    agent.start()
    print("AI Agent initialized and ready to use!")
