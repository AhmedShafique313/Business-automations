import random
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import numpy as np

class PropertyMetricsGenerator:
    def __init__(self):
        # Initialize with realistic ranges for different property types
        self.property_ranges = {
            "residential": {
                "price_range": (500000, 3000000),  # Price range for SF
                "rent_range": (2500, 15000),       # Monthly rent range
                "sqft_range": (600, 4000),         # Square footage range
                "cap_rate_range": (0.03, 0.06),    # Typical residential cap rates
                "appreciation_range": (0.03, 0.12), # Annual appreciation range
                "expense_ratio_range": (0.35, 0.45) # Operating expense ratio
            },
            "commercial": {
                "price_range": (1000000, 10000000),
                "rent_range": (5000, 50000),
                "sqft_range": (1000, 10000),
                "cap_rate_range": (0.05, 0.08),
                "appreciation_range": (0.02, 0.08),
                "expense_ratio_range": (0.30, 0.40)
            }
        }
        
        # Market trend factors
        self.market_trends = {
            "hot": {
                "price_multiplier": 1.2,
                "rent_multiplier": 1.15,
                "cap_rate_adjustment": -0.005,  # Lower cap rates in hot markets
                "appreciation_boost": 0.02
            },
            "neutral": {
                "price_multiplier": 1.0,
                "rent_multiplier": 1.0,
                "cap_rate_adjustment": 0,
                "appreciation_boost": 0
            },
            "cool": {
                "price_multiplier": 0.9,
                "rent_multiplier": 0.95,
                "cap_rate_adjustment": 0.01,   # Higher cap rates in cool markets
                "appreciation_boost": -0.01
            }
        }
        
        # Location factors for San Francisco neighborhoods
        self.location_factors = {
            "Pacific Heights": {"multiplier": 1.4, "trend": "hot"},
            "Mission District": {"multiplier": 1.2, "trend": "hot"},
            "SOMA": {"multiplier": 1.3, "trend": "neutral"},
            "Richmond District": {"multiplier": 1.1, "trend": "neutral"},
            "Sunset District": {"multiplier": 1.0, "trend": "cool"},
            "Bayview": {"multiplier": 0.8, "trend": "hot"}  # Up and coming
        }

    def generate_metrics(self, 
                        property_type: str = "residential",
                        location: str = "Mission District",
                        bedrooms: int = 3,
                        include_history: bool = False) -> Dict:
        """
        Generate realistic property metrics based on type, location, and market conditions
        
        Args:
            property_type: Type of property (residential or commercial)
            location: Neighborhood in San Francisco
            bedrooms: Number of bedrooms (for residential)
            include_history: Whether to include historical data
            
        Returns:
            Dict containing property metrics
        """
        ranges = self.property_ranges[property_type]
        location_factor = self.location_factors[location]
        market_trend = self.market_trends[location_factor["trend"]]
        
        # Base calculations
        base_price = random.uniform(*ranges["price_range"])
        base_rent = random.uniform(*ranges["rent_range"])
        
        # Apply location and market factors
        price = base_price * location_factor["multiplier"] * market_trend["price_multiplier"]
        monthly_rent = base_rent * location_factor["multiplier"] * market_trend["rent_multiplier"]
        
        # Calculate operating expenses (property tax, insurance, maintenance, etc.)
        expense_ratio = random.uniform(*ranges["expense_ratio_range"])
        annual_expenses = price * expense_ratio
        monthly_expenses = annual_expenses / 12
        
        # Calculate cash flow
        monthly_cash_flow = monthly_rent - monthly_expenses
        
        # Calculate cap rate (NOI / Property Value)
        noi = (monthly_rent * 12) - annual_expenses
        cap_rate = (noi / price) + market_trend["cap_rate_adjustment"]
        
        # Calculate appreciation
        base_appreciation = random.uniform(*ranges["appreciation_range"])
        appreciation = base_appreciation + market_trend["appreciation_boost"]
        
        # Generate price history if requested
        price_history = None
        if include_history:
            price_history = self._generate_price_history(price, appreciation)
        
        # Market analysis based on metrics
        market_analysis = self._generate_market_analysis(
            cap_rate, appreciation, monthly_cash_flow, location_factor["trend"]
        )
        
        return {
            "metrics": {
                "price": round(price, 2),
                "price_per_sqft": round(price / random.uniform(*ranges["sqft_range"]), 2),
                "monthly_rent": round(monthly_rent, 2),
                "monthly_expenses": round(monthly_expenses, 2),
                "monthly_cash_flow": round(monthly_cash_flow, 2),
                "cap_rate": round(cap_rate * 100, 2),  # Convert to percentage
                "appreciation": round(appreciation * 100, 2),  # Convert to percentage
                "roi": round(((monthly_cash_flow * 12) / price) * 100, 2),  # Annual ROI as percentage
                "expense_ratio": round(expense_ratio * 100, 2)
            },
            "market_analysis": market_analysis,
            "price_history": price_history,
            "location_data": {
                "neighborhood": location,
                "market_trend": location_factor["trend"],
                "neighborhood_multiplier": location_factor["multiplier"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_price_history(self, current_price: float, appreciation_rate: float) -> Dict:
        """Generate 5-year price history based on appreciation rate"""
        history = {}
        price = current_price
        
        for year in range(5):
            # Add some randomness to historical appreciation
            historical_rate = appreciation_rate * random.uniform(0.8, 1.2)
            price = price / (1 + historical_rate)  # Work backwards
            history[str(datetime.now().year - (year + 1))] = round(price, 2)
        
        return history
    
    def _generate_market_analysis(self, 
                                cap_rate: float,
                                appreciation: float,
                                cash_flow: float,
                                trend: str) -> str:
        """Generate market analysis based on metrics"""
        analysis = []
        
        # Cap rate analysis
        if cap_rate > 0.06:
            analysis.append("Strong cash flow potential with above-average cap rate")
        elif cap_rate > 0.04:
            analysis.append("Solid cap rate indicating good rental income potential")
        else:
            analysis.append("Cap rate suggests focus on appreciation over cash flow")
        
        # Appreciation analysis
        if appreciation > 0.08:
            analysis.append("High appreciation potential in rapidly growing area")
        elif appreciation > 0.05:
            analysis.append("Steady appreciation expected based on market trends")
        else:
            analysis.append("Conservative appreciation projections")
        
        # Cash flow analysis
        if cash_flow > 5000:
            analysis.append("Excellent monthly cash flow")
        elif cash_flow > 2000:
            analysis.append("Good positive cash flow")
        elif cash_flow > 0:
            analysis.append("Positive cash flow with room for optimization")
        else:
            analysis.append("May require additional investment to improve cash flow")
        
        # Market trend analysis
        trend_analysis = {
            "hot": "High demand market with potential for strong returns",
            "neutral": "Stable market conditions with balanced growth potential",
            "cool": "Value opportunity in developing market"
        }
        analysis.append(trend_analysis[trend])
        
        return " | ".join(analysis)


# Example usage
if __name__ == "__main__":
    generator = PropertyMetricsGenerator()
    
    # Generate metrics for a residential property
    metrics = generator.generate_metrics(
        property_type="residential",
        location="Mission District",
        bedrooms=3,
        include_history=True
    )
    
    print(json.dumps(metrics, indent=2))
