#!/usr/bin/env python3

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.io as pio
from intelligence.case_study_analyzer import CaseStudyAnalyzer
from intelligence.case_study_collector import CaseStudyCollector
from intelligence.notification_system import NotificationSystem
from intelligence.orchestrator import IntelligenceOrchestrator
from intelligence.performance_monitor import PerformanceMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_case_study_collector():
    """Test case study collection functionality."""
    logger.info("Testing case study collector...")
    
    collector = CaseStudyCollector('intelligence/config.json')
    
    # Test data collection for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        case_studies = collector.collect_case_study(
            case_id="test_case_1",
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Successfully collected case study data: {case_studies}")
        
    except Exception as e:
        logger.error(f"Error in case study collection: {e}")
        raise

def test_case_study_analyzer():
    """Test case study analysis functionality."""
    logger.info("Testing case study analyzer...")
    
    analyzer = CaseStudyAnalyzer('intelligence/config.json')
    
    try:
        # Create test data
        test_data = [
            {
                'content_length': 500,
                'image_count': 2,
                'video_count': 1,
                'hashtag_count': 5,
                'hour': 14,
                'day_of_week': 2,
                'engagement_rate': 0.05,
                'likes_ratio': 0.05,
                'comments_ratio': 0.02,
                'shares_ratio': 0.01,
                'saves_ratio': 0.03,
                'age_group': '25-34',
                'gender': 'F',
                'location': 'US',
                'interests': ['luxury', 'real estate'],
                'awareness_rate': 0.08,
                'consideration_rate': 0.06,
                'action_rate': 0.04,
                'retention_rate': 0.03
            },
            {
                'content_length': 800,
                'image_count': 3,
                'video_count': 0,
                'hashtag_count': 7,
                'hour': 10,
                'day_of_week': 3,
                'engagement_rate': 0.07,
                'likes_ratio': 0.07,
                'comments_ratio': 0.03,
                'shares_ratio': 0.02,
                'saves_ratio': 0.04,
                'age_group': '35-44',
                'gender': 'M',
                'location': 'UK',
                'interests': ['luxury', 'interior design'],
                'awareness_rate': 0.09,
                'consideration_rate': 0.07,
                'action_rate': 0.05,
                'retention_rate': 0.04
            },
            {
                'content_length': 300,
                'image_count': 1,
                'video_count': 2,
                'hashtag_count': 4,
                'hour': 18,
                'day_of_week': 5,
                'engagement_rate': 0.04,
                'likes_ratio': 0.04,
                'comments_ratio': 0.01,
                'shares_ratio': 0.01,
                'saves_ratio': 0.02,
                'age_group': '18-24',
                'gender': 'F',
                'location': 'CA',
                'interests': ['real estate', 'home decor'],
                'awareness_rate': 0.06,
                'consideration_rate': 0.04,
                'action_rate': 0.02,
                'retention_rate': 0.02
            }
        ]
        
        # Analyze patterns
        patterns = analyzer.analyze_case_studies(test_data)
        logger.info(f"Successfully analyzed patterns: {patterns}")
        
    except Exception as e:
        logger.error(f"Error in case study analysis: {e}")
        raise

def test_performance_monitor():
    """Test performance monitoring functionality."""
    logger.info("Testing performance monitor...")
    
    monitor = PerformanceMonitor('intelligence/config.json')
    
    try:
        # Test metrics collection
        metrics = monitor.collect_daily_metrics()
        logger.info(f"Collected daily metrics: {metrics}")
        
        # Test report generation
        monitor.generate_weekly_report()
        logger.info("Generated weekly report")
        
    except Exception as e:
        logger.error(f"Error in performance monitoring: {e}")
        raise

def test_notification_system():
    """Test notification system functionality."""
    logger.info("Testing notification system...")
    
    notifier = NotificationSystem('intelligence/config.json')
    
    try:
        # Create test report data with proper structure
        report_data = {
            'metrics': {
                'engagement': {
                    'daily_engagement': {
                        'rate': 4.8,
                        'trend': '+10%',
                        'status': 'excellent'
                    },
                    'comments_ratio': {
                        'rate': 2.5,
                        'trend': '+5%',
                        'status': 'good'
                    }
                },
                'conversion': {
                    'conversion_rate': {
                        'rate': 3.2,
                        'trend': '+15%',
                        'status': 'good'
                    },
                    'revenue': {
                        'amount': 2200,
                        'trend': '+20%',
                        'status': 'excellent'
                    }
                }
            },
            'patterns': {
                'content': {
                    'optimal_post_length': 800,
                    'optimal_image_count': 3,
                    'optimal_video_count': 1
                },
                'timing': {
                    'optimal_posting_hours': [10, 14, 18],
                    'optimal_posting_days': ['Mon', 'Wed', 'Fri']
                },
                'audience': {
                    'top_age_groups': ['25-34', '35-44'],
                    'top_locations': ['US', 'UK', 'CA']
                }
            },
            'recommendations': [
                'Increase posting frequency during peak hours (10 AM, 2 PM, and 6 PM)',
                'Focus on video content to boost engagement',
                'Target content for the 25-34 age demographic',
                'Optimize landing page conversion elements',
                'Implement upselling strategies for higher revenue'
            ]
        }
        
        # Send test report
        notifier.send_performance_report(report_data)
        logger.info("Successfully sent test report")
        
    except Exception as e:
        logger.error(f"Error in notification system: {e}")
        raise

def test_intelligence_orchestrator():
    """Test the complete intelligence system orchestration."""
    logger.info("Testing intelligence orchestrator...")
    
    orchestrator = IntelligenceOrchestrator('intelligence/config.json')
    
    try:
        # Test pattern analysis
        patterns = orchestrator.analyze_successful_patterns()
        logger.info(f"Analyzed patterns: {patterns}")
        
        # Test performance monitoring
        performance_data = orchestrator.monitor_performance()
        logger.info(f"Monitored performance: {performance_data}")
        
        # Generate and send report
        orchestrator.generate_weekly_report()
        logger.info("Generated and sent weekly report")
        
    except Exception as e:
        logger.error(f"Error in intelligence orchestration: {e}")
        raise

def main():
    """Run all tests."""
    try:
        # Create necessary directories
        Path('data').mkdir(exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        Path('reports').mkdir(exist_ok=True)
        
        # Run tests
        test_case_study_collector()
        test_case_study_analyzer()
        test_performance_monitor()
        test_notification_system()
        test_intelligence_orchestrator()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise

if __name__ == '__main__':
    main()
