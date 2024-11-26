import uuid
import asyncio
import logging
from typing import Dict, Any
from app.core.config import settings
from app.agents.website_analyzer import WebsiteAnalyzer
from app.agents.business_optimizer import BusinessOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self.sessions = {}
        self.website_analyzer = WebsiteAnalyzer()
        self.business_optimizer = BusinessOptimizer()
        self.logger = logging.getLogger(__name__)

    async def create_session(self, business_data: Dict[str, Any]) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "business_data": business_data,
            "analysis_results": None,
            "recommendations": None,
            "status": "pending",
            "progress": []
        }
        self.logger.info(f"Created new session {session_id} for business: {business_data['business_name']}")
        return session_id

    async def start_analysis(self, session_id: str):
        if session_id not in self.sessions:
            raise ValueError("Invalid session ID")

        # Start analysis in background
        asyncio.create_task(self._run_analysis(session_id))

    async def _run_analysis(self, session_id: str):
        try:
            session = self.sessions[session_id]
            business_data = session["business_data"]
            
            # Update status
            session["status"] = "analyzing"
            self.logger.info(f"Starting analysis for session {session_id}")
            session["progress"].append("Started website analysis")
            
            # Analyze website
            self.logger.info(f"Analyzing website: {business_data['website']}")
            website_analysis = await self.website_analyzer.analyze(business_data["website"])
            session["analysis_results"] = website_analysis
            session["progress"].append("Completed website analysis")
            
            if website_analysis.get("error"):
                self.logger.error(f"Website analysis failed: {website_analysis['error']}")
                session["status"] = "failed"
                session["error"] = website_analysis["error"]
                return
            
            # Generate recommendations
            self.logger.info("Generating business recommendations")
            session["progress"].append("Started generating recommendations")
            recommendations = await self.business_optimizer.generate_recommendations(
                website_analysis,
                business_data
            )
            session["recommendations"] = recommendations
            session["progress"].append("Completed generating recommendations")
            
            # Update status
            session["status"] = "completed"
            self.logger.info(f"Analysis completed for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            self.sessions[session_id]["status"] = "failed"
            self.sessions[session_id]["error"] = str(e)
            self.sessions[session_id]["progress"].append(f"Error: {str(e)}")

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise ValueError("Invalid session ID")
            
        session = self.sessions[session_id]
        return {
            "status": session["status"],
            "progress": session["progress"],
            "recommendations": session["recommendations"] if session["status"] == "completed" else None,
            "error": session.get("error"),
            "analysis_results": session.get("analysis_results")
        }
