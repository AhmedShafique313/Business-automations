from template_processor import TemplateProcessor
from property_metrics_generator import PropertyMetricsGenerator
from typing import Dict, Optional
import json

class DynamicTemplateProcessor:
    def __init__(self):
        self.template_processor = TemplateProcessor()
        self.metrics_generator = PropertyMetricsGenerator()
    
    def generate_email(self,
                      psychological_profile: Dict,
                      property_details: Dict,
                      sequence_type: Optional[str] = None) -> Optional[Dict]:
        """
        Generate a personalized email with dynamic property metrics
        
        Args:
            psychological_profile: Dict containing personality traits and preferences
            property_details: Dict containing property type, location, etc.
            sequence_type: Optional specific sequence type to use
        
        Returns:
            Dict containing processed email subject and content
        """
        # Generate property metrics
        metrics = self.metrics_generator.generate_metrics(
            property_type=property_details.get("type", "residential"),
            location=property_details.get("location", "Mission District"),
            bedrooms=property_details.get("bedrooms", 3),
            include_history=True
        )
        
        # Create context with all necessary variables
        context = {
            "name": property_details.get("recipient_name", "Valued Investor"),
            "location": property_details["location"],
            "property_type": property_details.get("type", "residential"),
            "cap_rate": str(metrics["metrics"]["cap_rate"]),
            "cash_flow": str(metrics["metrics"]["monthly_cash_flow"]),
            "appreciation": str(metrics["metrics"]["appreciation"]),
            "roi": str(metrics["metrics"]["roi"]),
            "price_sqft": str(metrics["metrics"]["price_per_sqft"]),
            "yoy_growth": str(metrics["metrics"]["appreciation"]),
            "investment_analysis": metrics["market_analysis"],
            "market_trends": metrics["market_analysis"],
            "price": f"${metrics['metrics']['price']:,.2f}",
            "monthly_rent": f"${metrics['metrics']['monthly_rent']:,.2f}",
            "property_details": (
                f"{property_details.get('bedrooms', 3)} bed, "
                f"{property_details.get('bathrooms', 2)} bath, "
                f"in {property_details['location']}"
            )
        }
        
        # Generate email using template processor
        return self.template_processor.generate_email(
            psychological_profile=psychological_profile,
            context=context,
            sequence_type=sequence_type
        )


# Example usage
if __name__ == "__main__":
    processor = DynamicTemplateProcessor()
    
    # Example psychological profile (analytical investor)
    profile = {
        "personality_traits": ["analytical", "detail-oriented"],
        "communication_preferences": ["formal", "data-driven"],
        "interests": ["investment analysis", "market research"]
    }
    
    # Example property details
    property_details = {
        "type": "residential",
        "location": "Mission District",
        "bedrooms": 3,
        "bathrooms": 2,
        "recipient_name": "John Smith"
    }
    
    # Generate personalized email with dynamic metrics
    email = processor.generate_email(profile, property_details)
    
    if email:
        print("Subject:", email["subject"])
        print("\nContent:", email["content"])
