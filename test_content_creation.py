"""
Test Content Creation with Research Data
Tests the AI Marketing Platform's content creation capabilities using real research data.
"""

import asyncio
import json
from pathlib import Path
import logging
from datetime import datetime, timedelta
import aiohttp
import numpy as np
from bs4 import BeautifulSoup
import uuid

from agents.agent_orchestrator import AgentOrchestrator
from agents.intelligence.agency.agents.trend_analyzer import TrendMetrics, TrendSource, TrendPattern, Trend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_research_trends(industry: str) -> list[dict]:
    """Fetch real research trends from academic and industry sources."""
    async with aiohttp.ClientSession() as session:
        trends = []
        
        # Research sources
        sources = {
            'tech': [
                'https://arxiv.org/list/cs.AI/recent',  # AI/ML research
                'https://arxiv.org/list/cs.CL/recent',  # NLP research
                'https://arxiv.org/list/cs.CV/recent'   # Computer Vision research
            ],
            'fitness': [
                'https://pubmed.ncbi.nlm.nih.gov/?term=fitness+trends',
                'https://pubmed.ncbi.nlm.nih.gov/?term=exercise+science'
            ]
        }
        
        if industry not in sources:
            raise ValueError(f"No research sources defined for industry: {industry}")
        
        for url in sources[industry]:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        if 'arxiv.org' in url:
                            # Parse arXiv papers
                            papers = soup.find_all('div', class_='list-title')
                            for paper in papers[:5]:  # Get top 5 papers
                                title = paper.get_text(strip=True)
                                abstract = paper.find_next('p', class_='mathjax').get_text(strip=True)
                                trends.append({
                                    'title': title,
                                    'description': abstract,
                                    'source': 'arXiv',
                                    'url': url,
                                    'timestamp': datetime.now().isoformat()
                                })
                        
                        elif 'pubmed' in url:
                            # Parse PubMed articles
                            articles = soup.find_all('article', class_='full-docsum')
                            for article in articles[:5]:  # Get top 5 articles
                                title = article.find('a', class_='docsum-title').get_text(strip=True)
                                abstract = article.find('div', class_='full-view-snippet').get_text(strip=True)
                                trends.append({
                                    'title': title,
                                    'description': abstract,
                                    'source': 'PubMed',
                                    'url': url,
                                    'timestamp': datetime.now().isoformat()
                                })
            
            except Exception as e:
                logger.error(f"Failed to fetch from {url}: {e}")
                continue
        
        return trends

def create_trend_from_research(research_data: dict, industry: str) -> Trend:
    """Create a trend object from research data."""
    return Trend(
        trend_id=str(uuid.uuid4()),
        title=research_data['title'],
        description=research_data['description'],
        category=industry,
        keywords=extract_keywords(research_data['description']),  # Extract keywords from description
        metrics=TrendMetrics(
            engagement_rate=0.8,  # Research-based content tends to have good engagement
            growth_rate=0.7,
            virality_score=0.75,
            longevity_score=0.9,  # Research content has longer relevance
            cross_platform_presence=0.8,
            industry_relevance={industry: 0.9},
            demographic_fit={"18-35": 0.7, "35-50": 0.8, "50+": 0.6},
            sentiment_score=0.8,
            conversion_potential=0.7,
            brand_safety_score=0.95  # Research content is typically brand-safe
        ),
        sources=[
            TrendSource(
                platform=research_data['source'],
                url=research_data['url'],
                post_id=None,
                author=None,
                timestamp=research_data['timestamp'],
                engagement={"views": 5000, "citations": 100},
                reach=10000
            )
        ],
        patterns=[
            TrendPattern(
                pattern_type="research_insight",
                frequency=0.8,
                impact_score=0.85,
                examples=[
                    "Present research findings",
                    "Explain practical applications",
                    "Show real-world impact"
                ],
                context={
                    "tone": "educational",
                    "style": "authoritative",
                    "approach": "data-driven"
                }
            )
        ],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        expiry=(datetime.now() + timedelta(days=30)).isoformat(),  # Research trends have longer relevance
        status="active",
        score=0.85
    )

def extract_keywords(text: str) -> list[str]:
    """Extract relevant keywords from text using NLP."""
    # TODO: Implement more sophisticated keyword extraction
    # For now, just split and take unique words
    words = text.lower().split()
    return list(set([w for w in words if len(w) > 4]))[:10]  # Take top 10 unique words

async def test_content_creation():
    """Test content creation using real research data."""
    orchestrator = AgentOrchestrator()
    
    # Test scenarios
    test_cases = [
        {
            'industry': 'tech',
            'platforms': ['linkedin', 'medium'],  # Professional platforms for research content
            'content_types': ['article', 'infographic'],
            'context': {
                'target_audience': 'tech professionals and researchers',
                'brand_voice': 'authoritative and innovative',
                'key_topics': ['AI research', 'machine learning', 'innovation']
            }
        },
        {
            'industry': 'fitness',
            'platforms': ['instagram', 'youtube'],
            'content_types': ['video', 'infographic'],
            'context': {
                'target_audience': 'fitness enthusiasts and health professionals',
                'brand_voice': 'scientific and practical',
                'key_topics': ['exercise science', 'health research', 'fitness innovation']
            }
        }
    ]
    
    results = []
    for test_case in test_cases:
        try:
            logger.info(f"Testing content creation for {test_case['industry']} industry")
            
            # Fetch real research trends
            research_trends = await fetch_research_trends(test_case['industry'])
            
            # Convert research data to trends
            trends = [
                create_trend_from_research(data, test_case['industry'])
                for data in research_trends
            ]
            
            # Update trend analyzer cache
            orchestrator.trend_analyzer.trends_cache[test_case['industry']] = trends
            
            # Create campaign
            campaign = await orchestrator.create_viral_campaign(
                industry=test_case['industry'],
                platforms=test_case['platforms'],
                content_types=test_case['content_types'],
                context=test_case['context']
            )
            
            # Get campaign insights
            insights = await orchestrator.get_campaign_insights(campaign['campaign_id'])
            
            result = {
                'test_case': test_case,
                'research_trends': research_trends,
                'campaign': campaign,
                'insights': insights,
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
            
            # Log success metrics
            logger.info(f"Campaign {campaign['campaign_id']} metrics:")
            for content in campaign['content']:
                logger.info(f"Platform: {content['platform']}")
                logger.info(f"Research-based content:")
                logger.info(f"- Quality: {content['validation']['validations']['quality']['score']:.2f}")
                logger.info(f"- Scientific Accuracy: {content['validation']['validations'].get('scientific_accuracy', {'score': 0.0})['score']:.2f}")
                logger.info(f"- Engagement Potential: {content['validation']['validations']['engagement']['score']:.2f}")
                logger.info("Content preview:")
                logger.info(json.dumps(content['content'], indent=2))
                logger.info("-" * 80)
            
        except Exception as e:
            logger.error(f"Test case failed: {e}")
            result = {
                'test_case': test_case,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            results.append(result)
    
    # Save results
    output_dir = Path('test_results')
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f'research_content_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Test results saved to {output_file}")
    return results

if __name__ == "__main__":
    asyncio.run(test_content_creation())
