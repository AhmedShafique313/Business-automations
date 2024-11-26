import logging
from datetime import datetime
import json
from pathlib import Path

class BaseAgent:
    def __init__(self, name, work_dir):
        self.name = name
        self.work_dir = Path(work_dir)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup agent-specific logging"""
        log_file = self.work_dir / f'{self.name.lower()}_agent.log'
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
    def save_work(self, work_item, category):
        """Save work items to JSON file"""
        timestamp = datetime.now().isoformat()
        work_file = self.work_dir / f'{category}_{timestamp}.json'
        
        with open(work_file, 'w') as f:
            json.dump({
                'agent': self.name,
                'timestamp': timestamp,
                'category': category,
                'content': work_item
            }, f, indent=2)
            
        return work_file
        
    def load_work(self, work_file):
        """Load work items from JSON file"""
        with open(work_file, 'r') as f:
            return json.load(f)
            
    def log_activity(self, activity, status, details=None):
        """Log agent activity with structured format"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent': self.name,
            'activity': activity,
            'status': status
        }
        if details:
            log_entry['details'] = details
            
        self.logger.info(json.dumps(log_entry))
