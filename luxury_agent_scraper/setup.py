from setuptools import setup, find_packages

setup(
    name="luxury_agent_scraper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'playwright==1.39.0',
        'openai==1.2.3',
        'pandas==2.1.2',
        'beautifulsoup4==4.12.2',
        'python-dotenv==1.0.0',
        'asyncio==3.4.3',
        'aiohttp==3.8.6',
        'lxml==4.9.3'
    ]
)
