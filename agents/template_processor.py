import json
import random
from typing import Dict, List, Optional, Union
import os

class TemplateProcessor:
    def __init__(self, templates_dir: str = "../templates"):
        self.templates_dir = templates_dir
        self.sequences = self._load_sequences()
        self.personalized_sequences = self._load_personalized_sequences()
    
    def _load_sequences(self) -> Dict:
        """Load standard email sequences"""
        with open(os.path.join(self.templates_dir, "email_sequences.json"), "r") as f:
            return json.load(f)
    
    def _load_personalized_sequences(self) -> Dict:
        """Load personalized email sequences"""
        with open(os.path.join(self.templates_dir, "personalized_sequences.json"), "r") as f:
            return json.load(f)
    
    def get_matching_sequence(self, psychological_profile: Dict) -> Optional[Dict]:
        """
        Find the best matching sequence based on psychological profile
        
        Args:
            psychological_profile: Dict containing personality traits, communication preferences, and interests
        
        Returns:
            Best matching sequence or None if no good match found
        """
        best_match = None
        best_score = 0
        
        for sequence_type, sequence in self.personalized_sequences.items():
            score = self._calculate_profile_match_score(
                psychological_profile,
                sequence["profile_match"]
            )
            
            if score > best_score:
                best_score = score
                best_match = sequence
        
        # Require at least 30% match
        return best_match if best_score >= 0.3 else None
    
    def _calculate_profile_match_score(self, user_profile: Dict, sequence_profile: Dict) -> float:
        """Calculate how well a user's profile matches a sequence profile"""
        total_points = 0
        earned_points = 0
        
        # Check personality traits
        if "personality_traits" in user_profile and "personality_traits" in sequence_profile:
            user_traits = set(user_profile["personality_traits"])
            sequence_traits = set(sequence_profile["personality_traits"])
            total_points += len(sequence_traits)
            earned_points += len(user_traits.intersection(sequence_traits))
        
        # Check communication preferences
        if "communication_preferences" in user_profile and "communication_preferences" in sequence_profile:
            user_prefs = set(user_profile["communication_preferences"])
            sequence_prefs = set(sequence_profile["communication_preferences"])
            total_points += len(sequence_prefs)
            earned_points += len(user_prefs.intersection(sequence_prefs))
        
        # Check interests
        if "interests" in user_profile and "interests" in sequence_profile:
            user_interests = set(user_profile["interests"])
            sequence_interests = set(sequence_profile["interests"])
            total_points += len(sequence_interests)
            earned_points += len(user_interests.intersection(sequence_interests))
        
        return earned_points / total_points if total_points > 0 else 0
    
    def process_template(self, template: Dict, context: Dict) -> Dict:
        """
        Process a template with given context variables
        
        Args:
            template: Dict containing email template with variants
            context: Dict containing values for template variables
        
        Returns:
            Dict with processed subject and content
        """
        # Select random variants
        subject_variant = random.choice(template["subject"]["variants"])
        content_variant = random.choice(template["content"]["variants"])
        
        # Replace variables in subject and content
        processed_subject = self._replace_variables(subject_variant, context)
        processed_content = self._replace_variables(content_variant, context)
        
        return {
            "subject": processed_subject,
            "content": processed_content
        }
    
    def _replace_variables(self, text: str, context: Dict) -> str:
        """Replace template variables with actual values"""
        for key, value in context.items():
            placeholder = "{{" + key + "}}"
            text = text.replace(placeholder, str(value))
        return text
    
    def generate_email(self, 
                      psychological_profile: Dict,
                      context: Dict,
                      sequence_type: Optional[str] = None) -> Optional[Dict]:
        """
        Generate a personalized email based on psychological profile and context
        
        Args:
            psychological_profile: Dict containing personality traits and preferences
            context: Dict containing values for template variables
            sequence_type: Optional specific sequence type to use
        
        Returns:
            Dict containing processed email subject and content, or None if no matching sequence
        """
        if sequence_type:
            if sequence_type in self.personalized_sequences:
                sequence = self.personalized_sequences[sequence_type]
            elif sequence_type in self.sequences:
                sequence = self.sequences[sequence_type]
            else:
                return None
        else:
            sequence = self.get_matching_sequence(psychological_profile)
            if not sequence:
                # Fallback to default welcome sequence
                sequence = self.sequences.get("welcome_sequence")
        
        if not sequence:
            return None
        
        # Get first step of sequence (can be extended to handle multiple steps)
        template = sequence["steps"][0]
        
        return self.process_template(template, context)


# Example usage:
if __name__ == "__main__":
    processor = TemplateProcessor()
    
    # Example psychological profile
    profile = {
        "personality_traits": ["analytical", "detail-oriented"],
        "communication_preferences": ["formal", "data-driven"],
        "interests": ["investment analysis", "market research"]
    }
    
    # Example context variables
    context = {
        "name": "John Smith",
        "location": "San Francisco",
        "roi": "12.5",
        "price_sqft": "850",
        "yoy_growth": "8.2",
        "investment_analysis": "Property shows strong potential with consistent growth"
    }
    
    # Generate personalized email
    email = processor.generate_email(profile, context)
    
    if email:
        print("Subject:", email["subject"])
        print("\nContent:", email["content"])
    else:
        print("No matching sequence found")
