from base_agent import BaseAgent
import random
from datetime import datetime, timedelta

class MakerAgent(BaseAgent):
    def __init__(self, work_dir):
        super().__init__("Maker", work_dir)
        self.content_types = ['reel', 'post', 'story']
        self.expertise_areas = [
            'luxury_staging',
            'interior_design',
            'property_showcase',
            'design_tips'
        ]
        
    def generate_content(self):
        """Generate new content for social media"""
        content_type = random.choice(self.content_types)
        expertise = random.choice(self.expertise_areas)
        
        content = {
            'type': content_type,
            'expertise': expertise,
            'title': self._generate_title(expertise),
            'description': self._generate_description(expertise),
            'hashtags': self._generate_hashtags(expertise),
            'scheduling': self._generate_schedule(),
            'status': 'pending_review'
        }
        
        # Save the generated content
        work_file = self.save_work(content, f'content_{content_type}')
        self.log_activity(
            'content_generation',
            'completed',
            {'content_type': content_type, 'file': str(work_file)}
        )
        
        return work_file
        
    def _generate_title(self, expertise):
        """Generate engaging titles based on expertise area"""
        titles = {
            'luxury_staging': [
                "Transform Your Space: Luxury Home Staging Secrets",
                "Elevate Your Property with Professional Staging",
                "Design Gaga's Guide to Luxury Home Presentation"
            ],
            'interior_design': [
                "Timeless Interior Design Trends",
                "Creating Sophisticated Living Spaces",
                "Luxury Interior Design Made Simple"
            ]
        }
        return random.choice(titles.get(expertise, ["Luxury Home Design Tips"]))
        
    def _generate_description(self, expertise):
        """Generate detailed content description"""
        descriptions = {
            'luxury_staging': [
                "Discover how professional staging can transform your property into a luxury showcase. Our expert tips will help you create an irresistible presentation that attracts high-end buyers.",
                "Learn the art of luxury home staging with Design Gaga. We'll show you how to highlight your property's best features and create an emotional connection with potential buyers."
            ]
        }
        return random.choice(descriptions.get(expertise, ["Expert luxury home staging tips and tricks."]))
        
    def _generate_hashtags(self, expertise):
        """Generate relevant hashtags"""
        hashtag_sets = {
            'luxury_staging': [
                "#LuxuryHomeStaging", "#DesignGaga", "#InteriorDesign",
                "#LuxuryRealEstate", "#HomeStaging", "#PropertyStyling"
            ]
        }
        return random.sample(hashtag_sets.get(expertise, []), 4)
        
    def _generate_schedule(self):
        """Generate optimal posting schedule"""
        now = datetime.now()
        optimal_hours = [10, 14, 17, 20]  # Optimal posting times
        next_slot = min(optimal_hours, key=lambda x: abs(x - now.hour))
        
        if now.hour >= next_slot:
            # Move to next day if we've passed today's slots
            scheduled_time = now + timedelta(days=1)
            scheduled_time = scheduled_time.replace(hour=optimal_hours[0], minute=0)
        else:
            scheduled_time = now.replace(hour=next_slot, minute=0)
            
        return scheduled_time.isoformat()

    def create_reel(self):
        """Create a luxury home staging reel"""
        reel_content = {
            'type': 'reel',
            'scenes': self._generate_reel_scenes(),
            'music': self._select_background_music(),
            'transitions': self._generate_transitions(),
            'status': 'pending_review'
        }
        
        work_file = self.save_work(reel_content, 'reel')
        self.log_activity('reel_creation', 'completed', {'file': str(work_file)})
        return work_file
        
    def _generate_reel_scenes(self):
        """Generate scene sequence for reels"""
        scenes = [
            {
                'duration': 3,
                'type': 'opening',
                'text': "Luxury Home Staging by Design Gaga",
                'effect': 'fade_in'
            },
            {
                'duration': 4,
                'type': 'showcase',
                'text': "Transform Your Space",
                'effect': 'pan_right'
            }
        ]
        return scenes
        
    def _select_background_music(self):
        """Select appropriate background music"""
        music_options = [
            {
                'title': 'Elegant Luxury',
                'duration': 30,
                'genre': 'ambient',
                'license': 'royalty_free'
            }
        ]
        return random.choice(music_options)
        
    def _generate_transitions(self):
        """Generate smooth transitions between scenes"""
        transitions = ['fade', 'dissolve', 'slide_left', 'slide_right']
        return random.sample(transitions, 3)
