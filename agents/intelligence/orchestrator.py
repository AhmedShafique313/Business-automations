import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json

from .case_study_analyzer import CaseStudyAnalyzer
from .case_study_collector import CaseStudyCollector
from .performance_monitor import PerformanceMonitor
from .notification_system import NotificationSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligenceOrchestrator:
    """Orchestrates the intelligence system components."""
    
    def __init__(self, config_path: str):
        """Initialize the intelligence orchestrator."""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.collector = CaseStudyCollector(config_path)
        self.analyzer = CaseStudyAnalyzer(config_path)
        self.monitor = PerformanceMonitor(config_path)
        self.notifier = NotificationSystem(config_path)
        
        # Create necessary directories
        self._initialize_directories()
    
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _initialize_directories(self) -> None:
        """Create necessary directories."""
        directories = [
            Path(self.config['case_studies']['data_path']),
            Path('reports'),
            Path('reports/temp'),
            Path('logs')
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def analyze_successful_patterns(self) -> Dict:
        """
        Analyze patterns from successful case studies.
        
        Returns:
            Dictionary containing identified patterns
        """
        try:
            # Get successful case studies
            case_studies = self.collector.get_successful_cases()
            
            # Analyze patterns
            patterns = self.analyzer.analyze_case_studies(case_studies)
            
            logger.info("Successfully analyzed patterns from case studies")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze patterns: {e}")
            raise
    
    def collect_case_study(self,
                          case_id: str,
                          start_date: datetime,
                          end_date: datetime) -> None:
        """
        Collect data for a new case study.
        
        Args:
            case_id: Unique identifier for the case study
            start_date: Start date for data collection
            end_date: End date for data collection
        """
        try:
            # Collect case study data
            self.collector.collect_case_study(case_id, start_date, end_date)
            
            # Re-analyze patterns with new data
            self.analyze_successful_patterns()
            
            logger.info(f"Successfully collected and analyzed case study {case_id}")
            
        except Exception as e:
            logger.error(f"Failed to collect case study: {e}")
            raise
    
    def monitor_performance(self) -> Dict:
        """
        Monitor current performance metrics.
        
        Returns:
            Dictionary containing current performance metrics
        """
        try:
            # Collect current metrics
            current_metrics = self.monitor.collect_daily_metrics()
            
            # Compare with patterns
            performance_data = self.analyzer.compare_with_patterns(current_metrics)
            
            logger.info("Successfully monitored performance")
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to monitor performance: {e}")
            raise
    
    def generate_weekly_report(self) -> None:
        """Generate and send weekly performance report."""
        try:
            # Get current performance data
            performance_data = self.monitor_performance()
            
            # Generate recommendations
            recommendations = self.analyzer.generate_recommendations()
            
            # Combine data for report
            report_data = {
                'metrics': performance_data,
                'recommendations': recommendations,
                'patterns': self.analyze_successful_patterns(),
                'next_actions': self._generate_next_actions(performance_data)
            }
            
            # Send report
            self.notifier.send_performance_report(
                report_data,
                recipient="gagan@designgaga.ca"
            )
            
            logger.info("Successfully generated and sent weekly report")
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            raise
    
    def _generate_next_actions(self, performance_data: Dict) -> List[str]:
        """Generate prioritized next actions based on performance data."""
        actions = []
        
        # Check content performance
        if performance_data['content']['engagement_rate'] < self.config['performance']['thresholds']['engagement_rate']['good']:
            actions.append("Improve content engagement by following successful content patterns")
        
        # Check timing performance
        timing_patterns = self.analyzer.success_patterns.get('timing', {})
        if timing_patterns:
            actions.append(f"Optimize posting schedule to match successful patterns: {timing_patterns}")
        
        # Check conversion performance
        if performance_data['conversion']['conversion_rate'] < self.config['performance']['thresholds']['conversion_rate']['good']:
            actions.append("Optimize conversion funnel based on successful patterns")
        
        return sorted(actions, key=lambda x: self._get_action_priority(x))
    
    def _get_action_priority(self, action: str) -> int:
        """Get priority score for an action."""
        priority_keywords = {
            'conversion': 3,
            'engagement': 2,
            'content': 2,
            'timing': 1
        }
        
        for keyword, priority in priority_keywords.items():
            if keyword in action.lower():
                return priority
        return 0
    
    def start(self) -> None:
        """Start the intelligence system."""
        try:
            logger.info("Starting intelligence system...")
            
            # Analyze initial patterns
            self.analyze_successful_patterns()
            
            # Start performance monitoring
            self.monitor.initialize_scheduler()
            
            logger.info("Intelligence system started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start intelligence system: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the intelligence system."""
        try:
            logger.info("Stopping intelligence system...")
            
            # Stop performance monitoring
            self.monitor.scheduler.shutdown()
            
            logger.info("Intelligence system stopped successfully")
            
        except Exception as e:
            logger.error(f"Failed to stop intelligence system: {e}")
            raise
