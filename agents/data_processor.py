import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
from aiohttp import ClientSession
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Handles data collection and processing from multiple sources."""
    
    def __init__(self, config_path: str):
        """Initialize the DataProcessor with configuration."""
        self.config = self._load_config(config_path)
        self.session: Optional[ClientSession] = None
        self.data_cache: Dict[str, pd.DataFrame] = {}
    
    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    async def initialize(self):
        """Initialize HTTP session and other resources."""
        self.session = ClientSession()
    
    async def close(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_data(self, source: dict, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data from a specific source with retry logic."""
        source_type = source['type']
        metrics = source['metrics']
        
        try:
            if source_type == 'google_analytics':
                return await self._fetch_google_analytics(source, metrics, start_date, end_date)
            elif source_type == 'facebook':
                return await self._fetch_facebook(source, metrics, start_date, end_date)
            elif source_type == 'instagram':
                return await self._fetch_instagram(source, metrics, start_date, end_date)
            elif source_type == 'linkedin':
                return await self._fetch_linkedin(source, metrics, start_date, end_date)
            elif source_type == 'mailchimp':
                return await self._fetch_mailchimp(source, metrics, start_date, end_date)
            elif source_type == 'hubspot':
                return await self._fetch_hubspot(source, metrics, start_date, end_date)
            elif source_type == 'custom':
                return await self._fetch_custom(source, metrics, start_date, end_date)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
        except Exception as e:
            logger.error(f"Error fetching data from {source_type}: {e}")
            raise
    
    async def collect_all_data(self, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        """Collect data from all configured sources."""
        tasks = []
        for source in self.config['data_sources']:
            tasks.append(self.fetch_data(source, start_date, end_date))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_data = {}
        for source, result in zip(self.config['data_sources'], results):
            if isinstance(result, Exception):
                logger.error(f"Failed to collect data from {source['name']}: {result}")
                continue
            processed_data[source['name']] = result
        
        return processed_data
    
    def process_data(self, raw_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Process and combine data from multiple sources."""
        processed_dfs = []
        
        for source_name, df in raw_data.items():
            if df.empty:
                continue
            
            # Add source identifier
            df['source'] = source_name
            processed_dfs.append(df)
        
        if not processed_dfs:
            return pd.DataFrame()
        
        # Combine all data
        combined_df = pd.concat(processed_dfs, ignore_index=True)
        
        # Apply aggregations based on config
        aggregation_intervals = self.config['data_processing']['aggregation_intervals']
        aggregated_data = self._apply_aggregations(combined_df, aggregation_intervals)
        
        return aggregated_data
    
    def _apply_aggregations(self, df: pd.DataFrame, intervals: List[str]) -> pd.DataFrame:
        """Apply time-based aggregations to the data."""
        aggregated_dfs = []
        
        for interval in intervals:
            # Convert interval string to pandas offset
            if interval.endswith('h'):
                freq = f"{interval[:-1]}H"
            elif interval.endswith('d'):
                freq = f"{interval[:-1]}D"
            else:
                logger.warning(f"Unsupported interval format: {interval}")
                continue
            
            # Perform aggregation
            agg_df = df.resample(freq, on='timestamp').agg({
                'value': 'mean',
                'source': 'first'
            }).reset_index()
            
            agg_df['interval'] = interval
            aggregated_dfs.append(agg_df)
        
        return pd.concat(aggregated_dfs, ignore_index=True)
    
    async def _fetch_google_analytics(self, source: dict, metrics: List[str], 
                                    start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data from Google Analytics."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Prepare the Analytics API request
            view_id = source['view_id']
            url = f"https://www.googleapis.com/analytics/v3/data/ga"
            params = {
                'ids': f'ga:{view_id}',
                'start-date': start_date.strftime('%Y-%m-%d'),
                'end-date': end_date.strftime('%Y-%m-%d'),
                'metrics': ','.join(metrics),
                'dimensions': 'ga:date'
            }
            
            headers = {
                'Authorization': f'Bearer {source["access_token"]}'
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                
            # Convert to DataFrame
            df = pd.DataFrame(data['rows'], columns=['date'] + metrics)
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.drop('date', axis=1)
            
            # Melt metrics into a single column
            df = pd.melt(df, id_vars=['timestamp'], var_name='metric', value_name='value')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Google Analytics data: {e}")
            return pd.DataFrame()
    
    async def _fetch_facebook(self, source: dict, metrics: List[str],
                            start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data from Facebook Insights."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Prepare the Facebook API request
            page_id = source['page_id']
            access_token = source['access_token']
            url = f"https://graph.facebook.com/v17.0/{page_id}/insights"
            
            params = {
                'metric': ','.join(metrics),
                'period': 'day',
                'since': int(start_date.timestamp()),
                'until': int(end_date.timestamp()),
                'access_token': access_token
            }
            
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
            
            # Process the data
            all_data = []
            for metric in data['data']:
                metric_name = metric['name']
                for value in metric['values']:
                    all_data.append({
                        'timestamp': value['end_time'],
                        'metric': metric_name,
                        'value': value['value']
                    })
            
            return pd.DataFrame(all_data)
            
        except Exception as e:
            logger.error(f"Error fetching Facebook data: {e}")
            return pd.DataFrame()
    
    async def _fetch_instagram(self, source: dict, metrics: List[str],
                             start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data from Instagram Insights."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Prepare the Instagram API request
            account_id = source['account_id']
            access_token = source['access_token']
            url = f"https://graph.facebook.com/v17.0/{account_id}/insights"
            
            params = {
                'metric': ','.join(metrics),
                'period': 'day',
                'since': int(start_date.timestamp()),
                'until': int(end_date.timestamp()),
                'access_token': access_token
            }
            
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
            
            # Process the data
            all_data = []
            for metric in data['data']:
                metric_name = metric['name']
                for value in metric['values']:
                    all_data.append({
                        'timestamp': value['end_time'],
                        'metric': metric_name,
                        'value': value['value']
                    })
            
            return pd.DataFrame(all_data)
            
        except Exception as e:
            logger.error(f"Error fetching Instagram data: {e}")
            return pd.DataFrame()
    
    async def _fetch_linkedin(self, source: dict, metrics: List[str],
                            start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data from LinkedIn Company Pages."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Prepare the LinkedIn API request
            organization_id = source['organization_id']
            access_token = source['access_token']
            url = f"https://api.linkedin.com/v2/organizationalEntityShareStatistics"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            params = {
                'q': 'organization',
                'organization': f'urn:li:organization:{organization_id}',
                'timeIntervals.timeGranularity': 'DAY',
                'timeIntervals.start': int(start_date.timestamp() * 1000),
                'timeIntervals.end': int(end_date.timestamp() * 1000)
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
            
            # Process the data
            all_data = []
            for element in data['elements']:
                time_range = element['timeRange']
                for metric in metrics:
                    if metric in element['totalShareStatistics']:
                        all_data.append({
                            'timestamp': datetime.fromtimestamp(time_range['start'] / 1000),
                            'metric': metric,
                            'value': element['totalShareStatistics'][metric]
                        })
            
            return pd.DataFrame(all_data)
            
        except Exception as e:
            logger.error(f"Error fetching LinkedIn data: {e}")
            return pd.DataFrame()
    
    async def _fetch_mailchimp(self, source: dict, metrics: List[str],
                              start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data from MailChimp."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Prepare the MailChimp API request
            api_key = source['api_key']
            server = source['server_prefix']
            list_id = source['list_id']
            url = f"https://{server}.api.mailchimp.com/3.0/reports"
            
            headers = {
                'Authorization': f'apikey {api_key}'
            }
            
            params = {
                'count': 1000,
                'list_id': list_id,
                'since_send_time': start_date.isoformat(),
                'before_send_time': end_date.isoformat()
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
            
            # Process the data
            all_data = []
            for report in data['reports']:
                send_time = datetime.strptime(report['send_time'], '%Y-%m-%dT%H:%M:%S%z')
                for metric in metrics:
                    if metric in report:
                        all_data.append({
                            'timestamp': send_time,
                            'metric': metric,
                            'value': report[metric]
                        })
            
            return pd.DataFrame(all_data)
            
        except Exception as e:
            logger.error(f"Error fetching MailChimp data: {e}")
            return pd.DataFrame()
    
    async def _fetch_hubspot(self, source: dict, metrics: List[str],
                            start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data from HubSpot."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Prepare the HubSpot API request
            api_key = source['api_key']
            url = "https://api.hubapi.com/analytics/v2/reports"
            
            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            
            params = {
                'start': int(start_date.timestamp() * 1000),
                'end': int(end_date.timestamp() * 1000),
                'metrics': metrics
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
            
            # Process the data
            all_data = []
            for metric in data:
                for point in metric['data']:
                    all_data.append({
                        'timestamp': datetime.fromtimestamp(point['timestamp'] / 1000),
                        'metric': metric['name'],
                        'value': point['value']
                    })
            
            return pd.DataFrame(all_data)
            
        except Exception as e:
            logger.error(f"Error fetching HubSpot data: {e}")
            return pd.DataFrame()
    
    async def _fetch_custom(self, source: dict, metrics: List[str],
                           start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch data from custom endpoints."""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        try:
            # Prepare the custom API request
            url = source['endpoint']
            headers = source.get('headers', {})
            
            params = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': ','.join(metrics)
            }
            
            # Add any custom parameters from config
            params.update(source.get('params', {}))
            
            async with self.session.get(url, params=params, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
            
            # Process the data according to the custom format specified in config
            data_format = source.get('data_format', {})
            timestamp_field = data_format.get('timestamp_field', 'timestamp')
            metric_field = data_format.get('metric_field', 'metric')
            value_field = data_format.get('value_field', 'value')
            
            all_data = []
            for item in data:
                all_data.append({
                    'timestamp': item[timestamp_field],
                    'metric': item[metric_field],
                    'value': item[value_field]
                })
            
            return pd.DataFrame(all_data)
            
        except Exception as e:
            logger.error(f"Error fetching custom data: {e}")
            return pd.DataFrame()

async def main():
    """Main function to demonstrate usage."""
    config_path = Path(__file__).parent / 'config' / 'data_collection_config.json'
    processor = DataProcessor(str(config_path))
    
    await processor.initialize()
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        raw_data = await processor.collect_all_data(start_date, end_date)
        processed_data = processor.process_data(raw_data)
        
        logger.info(f"Collected and processed data from {len(raw_data)} sources")
        logger.info(f"Processed data shape: {processed_data.shape}")
    finally:
        await processor.close()

if __name__ == '__main__':
    asyncio.run(main())
