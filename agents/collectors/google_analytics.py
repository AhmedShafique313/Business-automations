from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

class GoogleAnalyticsCollector:
    """Collects data from Google Analytics."""
    
    def __init__(self, credentials):
        """Initialize the collector with credentials."""
        self.client = BetaAnalyticsDataClient(credentials=credentials)
    
    async def fetch_data(self, 
                        property_id: str,
                        metrics: List[str],
                        start_date: datetime,
                        end_date: datetime,
                        dimensions: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fetch data from Google Analytics.
        
        Args:
            property_id: Google Analytics property ID
            metrics: List of metrics to fetch
            start_date: Start date for the data
            end_date: End date for the data
            dimensions: Optional list of dimensions
            
        Returns:
            DataFrame containing the fetched data
        """
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )],
            metrics=[Metric(name=metric) for metric in metrics],
            dimensions=[Dimension(name=dim) for dim in (dimensions or [])]
        )
        
        try:
            response = await self.client.run_report(request)
            
            # Process the response into a DataFrame
            data = []
            for row in response.rows:
                row_data = {}
                
                # Add dimensions if present
                if dimensions:
                    for i, dim in enumerate(dimensions):
                        row_data[dim] = row.dimension_values[i].value
                
                # Add metrics
                for i, metric in enumerate(metrics):
                    row_data[metric] = float(row.metric_values[i].value)
                
                data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # Add timestamp column
            df['timestamp'] = pd.date_range(
                start=start_date,
                end=end_date,
                periods=len(df)
            )
            
            return df
            
        except Exception as e:
            print(f"Error fetching Google Analytics data: {e}")
            return pd.DataFrame()
    
    async def fetch_realtime_data(self,
                                property_id: str,
                                metrics: List[str]) -> pd.DataFrame:
        """
        Fetch real-time data from Google Analytics.
        
        Args:
            property_id: Google Analytics property ID
            metrics: List of metrics to fetch
            
        Returns:
            DataFrame containing the real-time data
        """
        request = RunReportRequest(
            property=f"properties/{property_id}",
            metrics=[Metric(name=metric) for metric in metrics]
        )
        
        try:
            response = await self.client.run_realtime_report(request)
            
            # Process the response into a DataFrame
            data = []
            for row in response.rows:
                row_data = {}
                for i, metric in enumerate(metrics):
                    row_data[metric] = float(row.metric_values[i].value)
                data.append(row_data)
            
            df = pd.DataFrame(data)
            df['timestamp'] = datetime.now()
            
            return df
            
        except Exception as e:
            print(f"Error fetching real-time Google Analytics data: {e}")
            return pd.DataFrame()
    
    async def fetch_common_metrics(self,
                                 property_id: str,
                                 start_date: datetime,
                                 end_date: datetime) -> pd.DataFrame:
        """
        Fetch commonly used metrics from Google Analytics.
        
        Args:
            property_id: Google Analytics property ID
            start_date: Start date for the data
            end_date: End date for the data
            
        Returns:
            DataFrame containing common metrics
        """
        common_metrics = [
            'activeUsers',
            'screenPageViews',
            'sessions',
            'bounceRate',
            'averageSessionDuration',
            'conversions',
            'totalRevenue'
        ]
        
        common_dimensions = [
            'date',
            'deviceCategory',
            'country'
        ]
        
        return await self.fetch_data(
            property_id=property_id,
            metrics=common_metrics,
            dimensions=common_dimensions,
            start_date=start_date,
            end_date=end_date
        )
