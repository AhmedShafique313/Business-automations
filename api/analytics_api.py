"""API endpoints for email marketing analytics."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsAPI:
    """Analytics API endpoints."""
    
    def __init__(self, db_path: str = "contacts.db"):
        """Initialize with database path."""
        self.db_path = db_path
    
    async def get_overview_stats(self) -> Dict:
        """Get overview statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get total contacts
            cursor.execute("SELECT COUNT(*) FROM contacts")
            total_contacts = cursor.fetchone()[0]
            
            # Get contact growth (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor.execute(
                "SELECT COUNT(*) FROM contacts WHERE created_at >= ?",
                (thirty_days_ago,)
            )
            new_contacts = cursor.fetchone()[0]
            
            # Calculate growth percentage
            growth_percentage = (
                (new_contacts / total_contacts * 100)
                if total_contacts > 0 else 0
            )
            
            # Get email statistics
            cursor.execute("""
                SELECT 
                    interaction_type,
                    COUNT(*) as count
                FROM email_interactions
                WHERE timestamp >= ?
                GROUP BY interaction_type
            """, (thirty_days_ago,))
            
            interactions = {}
            total_emails = 0
            for row in cursor.fetchall():
                interaction_type, count = row
                interactions[interaction_type] = count
                if interaction_type == 'sent':
                    total_emails = count
            
            # Calculate rates
            open_rate = (
                interactions.get('opened', 0) / total_emails * 100
                if total_emails > 0 else 0
            )
            click_rate = (
                interactions.get('clicked', 0) / total_emails * 100
                if total_emails > 0 else 0
            )
            
            # Get active sequences
            cursor.execute(
                "SELECT COUNT(DISTINCT sequence_id) FROM sequence_tracking WHERE status = 'active'"
            )
            active_sequences = cursor.fetchone()[0]
            
            return {
                "totalContacts": total_contacts,
                "contactGrowth": round(growth_percentage, 1),
                "openRate": round(open_rate, 1),
                "clickRate": round(click_rate, 1),
                "activeSequences": active_sequences
            }
    
    async def get_engagement_data(self) -> Dict:
        """Get engagement data over time."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get last 6 months of data
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', timestamp) as month,
                    interaction_type,
                    COUNT(*) as count
                FROM email_interactions
                WHERE timestamp >= date('now', '-6 months')
                GROUP BY month, interaction_type
                ORDER BY month
            """)
            
            months = []
            open_rates = []
            click_rates = []
            
            current_month = ""
            month_data = {"sent": 0, "opened": 0, "clicked": 0}
            
            for row in cursor.fetchall():
                month, interaction_type, count = row
                
                if month != current_month and current_month:
                    # Calculate rates for previous month
                    if month_data["sent"] > 0:
                        months.append(current_month)
                        open_rates.append(
                            round(month_data["opened"] / month_data["sent"] * 100, 1)
                        )
                        click_rates.append(
                            round(month_data["clicked"] / month_data["sent"] * 100, 1)
                        )
                    month_data = {"sent": 0, "opened": 0, "clicked": 0}
                
                current_month = month
                month_data[interaction_type] = count
            
            # Add last month
            if month_data["sent"] > 0:
                months.append(current_month)
                open_rates.append(
                    round(month_data["opened"] / month_data["sent"] * 100, 1)
                )
                click_rates.append(
                    round(month_data["clicked"] / month_data["sent"] * 100, 1)
                )
            
            return {
                "labels": months,
                "datasets": [
                    {
                        "label": "Open Rate",
                        "data": open_rates,
                        "borderColor": "rgb(75, 192, 192)",
                        "tension": 0.1
                    },
                    {
                        "label": "Click Rate",
                        "data": click_rates,
                        "borderColor": "rgb(255, 99, 132)",
                        "tension": 0.1
                    }
                ]
            }
    
    async def get_sequence_performance(self) -> Dict:
        """Get sequence performance data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sequence_id,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM sequence_tracking
                GROUP BY sequence_id
            """)
            
            labels = []
            completion_rates = []
            
            for row in cursor.fetchall():
                sequence_id, total, completed = row
                labels.append(sequence_id)
                completion_rate = round(completed / total * 100, 1) if total > 0 else 0
                completion_rates.append(completion_rate)
            
            return {
                "labels": labels,
                "datasets": [{
                    "label": "Completion Rate",
                    "data": completion_rates,
                    "backgroundColor": [
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(153, 102, 255, 0.2)'
                    ],
                    "borderColor": [
                        'rgb(75, 192, 192)',
                        'rgb(255, 99, 132)',
                        'rgb(255, 206, 86)',
                        'rgb(153, 102, 255)'
                    ],
                    "borderWidth": 1
                }]
            }
    
    async def get_ab_test_results(self) -> List[Dict]:
        """Get A/B test results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    test_id,
                    variant,
                    result,
                    COUNT(*) as count
                FROM ab_test_results
                GROUP BY test_id, variant, result
            """)
            
            results = {}
            for row in cursor.fetchall():
                test_id, variant, result, count = row
                
                if test_id not in results:
                    results[test_id] = {
                        "id": test_id,
                        "variantA": 0,
                        "variantB": 0,
                        "winner": "",
                        "improvement": 0
                    }
                
                if result == "success":
                    if variant == "A":
                        results[test_id]["variantA"] = count
                    else:
                        results[test_id]["variantB"] = count
            
            # Calculate winners and improvements
            for test_id, data in results.items():
                if data["variantA"] > data["variantB"]:
                    data["winner"] = "A"
                    data["improvement"] = round(
                        (data["variantA"] - data["variantB"]) / data["variantB"] * 100
                        if data["variantB"] > 0 else 0,
                        1
                    )
                else:
                    data["winner"] = "B"
                    data["improvement"] = round(
                        (data["variantB"] - data["variantA"]) / data["variantA"] * 100
                        if data["variantA"] > 0 else 0,
                        1
                    )
            
            return list(results.values())

# Initialize API
analytics_api = AnalyticsAPI()

@app.get("/api/analytics/overview")
async def get_overview():
    """Get overview statistics."""
    try:
        return await analytics_api.get_overview_stats()
    except Exception as e:
        logger.error(f"Error getting overview stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analytics/engagement")
async def get_engagement():
    """Get engagement data."""
    try:
        return await analytics_api.get_engagement_data()
    except Exception as e:
        logger.error(f"Error getting engagement data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analytics/sequences")
async def get_sequences():
    """Get sequence performance data."""
    try:
        return await analytics_api.get_sequence_performance()
    except Exception as e:
        logger.error(f"Error getting sequence performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/analytics/ab-tests")
async def get_ab_tests():
    """Get A/B test results."""
    try:
        return await analytics_api.get_ab_test_results()
    except Exception as e:
        logger.error(f"Error getting A/B test results: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
