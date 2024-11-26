from base_agent import BaseAgent
import json
from pathlib import Path
import time

class CheckerAgent(BaseAgent):
    def __init__(self, work_dir):
        super().__init__("Checker", work_dir)
        self.review_criteria = {
            'branding': {
                'weight': 0.3,
                'checks': [
                    'consistent_voice',
                    'luxury_appeal',
                    'professional_tone'
                ]
            },
            'engagement': {
                'weight': 0.25,
                'checks': [
                    'compelling_title',
                    'clear_call_to_action',
                    'emotional_connection'
                ]
            },
            'technical': {
                'weight': 0.25,
                'checks': [
                    'proper_formatting',
                    'optimal_timing',
                    'hashtag_relevance'
                ]
            },
            'quality': {
                'weight': 0.2,
                'checks': [
                    'content_originality',
                    'value_proposition',
                    'target_audience_fit'
                ]
            }
        }
        
    def review_content(self, work_file):
        """Review content based on established criteria"""
        content = self.load_work(work_file)
        review_results = {
            'original_content': content,
            'review_timestamp': time.time(),
            'criteria_scores': {},
            'feedback': [],
            'overall_score': 0,
            'status': 'pending'
        }
        
        # Evaluate each criteria
        for category, details in self.review_criteria.items():
            category_score = self._evaluate_category(content, category, details)
            review_results['criteria_scores'][category] = category_score
            
        # Calculate overall score
        overall_score = sum(
            score * self.review_criteria[cat]['weight']
            for cat, score in review_results['criteria_scores'].items()
        )
        review_results['overall_score'] = overall_score
        
        # Generate feedback and status
        review_results['feedback'] = self._generate_feedback(review_results)
        review_results['status'] = 'approved' if overall_score >= 0.8 else 'needs_revision'
        
        # Save review results
        review_file = self.save_work(review_results, 'review')
        self.log_activity(
            'content_review',
            review_results['status'],
            {
                'original_file': str(work_file),
                'review_file': str(review_file),
                'score': overall_score
            }
        )
        
        return review_file
        
    def _evaluate_category(self, content, category, criteria):
        """Evaluate content against specific category criteria"""
        if category == 'branding':
            return self._check_branding(content)
        elif category == 'engagement':
            return self._check_engagement(content)
        elif category == 'technical':
            return self._check_technical(content)
        elif category == 'quality':
            return self._check_quality(content)
        return 0.5  # Default score
        
    def _check_branding(self, content):
        """Check branding consistency and luxury appeal"""
        score = 0
        checks = {
            'luxury_keywords': ['luxury', 'elegant', 'sophisticated', 'premium'],
            'brand_voice': ['professional', 'expert', 'transform', 'design']
        }
        
        description = content.get('description', '').lower()
        title = content.get('title', '').lower()
        
        # Check luxury keywords
        luxury_count = sum(1 for word in checks['luxury_keywords'] if word in description or word in title)
        score += (luxury_count / len(checks['luxury_keywords'])) * 0.5
        
        # Check brand voice
        voice_count = sum(1 for word in checks['brand_voice'] if word in description or word in title)
        score += (voice_count / len(checks['brand_voice'])) * 0.5
        
        return min(score, 1.0)
        
    def _check_engagement(self, content):
        """Check content engagement potential"""
        score = 0
        
        # Check title length and impact
        title = content.get('title', '')
        if 20 <= len(title) <= 60:
            score += 0.3
            
        # Check hashtag count
        hashtags = content.get('hashtags', [])
        if 3 <= len(hashtags) <= 6:
            score += 0.3
            
        # Check description length and call to action
        description = content.get('description', '')
        if 100 <= len(description) <= 300:
            score += 0.2
        if any(cta in description.lower() for cta in ['contact', 'book', 'visit', 'learn']):
            score += 0.2
            
        return min(score, 1.0)
        
    def _check_technical(self, content):
        """Check technical aspects of content"""
        score = 0
        
        # Check scheduling
        if content.get('scheduling'):
            score += 0.3
            
        # Check content structure
        if all(key in content for key in ['title', 'description', 'hashtags']):
            score += 0.4
            
        # Check hashtag format
        hashtags = content.get('hashtags', [])
        if all(tag.startswith('#') for tag in hashtags):
            score += 0.3
            
        return min(score, 1.0)
        
    def _check_quality(self, content):
        """Check content quality and originality"""
        score = 0.7  # Base score for original content
        
        # Add bonus for comprehensive content
        if len(content.get('description', '')) > 200:
            score += 0.15
            
        if len(content.get('hashtags', [])) >= 4:
            score += 0.15
            
        return min(score, 1.0)
        
    def _generate_feedback(self, review_results):
        """Generate specific feedback based on review results"""
        feedback = []
        scores = review_results['criteria_scores']
        
        for category, score in scores.items():
            if score < 0.8:
                feedback.append(self._get_improvement_suggestions(category, score))
                
        if review_results['overall_score'] >= 0.8:
            feedback.append("Content meets Design Gaga's high standards for luxury home staging presentation.")
            
        return feedback
        
    def _get_improvement_suggestions(self, category, score):
        """Get specific improvement suggestions based on category and score"""
        suggestions = {
            'branding': "Enhance luxury positioning and brand voice. Include more premium-focused language.",
            'engagement': "Strengthen call-to-action and emotional connection with the audience.",
            'technical': "Improve technical elements such as hashtag usage and posting schedule.",
            'quality': "Enhance content originality and value proposition for the target audience."
        }
        return f"{category.title()} ({score:.2f}): {suggestions.get(category, 'Needs improvement')}"
