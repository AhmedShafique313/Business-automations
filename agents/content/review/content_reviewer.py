"""
Content Reviewer
Handles content review and approval workflows.
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime
import asyncio
from enum import Enum

class ReviewStatus(Enum):
    """Content review status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

class ContentReviewer:
    """Manages content review workflows."""
    
    def __init__(self, work_dir: Path):
        """Initialize content reviewer."""
        self.work_dir = Path(work_dir)
        self.reviews_dir = self.work_dir / 'reviews'
        self.reviews_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('ContentReviewer')
        
        # Load review criteria
        self.criteria = self._load_review_criteria()
    
    def _load_review_criteria(self) -> Dict:
        """Load review criteria for different content types."""
        try:
            criteria_file = self.work_dir / 'review_criteria.json'
            if not criteria_file.exists():
                return self._create_default_criteria()
            
            with open(criteria_file) as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load review criteria: {str(e)}")
            return self._create_default_criteria()
    
    def _create_default_criteria(self) -> Dict:
        """Create default review criteria."""
        criteria = {
            "blog_post": {
                "quality": {
                    "grammar": {"weight": 0.3, "threshold": 0.8},
                    "readability": {"weight": 0.3, "threshold": 0.7},
                    "originality": {"weight": 0.4, "threshold": 0.6}
                },
                "seo": {
                    "keyword_density": {"weight": 0.3, "threshold": 0.02},
                    "meta_description": {"weight": 0.3, "threshold": 0.9},
                    "heading_structure": {"weight": 0.4, "threshold": 0.8}
                },
                "compliance": {
                    "plagiarism": {"weight": 0.4, "threshold": 0.1},
                    "brand_guidelines": {"weight": 0.3, "threshold": 0.9},
                    "legal_requirements": {"weight": 0.3, "threshold": 1.0}
                }
            },
            "social_post": {
                "quality": {
                    "grammar": {"weight": 0.3, "threshold": 0.8},
                    "engagement_potential": {"weight": 0.4, "threshold": 0.7},
                    "hashtag_relevance": {"weight": 0.3, "threshold": 0.6}
                },
                "compliance": {
                    "brand_voice": {"weight": 0.4, "threshold": 0.8},
                    "platform_guidelines": {"weight": 0.3, "threshold": 1.0},
                    "sensitive_content": {"weight": 0.3, "threshold": 0.9}
                }
            },
            "email_campaign": {
                "quality": {
                    "subject_line": {"weight": 0.4, "threshold": 0.8},
                    "content_quality": {"weight": 0.3, "threshold": 0.7},
                    "call_to_action": {"weight": 0.3, "threshold": 0.8}
                },
                "compliance": {
                    "spam_score": {"weight": 0.4, "threshold": 0.1},
                    "gdpr_compliance": {"weight": 0.3, "threshold": 1.0},
                    "unsubscribe_mechanism": {"weight": 0.3, "threshold": 1.0}
                }
            }
        }
        
        # Save criteria
        criteria_file = self.work_dir / 'review_criteria.json'
        with open(criteria_file, 'w') as f:
            json.dump(criteria, f, indent=2)
        
        return criteria
    
    async def submit_for_review(self, content: Dict) -> Dict:
        """Submit content for review."""
        try:
            content_type = content.get('type')
            if content_type not in self.criteria:
                raise ValueError(f"No review criteria found for type: {content_type}")
            
            # Create review record
            review = {
                'content_id': content.get('id'),
                'content_type': content_type,
                'status': ReviewStatus.PENDING.value,
                'submitted_at': datetime.now().isoformat(),
                'reviews': [],
                'current_version': 1,
                'content': content
            }
            
            # Save review
            review_file = self.reviews_dir / f"{review['content_id']}_v{review['current_version']}.json"
            with open(review_file, 'w') as f:
                json.dump(review, f, indent=2)
            
            self.logger.info(f"Content submitted for review: {review['content_id']}")
            return review
            
        except Exception as e:
            self.logger.error(f"Failed to submit content for review: {str(e)}")
            raise
    
    async def review_content(self, content_id: str) -> Dict:
        """Review content against criteria."""
        try:
            # Load review record
            review_file = next(self.reviews_dir.glob(f"{content_id}_v*.json"))
            with open(review_file) as f:
                review = json.load(f)
            
            content_type = review['content_type']
            content = review['content']
            
            # Update status
            review['status'] = ReviewStatus.IN_REVIEW.value
            
            # Perform reviews
            quality_review = await self._review_quality(content, content_type)
            compliance_review = await self._review_compliance(content, content_type)
            
            # Combine reviews
            review_result = {
                'reviewer_id': 'system',
                'timestamp': datetime.now().isoformat(),
                'quality': quality_review,
                'compliance': compliance_review,
                'comments': [],
                'overall_score': (quality_review['score'] + compliance_review['score']) / 2
            }
            
            # Update review record
            review['reviews'].append(review_result)
            review['status'] = (
                ReviewStatus.APPROVED.value
                if review_result['overall_score'] >= 0.7
                else ReviewStatus.NEEDS_REVISION.value
            )
            
            # Save updated review
            with open(review_file, 'w') as f:
                json.dump(review, f, indent=2)
            
            self.logger.info(f"Content review completed: {content_id}")
            return review
            
        except Exception as e:
            self.logger.error(f"Failed to review content: {str(e)}")
            raise
    
    async def _review_quality(self, content: Dict, content_type: str) -> Dict:
        """Review content quality."""
        try:
            criteria = self.criteria[content_type]['quality']
            scores = {}
            
            # Common quality checks
            quality_checks = {
                'grammar': self._check_grammar,
                'readability': self._check_readability,
                'originality': self._check_originality,
                'engagement_potential': self._check_engagement,
                'technical_accuracy': self._check_technical_accuracy,
                'research_depth': self._check_research_depth
            }
            
            # Perform relevant quality checks
            for aspect, config in criteria.items():
                check_func = quality_checks.get(aspect)
                if check_func:
                    score = await check_func(content)
                else:
                    # Default to a basic text analysis if no specific check is available
                    score = await self._basic_text_analysis(content)
                
                scores[aspect] = {
                    'score': score,
                    'weight': config['weight'],
                    'threshold': config['threshold'],
                    'passed': score >= config['threshold']
                }
            
            overall_score = sum(
                score['score'] * score['weight']
                for score in scores.values()
            )
            
            return {
                'scores': scores,
                'score': overall_score,
                'passed': all(score['passed'] for score in scores.values())
            }
            
        except Exception as e:
            self.logger.error(f"Quality review failed: {str(e)}")
            raise
    
    async def _review_compliance(self, content: Dict, content_type: str) -> Dict:
        """Review content compliance."""
        try:
            criteria = self.criteria[content_type]['compliance']
            scores = {}
            
            # Common compliance checks
            compliance_checks = {
                'plagiarism': self._check_plagiarism,
                'brand_guidelines': self._check_brand_compliance,
                'legal_requirements': self._check_legal_compliance,
                'platform_guidelines': self._check_platform_compliance,
                'gdpr_compliance': self._check_gdpr_compliance,
                'copyright_clearance': self._check_copyright,
                'data_privacy': self._check_data_privacy
            }
            
            # Perform relevant compliance checks
            for aspect, config in criteria.items():
                check_func = compliance_checks.get(aspect)
                if check_func:
                    score = await check_func(content)
                else:
                    # Default to a basic compliance check if no specific check is available
                    score = await self._basic_compliance_check(content)
                
                scores[aspect] = {
                    'score': score,
                    'weight': config['weight'],
                    'threshold': config['threshold'],
                    'passed': score >= config['threshold']
                }
            
            overall_score = sum(
                score['score'] * score['weight']
                for score in scores.values()
            )
            
            return {
                'scores': scores,
                'score': overall_score,
                'passed': all(score['passed'] for score in scores.values())
            }
            
        except Exception as e:
            self.logger.error(f"Compliance review failed: {str(e)}")
            raise
    
    async def _check_grammar(self, content: Dict) -> float:
        """Check grammar and language quality."""
        try:
            # TODO: Integrate with a grammar checking service
            # For now, return a placeholder score
            return 0.85
        except Exception as e:
            self.logger.error(f"Grammar check failed: {str(e)}")
            return 0.0
    
    async def _check_readability(self, content: Dict) -> float:
        """Check content readability."""
        try:
            # TODO: Implement readability metrics (Flesch-Kincaid, etc.)
            # For now, return a placeholder score
            return 0.8
        except Exception as e:
            self.logger.error(f"Readability check failed: {str(e)}")
            return 0.0
    
    async def _check_originality(self, content: Dict) -> float:
        """Check content originality."""
        try:
            # TODO: Implement plagiarism detection
            # For now, return a placeholder score
            return 0.9
        except Exception as e:
            self.logger.error(f"Originality check failed: {str(e)}")
            return 0.0
    
    async def _check_engagement(self, content: Dict) -> float:
        """Check content engagement potential."""
        try:
            # TODO: Implement engagement metrics
            # For now, return a placeholder score
            return 0.75
        except Exception as e:
            self.logger.error(f"Engagement check failed: {str(e)}")
            return 0.0
    
    async def _check_technical_accuracy(self, content: Dict) -> float:
        """Check technical accuracy of content."""
        try:
            # TODO: Implement technical verification
            # For now, return a placeholder score
            return 0.9
        except Exception as e:
            self.logger.error(f"Technical accuracy check failed: {str(e)}")
            return 0.0
    
    async def _check_research_depth(self, content: Dict) -> float:
        """Check research depth and citation quality."""
        try:
            # TODO: Implement research quality metrics
            # For now, return a placeholder score
            return 0.85
        except Exception as e:
            self.logger.error(f"Research depth check failed: {str(e)}")
            return 0.0
    
    async def _check_plagiarism(self, content: Dict) -> float:
        """Check for plagiarism."""
        try:
            # TODO: Integrate with plagiarism detection service
            # For now, return a placeholder score
            return 0.95
        except Exception as e:
            self.logger.error(f"Plagiarism check failed: {str(e)}")
            return 0.0
    
    async def _check_brand_compliance(self, content: Dict) -> float:
        """Check compliance with brand guidelines."""
        try:
            # TODO: Implement brand guideline checks
            # For now, return a placeholder score
            return 0.9
        except Exception as e:
            self.logger.error(f"Brand compliance check failed: {str(e)}")
            return 0.0
    
    async def _check_legal_compliance(self, content: Dict) -> float:
        """Check legal compliance."""
        try:
            # TODO: Implement legal requirement checks
            # For now, return a placeholder score
            return 1.0
        except Exception as e:
            self.logger.error(f"Legal compliance check failed: {str(e)}")
            return 0.0
    
    async def _check_platform_compliance(self, content: Dict) -> float:
        """Check platform-specific guideline compliance."""
        try:
            # TODO: Implement platform guideline checks
            # For now, return a placeholder score
            return 0.95
        except Exception as e:
            self.logger.error(f"Platform compliance check failed: {str(e)}")
            return 0.0
    
    async def _check_gdpr_compliance(self, content: Dict) -> float:
        """Check GDPR compliance."""
        try:
            # TODO: Implement GDPR compliance checks
            # For now, return a placeholder score
            return 1.0
        except Exception as e:
            self.logger.error(f"GDPR compliance check failed: {str(e)}")
            return 0.0
    
    async def _check_copyright(self, content: Dict) -> float:
        """Check copyright compliance."""
        try:
            # TODO: Implement copyright checks
            # For now, return a placeholder score
            return 1.0
        except Exception as e:
            self.logger.error(f"Copyright check failed: {str(e)}")
            return 0.0
    
    async def _check_data_privacy(self, content: Dict) -> float:
        """Check data privacy compliance."""
        try:
            # TODO: Implement data privacy checks
            # For now, return a placeholder score
            return 1.0
        except Exception as e:
            self.logger.error(f"Data privacy check failed: {str(e)}")
            return 0.0
    
    async def _basic_text_analysis(self, content: Dict) -> float:
        """Perform basic text analysis when no specific check is available."""
        try:
            # TODO: Implement basic text analysis
            # For now, return a placeholder score
            return 0.8
        except Exception as e:
            self.logger.error(f"Basic text analysis failed: {str(e)}")
            return 0.0
    
    async def _basic_compliance_check(self, content: Dict) -> float:
        """Perform basic compliance check when no specific check is available."""
        try:
            # TODO: Implement basic compliance check
            # For now, return a placeholder score
            return 0.9
        except Exception as e:
            self.logger.error(f"Basic compliance check failed: {str(e)}")
            return 0.0
    
    async def approve_content(self, content_id: str, reviewer_id: str, comments: str = "") -> Dict:
        """Approve content for distribution."""
        try:
            # Load review record
            review_file = next(self.reviews_dir.glob(f"{content_id}_v*.json"))
            with open(review_file) as f:
                review = json.load(f)
            
            if review['status'] not in [ReviewStatus.IN_REVIEW.value, ReviewStatus.NEEDS_REVISION.value]:
                raise ValueError(f"Content not ready for approval: {review['status']}")
            
            # Update review
            review['status'] = ReviewStatus.APPROVED.value
            review['approved_by'] = reviewer_id
            review['approved_at'] = datetime.now().isoformat()
            if comments:
                review['approval_comments'] = comments
            
            # Save updated review
            with open(review_file, 'w') as f:
                json.dump(review, f, indent=2)
            
            self.logger.info(f"Content approved: {content_id}")
            return review
            
        except Exception as e:
            self.logger.error(f"Failed to approve content: {str(e)}")
            raise
    
    async def reject_content(self, content_id: str, reviewer_id: str, reason: str) -> Dict:
        """Reject content."""
        try:
            # Load review record
            review_file = next(self.reviews_dir.glob(f"{content_id}_v*.json"))
            with open(review_file) as f:
                review = json.load(f)
            
            if review['status'] not in [ReviewStatus.IN_REVIEW.value, ReviewStatus.NEEDS_REVISION.value]:
                raise ValueError(f"Content not ready for rejection: {review['status']}")
            
            # Update review
            review['status'] = ReviewStatus.REJECTED.value
            review['rejected_by'] = reviewer_id
            review['rejected_at'] = datetime.now().isoformat()
            review['rejection_reason'] = reason
            
            # Save updated review
            with open(review_file, 'w') as f:
                json.dump(review, f, indent=2)
            
            self.logger.info(f"Content rejected: {content_id}")
            return review
            
        except Exception as e:
            self.logger.error(f"Failed to reject content: {str(e)}")
            raise
    
    async def request_revision(
        self,
        content_id: str,
        reviewer_id: str,
        feedback: List[str]
    ) -> Dict:
        """Request content revision."""
        try:
            # Load review record
            review_file = next(self.reviews_dir.glob(f"{content_id}_v*.json"))
            with open(review_file) as f:
                review = json.load(f)
            
            if review['status'] not in [ReviewStatus.IN_REVIEW.value]:
                raise ValueError(f"Content not ready for revision: {review['status']}")
            
            # Update review
            review['status'] = ReviewStatus.NEEDS_REVISION.value
            review['revision_requested_by'] = reviewer_id
            review['revision_requested_at'] = datetime.now().isoformat()
            review['revision_feedback'] = feedback
            
            # Increment version for next revision
            review['current_version'] += 1
            
            # Save updated review with new version
            new_review_file = self.reviews_dir / f"{content_id}_v{review['current_version']}.json"
            with open(new_review_file, 'w') as f:
                json.dump(review, f, indent=2)
            
            self.logger.info(f"Revision requested for content: {content_id}")
            return review
            
        except Exception as e:
            self.logger.error(f"Failed to request revision: {str(e)}")
            raise
    
    async def get_review_status(self, content_id: str) -> Dict:
        """Get content review status."""
        try:
            # Find latest version
            review_files = list(self.reviews_dir.glob(f"{content_id}_v*.json"))
            if not review_files:
                raise ValueError(f"No review found for content: {content_id}")
            
            latest_file = max(review_files, key=lambda p: int(p.stem.split('_v')[1]))
            
            with open(latest_file) as f:
                review = json.load(f)
            
            return {
                'content_id': content_id,
                'status': review['status'],
                'version': review['current_version'],
                'reviews': review['reviews'],
                'latest_update': max(
                    review.get('submitted_at'),
                    review.get('approved_at', ''),
                    review.get('rejected_at', ''),
                    review.get('revision_requested_at', '')
                )
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get review status: {str(e)}")
            raise
