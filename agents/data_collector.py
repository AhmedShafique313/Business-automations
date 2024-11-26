import os
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import requests
from google.analytics import Analytics
from google.oauth2.credentials import Credentials
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from linkedin_api import Linkedin
from mailchimp3 import MailChimp
from hubspot import HubSpot
from twitter import Api as TwitterApi
from instagram_private_api import Client as InstagramApi
from pathlib import Path
import json
import aiohttp
import asyncio
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class DataSourceConfig:
    name: str
    type: str
    credentials: Dict
    endpoints: List[str]
    metrics: List[str]
    refresh_rate: str

class DataCollector:
    def __init__(self, config_path: str, work_dir: str):
        self.work_dir = Path(work_dir)
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.collectors: Dict[str, BaseCollector] = {}
        self.initialize_collectors()

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def initialize_collectors(self):
        """Initialize data collectors based on configuration."""
        collector_types = {
            'google_analytics': GoogleAnalyticsCollector,
            'facebook': FacebookCollector,
            'instagram': InstagramCollector,
            'linkedin': LinkedInCollector,
            'twitter': TwitterCollector,
            'mailchimp': MailChimpCollector,
            'hubspot': HubSpotCollector,
            'custom': CustomAPICollector
        }

        for source_config in self.config['data_sources']:
            source_type = source_config['type']
            if source_type in collector_types:
                self.collectors[source_config['name']] = collector_types[source_type](
                    DataSourceConfig(**source_config)
                )

    async def collect_all_data(self) -> Dict[str, pd.DataFrame]:
        """Collect data from all sources asynchronously."""
        tasks = []
        for collector in self.collectors.values():
            tasks.append(self.collect_source_data(collector))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data = {}
        for collector, result in zip(self.collectors.values(), results):
            if isinstance(result, Exception):
                self.logger.error(f"Error collecting data from {collector.config.name}: {str(result)}")
            else:
                data[collector.config.name] = result

        return data

    async def collect_source_data(self, collector: 'BaseCollector') -> pd.DataFrame:
        """Collect data from a specific source."""
        try:
            return await collector.collect_data()
        except Exception as e:
            self.logger.error(f"Error collecting data from {collector.config.name}: {str(e)}")
            raise

    def get_historical_data(self, source: str, start_date: datetime, 
                          end_date: datetime) -> pd.DataFrame:
        """Get historical data for a specific source."""
        collector = self.collectors.get(source)
        if not collector:
            raise ValueError(f"Source {source} not found")
        
        return collector.get_historical_data(start_date, end_date)

    def validate_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
        """Validate collected data for quality and completeness."""
        validation_results = {}
        
        for source, df in data.items():
            issues = []
            
            # Check for missing values
            missing = df.isnull().sum()
            if missing.any():
                issues.append(f"Missing values found: {missing[missing > 0].to_dict()}")
            
            # Check for data freshness
            if 'timestamp' in df.columns:
                latest = df['timestamp'].max()
                if latest < datetime.now() - timedelta(hours=1):
                    issues.append(f"Data may be stale. Latest timestamp: {latest}")
            
            # Check for anomalies
            for column in df.select_dtypes(include=['number']).columns:
                mean = df[column].mean()
                std = df[column].std()
                outliers = df[abs(df[column] - mean) > 3 * std]
                if not outliers.empty:
                    issues.append(f"Potential outliers found in {column}")
            
            validation_results[source] = issues
        
        return validation_results

class BaseCollector(ABC):
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def collect_data(self) -> pd.DataFrame:
        """Collect data from the source."""
        pass

    @abstractmethod
    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical data from the source."""
        pass

class GoogleAnalyticsCollector(BaseCollector):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.analytics = self._initialize_analytics()

    def _initialize_analytics(self) -> Analytics:
        """Initialize Google Analytics client."""
        credentials = Credentials.from_authorized_user_info(self.config.credentials)
        return Analytics(credentials=credentials)

    async def collect_data(self) -> pd.DataFrame:
        """Collect Google Analytics data."""
        # Implementation for Google Analytics data collection
        pass

    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical Google Analytics data."""
        # Implementation for historical Google Analytics data
        pass

class FacebookCollector(BaseCollector):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.api = self._initialize_facebook()

    def _initialize_facebook(self) -> FacebookAdsApi:
        """Initialize Facebook API client."""
        return FacebookAdsApi.init(
            access_token=self.config.credentials['access_token']
        )

    async def collect_data(self) -> pd.DataFrame:
        """Collect Facebook data."""
        # Implementation for Facebook data collection
        pass

    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical Facebook data."""
        # Implementation for historical Facebook data
        pass

class InstagramCollector(BaseCollector):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.api = self._initialize_instagram()

    def _initialize_instagram(self) -> InstagramApi:
        """Initialize Instagram API client."""
        return InstagramApi(
            username=self.config.credentials['username'],
            password=self.config.credentials['password']
        )

    async def collect_data(self) -> pd.DataFrame:
        """Collect Instagram data."""
        # Implementation for Instagram data collection
        pass

    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical Instagram data."""
        # Implementation for historical Instagram data
        pass

class LinkedInCollector(BaseCollector):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.api = self._initialize_linkedin()

    def _initialize_linkedin(self) -> Linkedin:
        """Initialize LinkedIn API client."""
        return Linkedin(
            username=self.config.credentials['username'],
            password=self.config.credentials['password']
        )

    async def collect_data(self) -> pd.DataFrame:
        """Collect LinkedIn data."""
        # Implementation for LinkedIn data collection
        pass

    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical LinkedIn data."""
        # Implementation for historical LinkedIn data
        pass

class TwitterCollector(BaseCollector):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.api = self._initialize_twitter()

    def _initialize_twitter(self) -> TwitterApi:
        """Initialize Twitter API client."""
        return TwitterApi(
            consumer_key=self.config.credentials['consumer_key'],
            consumer_secret=self.config.credentials['consumer_secret'],
            access_token_key=self.config.credentials['access_token_key'],
            access_token_secret=self.config.credentials['access_token_secret']
        )

    async def collect_data(self) -> pd.DataFrame:
        """Collect Twitter data."""
        # Implementation for Twitter data collection
        pass

    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical Twitter data."""
        # Implementation for historical Twitter data
        pass

class MailChimpCollector(BaseCollector):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.client = self._initialize_mailchimp()

    def _initialize_mailchimp(self) -> MailChimp:
        """Initialize MailChimp client."""
        return MailChimp(mc_api=self.config.credentials['api_key'])

    async def collect_data(self) -> pd.DataFrame:
        """Collect MailChimp data."""
        # Implementation for MailChimp data collection
        pass

    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical MailChimp data."""
        # Implementation for historical MailChimp data
        pass

class HubSpotCollector(BaseCollector):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.client = self._initialize_hubspot()

    def _initialize_hubspot(self) -> HubSpot:
        """Initialize HubSpot client."""
        return HubSpot(api_key=self.config.credentials['api_key'])

    async def collect_data(self) -> pd.DataFrame:
        """Collect HubSpot data."""
        # Implementation for HubSpot data collection
        pass

    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical HubSpot data."""
        # Implementation for historical HubSpot data
        pass

class CustomAPICollector(BaseCollector):
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.session = aiohttp.ClientSession()

    async def collect_data(self) -> pd.DataFrame:
        """Collect data from custom API endpoints."""
        data = []
        for endpoint in self.config.endpoints:
            try:
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        data.append(await response.json())
                    else:
                        self.logger.error(f"Error fetching data from {endpoint}: {response.status}")
            except Exception as e:
                self.logger.error(f"Error collecting data from {endpoint}: {str(e)}")
        
        return pd.DataFrame(data)

    def get_historical_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical data from custom API endpoints."""
        # Implementation for historical custom API data
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
