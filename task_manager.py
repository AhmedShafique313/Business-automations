import json
import threading
import schedule
import time
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import os
from asana_integration import AsanaIntegration
import requests

class Task:
    def __init__(self, task_id, task_type, parameters, schedule_type="continuous", interval=None):
        self.task_id = task_id
        self.task_type = task_type
        self.parameters = parameters
        self.schedule_type = schedule_type  # continuous, interval, daily, weekly
        self.interval = interval
        self.last_run = None
        self.is_running = False
        self.thread = None
        self.asana_task_gid = None  # Store Asana task GID

class TaskManager:
    def __init__(self, tasks_file="tasks.json"):
        self.tasks_file = tasks_file
        self.tasks = {}
        self.load_tasks()
        self.setup_logging()
        
        # Initialize Asana integration
        try:
            self.asana = AsanaIntegration()
        except Exception as e:
            self.logger.error(f"Failed to initialize Asana integration: {str(e)}")
            self.asana = None
        
        # Initialize task handlers
        self.task_handlers = {
            "instagram": self.handle_instagram,
            "website_monitor": self.handle_website_monitoring,
            "email_management": self.handle_email_management,
            "system_maintenance": self.handle_system_maintenance,
            # Add more task handlers here
        }

    def setup_logging(self):
        logging.basicConfig(
            filename='task_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('TaskManager')

    def load_tasks(self):
        """Load tasks from JSON file"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r') as f:
                    tasks_data = json.load(f)
                    for task_data in tasks_data:
                        task = Task(**task_data)
                        self.tasks[task.task_id] = task
        except Exception as e:
            self.logger.error(f"Error loading tasks: {str(e)}")

    def save_tasks(self):
        """Save tasks to JSON file"""
        try:
            tasks_data = []
            for task in self.tasks.values():
                task_dict = task.__dict__.copy()
                task_dict.pop('thread', None)  # Remove thread object before saving
                tasks_data.append(task_dict)
            
            with open(self.tasks_file, 'w') as f:
                json.dump(tasks_data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving tasks: {str(e)}")

    def add_task(self, task_type, parameters, schedule_type="continuous", interval=None):
        """Add a new task"""
        task_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = Task(task_id, task_type, parameters, schedule_type, interval)
        self.tasks[task_id] = task
        
        # Create task in Asana
        if self.asana:
            try:
                task.asana_task_gid = self.asana.create_task(
                    task_id,
                    task_type,
                    parameters,
                    "Starting"
                )
            except Exception as e:
                self.logger.error(f"Failed to create Asana task: {str(e)}")
        
        self.save_tasks()
        self.start_task(task_id)
        return task_id

    def remove_task(self, task_id):
        """Remove a task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            self.stop_task(task_id)
            
            # Delete task from Asana
            if self.asana and task.asana_task_gid:
                try:
                    self.asana.delete_task(task.asana_task_gid)
                except Exception as e:
                    self.logger.error(f"Failed to delete Asana task: {str(e)}")
            
            del self.tasks[task_id]
            self.save_tasks()

    def start_task(self, task_id):
        """Start a task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.is_running:
            return True

        if task.task_type in self.task_handlers:
            task.is_running = True
            task.thread = threading.Thread(
                target=self._run_task_loop,
                args=(task,),
                daemon=True
            )
            task.thread.start()
            self.logger.info(f"Started task: {task_id}")
            return True
        return False

    def stop_task(self, task_id):
        """Stop a task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.is_running = False
            if task.thread:
                task.thread.join(timeout=1)
            
            # Update Asana status to Stopped
            if self.asana and task.asana_task_gid:
                try:
                    self.asana.update_task_status(task.asana_task_gid, "Stopped")
                except Exception as e:
                    self.logger.error(f"Failed to update Asana task status: {str(e)}")
            
            self.logger.info(f"Stopped task: {task_id}")

    def _run_task_loop(self, task):
        """Main task execution loop"""
        # Update Asana status to Running
        if self.asana and task.asana_task_gid:
            try:
                self.asana.update_task_status(task.asana_task_gid, "Running")
            except Exception as e:
                self.logger.error(f"Failed to update Asana task status: {str(e)}")
        
        while task.is_running:
            try:
                handler = self.task_handlers[task.task_type]
                handler(task.parameters)
                
                if task.schedule_type == "interval" and task.interval:
                    time.sleep(task.interval)
                elif task.schedule_type == "continuous":
                    time.sleep(1)  # Small delay to prevent CPU overload
                
                task.last_run = datetime.now()
                
                # Update Asana with success status
                if self.asana and task.asana_task_gid:
                    try:
                        self.asana.update_task_status(task.asana_task_gid, "Running")
                    except Exception as e:
                        self.logger.error(f"Failed to update Asana task status: {str(e)}")
                
            except Exception as e:
                error_msg = f"Error in task {task.task_id}: {str(e)}"
                self.logger.error(error_msg)
                
                # Update Asana with error status
                if self.asana and task.asana_task_gid:
                    try:
                        self.asana.update_task_status(task.asana_task_gid, "Error", error_msg)
                    except Exception as asana_error:
                        self.logger.error(f"Failed to update Asana task status: {str(asana_error)}")
                
                time.sleep(60)  # Wait before retrying on error

    # Task Handlers
    def handle_instagram(self, parameters):
        """Handle Instagram automation"""
        try:
            driver = webdriver.Firefox()
            driver.get("https://www.instagram.com")
            
            # Login
            if 'username' in parameters and 'password' in parameters:
                username_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                username_input.send_keys(parameters['username'])
                
                password_input = driver.find_element(By.NAME, "password")
                password_input.send_keys(parameters['password'])
                
                login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_button.click()
                
                # Wait for login
                time.sleep(5)
                
                # Perform automated actions
                if 'actions' in parameters:
                    for action in parameters['actions']:
                        if action == 'like_posts':
                            self._like_posts(driver)
                        elif action == 'follow_users':
                            self._follow_users(driver)
                        elif action == 'post_content':
                            self._post_content(driver, parameters.get('content', []))
            
            driver.quit()
        except Exception as e:
            self.logger.error(f"Instagram automation error: {str(e)}")

    def handle_website_monitoring(self, parameters):
        """Handle website monitoring"""
        try:
            url = parameters.get('url')
            if url:
                response = requests.get(url)
                if response.status_code != 200:
                    self.logger.warning(f"Website {url} returned status code {response.status_code}")
        except Exception as e:
            self.logger.error(f"Website monitoring error: {str(e)}")

    def handle_email_management(self, parameters):
        """Handle email management"""
        # Implement email management logic
        pass

    def handle_system_maintenance(self, parameters):
        """Handle system maintenance"""
        # Implement system maintenance logic
        pass

    # Helper methods for Instagram
    def _like_posts(self, driver):
        """Like posts on Instagram"""
        try:
            # Find and like posts
            like_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='button']")
            for button in like_buttons[:5]:  # Like up to 5 posts
                if random.random() < 0.7:  # 70% chance to like
                    button.click()
                    time.sleep(random.uniform(2, 5))
        except Exception as e:
            self.logger.error(f"Error liking posts: {str(e)}")

    def _follow_users(self, driver):
        """Follow users on Instagram"""
        try:
            # Find and follow users
            follow_buttons = driver.find_elements(By.CSS_SELECTOR, "button:contains('Follow')")
            for button in follow_buttons[:3]:  # Follow up to 3 users
                if random.random() < 0.5:  # 50% chance to follow
                    button.click()
                    time.sleep(random.uniform(2, 5))
        except Exception as e:
            self.logger.error(f"Error following users: {str(e)}")

    def _post_content(self, driver, content):
        """Post content on Instagram"""
        try:
            if content:
                # Click new post button
                new_post_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='New post']")
                new_post_button.click()
                time.sleep(2)
                
                # Upload content and add caption
                # Note: Actual implementation would depend on Instagram's current UI
                pass
        except Exception as e:
            self.logger.error(f"Error posting content: {str(e)}")

    def start_all_tasks(self):
        """Start all tasks"""
        for task_id in self.tasks:
            self.start_task(task_id)

    def stop_all_tasks(self):
        """Stop all tasks"""
        for task_id in self.tasks:
            self.stop_task(task_id)
