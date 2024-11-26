from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import time, timedelta
import json
import os
import datetime
from asana_tracker import AsanaTracker

@dataclass
class MessageConfig:
    template: str
    channel: str
    delay_hours: int = 0
    conditions: Dict = None
    a_b_test: Optional[Dict] = None
    priority: str = 'normal'
    
@dataclass
class CampaignStep:
    message: MessageConfig
    next_steps: List[str] = None
    
class CampaignConfig:
    def __init__(self):
        self.asana_tracker = AsanaTracker(os.getenv('ASANA_WORKSPACE_GID'))
        
        # Define campaign templates
        self.campaigns = {
            'luxury_welcome': {
                'steps': [
                    CampaignStep(
                        message=MessageConfig(
                            template='email_welcome_luxury',
                            channel='email',
                            conditions={'score_min': 70},
                            a_b_test={
                                'variants': ['modern_minimal', 'classic_elegant'],
                                'success_metric': 'response_rate'
                            }
                        ),
                        next_steps=['whatsapp_portfolio']
                    ),
                    CampaignStep(
                        message=MessageConfig(
                            template='whatsapp_portfolio',
                            channel='whatsapp',
                            delay_hours=48,
                            conditions={'no_response': True}
                        ),
                        next_steps=['linkedin_connect']
                    ),
                    CampaignStep(
                        message=MessageConfig(
                            template='linkedin_connect',
                            channel='linkedin',
                            delay_hours=24
                        )
                    )
                ],
                'priority': 'high'
            },
            
            'portfolio_showcase': {
                'steps': [
                    CampaignStep(
                        message=MessageConfig(
                            template='email_portfolio',
                            channel='email',
                            a_b_test={
                                'variants': ['lifestyle_focus', 'design_focus'],
                                'success_metric': 'click_rate'
                            }
                        ),
                        next_steps=['instagram_follow']
                    ),
                    CampaignStep(
                        message=MessageConfig(
                            template='instagram_follow',
                            channel='instagram',
                            delay_hours=24
                        ),
                        next_steps=['whatsapp_feedback']
                    )
                ],
                'priority': 'normal'
            },
            
            'referral_request': {
                'steps': [
                    CampaignStep(
                        message=MessageConfig(
                            template='email_referral',
                            channel='email',
                            conditions={'score_min': 90}
                        ),
                        next_steps=['linkedin_recommendation']
                    ),
                    CampaignStep(
                        message=MessageConfig(
                            template='linkedin_recommendation',
                            channel='linkedin',
                            delay_hours=72
                        )
                    )
                ],
                'priority': 'high'
            }
        }
        
        # Channel-specific timing settings
        self.timing_settings = {
            'email': {
                'optimal_times': [
                    time(9, 30),  # 9:30 AM
                    time(11, 0),  # 11:00 AM
                    time(14, 30),  # 2:30 PM
                    time(16, 0)   # 4:00 PM
                ],
                'quiet_hours': {
                    'start': time(18, 0),  # 6:00 PM
                    'end': time(8, 0)      # 8:00 AM
                },
                'frequency_cap': timedelta(days=1)
            },
            'whatsapp': {
                'optimal_times': [
                    time(10, 0),  # 10:00 AM
                    time(15, 0)   # 3:00 PM
                ],
                'quiet_hours': {
                    'start': time(19, 0),  # 7:00 PM
                    'end': time(9, 0)      # 9:00 AM
                },
                'frequency_cap': timedelta(days=2)
            },
            'linkedin': {
                'optimal_times': [
                    time(11, 0),  # 11:00 AM
                    time(13, 30)  # 1:30 PM
                ],
                'frequency_cap': timedelta(days=3)
            },
            'instagram': {
                'optimal_times': [
                    time(12, 0),  # 12:00 PM
                    time(17, 0)   # 5:00 PM
                ],
                'frequency_cap': timedelta(days=2)
            }
        }
        
        # A/B testing configuration
        self.ab_test_config = {
            'min_sample_size': 100,
            'confidence_level': 0.95,
            'metrics': {
                'response_rate': {
                    'type': 'percentage',
                    'success_threshold': 0.15  # 15% response rate
                },
                'click_rate': {
                    'type': 'percentage',
                    'success_threshold': 0.25  # 25% click rate
                },
                'conversion_rate': {
                    'type': 'percentage',
                    'success_threshold': 0.05  # 5% conversion rate
                }
            }
        }
        
    def get_campaign(self, campaign_type: str) -> Dict:
        """Get campaign configuration"""
        return self.campaigns.get(campaign_type)
        
    def get_next_send_time(self, channel: str, priority: str) -> time:
        """Get next optimal send time for channel"""
        channel_settings = self.timing_settings.get(channel, {})
        current_time = datetime.datetime.now().time()
        
        # Get optimal times for channel
        optimal_times = channel_settings.get('optimal_times', [time(9, 0)])
        
        # Adjust for priority
        if priority == 'high':
            # Add more time slots for high priority
            optimal_times = [
                t for t in optimal_times
            ] + [
                time((t.hour + 1) % 24, t.minute)
                for t in optimal_times
            ]
            
        # Find next available time
        for t in sorted(optimal_times):
            if t > current_time:
                # Check quiet hours
                quiet_hours = channel_settings.get('quiet_hours', {})
                if quiet_hours:
                    quiet_start = quiet_hours['start']
                    quiet_end = quiet_hours['end']
                    
                    # Skip if in quiet hours
                    if quiet_start < quiet_end:
                        if quiet_start <= t <= quiet_end:
                            continue
                    else:  # Handles overnight quiet hours
                        if t >= quiet_start or t <= quiet_end:
                            continue
                            
                return t
                
        # If no time found today, return first time tomorrow
        return optimal_times[0]
        
    def can_send_message(self, lead: Dict, channel: str) -> bool:
        """Check if we can send a message on this channel"""
        channel_settings = self.timing_settings.get(channel, {})
        
        # Check frequency cap
        if 'last_contact' in lead:
            last_contact = datetime.datetime.fromisoformat(lead['last_contact'])
            frequency_cap = channel_settings.get('frequency_cap', timedelta(days=1))
            
            if datetime.datetime.now() - last_contact < frequency_cap:
                return False
                
        # Check quiet hours
        quiet_hours = channel_settings.get('quiet_hours', {})
        if quiet_hours:
            current_time = datetime.datetime.now().time()
            quiet_start = quiet_hours['start']
            quiet_end = quiet_hours['end']
            
            # Check if current time is in quiet hours
            if quiet_start < quiet_end:
                if quiet_start <= current_time <= quiet_end:
                    return False
            else:  # Handles overnight quiet hours
                if current_time >= quiet_start or current_time <= quiet_end:
                    return False
                    
        return True
        
    def track_ab_test_result(self, test_name: str, variant: str, 
                            lead_gid: str, success: bool):
        """Track A/B test result in Asana"""
        # Find test configuration
        test_config = None
        for campaign in self.campaigns.values():
            for step in campaign['steps']:
                if step.message.a_b_test and test_name in step.message.template:
                    test_config = step.message.a_b_test
                    break
            if test_config:
                break
                
        if test_config:
            self.asana_tracker.track_ab_test_result(
                test_name, variant, lead_gid, success
            )
