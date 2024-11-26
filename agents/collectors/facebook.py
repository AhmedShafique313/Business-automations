from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.pagepost import PagePost
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.insights import Insights

class FacebookCollector:
    """Collects data from Facebook."""
    
    def __init__(self, api):
        """Initialize the collector with Facebook API instance."""
        self.api = api
    
    async def fetch_page_insights(self,
                                page_id: str,
                                metrics: List[str],
                                start_date: datetime,
                                end_date: datetime) -> pd.DataFrame:
        """
        Fetch page insights from Facebook.
        
        Args:
            page_id: Facebook page ID
            metrics: List of metrics to fetch
            start_date: Start date for the data
            end_date: End date for the data
            
        Returns:
            DataFrame containing page insights
        """
        try:
            page = Page(page_id)
            
            params = {
                'metric': metrics,
                'since': start_date.strftime('%Y-%m-%d'),
                'until': end_date.strftime('%Y-%m-%d'),
                'period': 'day'
            }
            
            insights = page.get_insights(params=params)
            
            # Process insights into DataFrame
            data = []
            for insight in insights:
                for value in insight['values']:
                    row_data = {
                        'metric': insight['name'],
                        'value': value['value'],
                        'timestamp': pd.to_datetime(value['end_time'])
                    }
                    data.append(row_data)
            
            df = pd.DataFrame(data)
            
            # Pivot the data to have metrics as columns
            df_pivoted = df.pivot(
                index='timestamp',
                columns='metric',
                values='value'
            ).reset_index()
            
            return df_pivoted
            
        except Exception as e:
            print(f"Error fetching Facebook page insights: {e}")
            return pd.DataFrame()
    
    async def fetch_post_insights(self,
                                page_id: str,
                                start_date: datetime,
                                end_date: datetime) -> pd.DataFrame:
        """
        Fetch insights for all posts within a date range.
        
        Args:
            page_id: Facebook page ID
            start_date: Start date for the data
            end_date: End date for the data
            
        Returns:
            DataFrame containing post insights
        """
        try:
            page = Page(page_id)
            
            # Get posts within date range
            params = {
                'since': start_date.strftime('%Y-%m-%d'),
                'until': end_date.strftime('%Y-%m-%d')
            }
            
            posts = page.get_posts(params=params)
            
            data = []
            for post in posts:
                post_obj = PagePost(post['id'])
                
                # Get insights for each post
                insights = post_obj.get_insights(params={
                    'metric': [
                        'post_impressions',
                        'post_engaged_users',
                        'post_reactions_by_type_total'
                    ]
                })
                
                row_data = {
                    'post_id': post['id'],
                    'message': post.get('message', ''),
                    'created_time': pd.to_datetime(post['created_time']),
                    'type': post.get('type', '')
                }
                
                # Add insights metrics
                for insight in insights:
                    row_data[insight['name']] = insight['values'][0]['value']
                
                data.append(row_data)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error fetching Facebook post insights: {e}")
            return pd.DataFrame()
    
    async def fetch_ad_insights(self,
                              ad_account_id: str,
                              start_date: datetime,
                              end_date: datetime) -> pd.DataFrame:
        """
        Fetch advertising insights.
        
        Args:
            ad_account_id: Facebook ad account ID
            start_date: Start date for the data
            end_date: End date for the data
            
        Returns:
            DataFrame containing ad insights
        """
        try:
            account = AdAccount(ad_account_id)
            
            params = {
                'time_range': {
                    'since': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                },
                'level': 'ad',
                'fields': [
                    'campaign_name',
                    'adset_name',
                    'ad_name',
                    'impressions',
                    'clicks',
                    'spend',
                    'actions',
                    'conversions'
                ]
            }
            
            insights = account.get_insights(params=params)
            
            data = []
            for insight in insights:
                row_data = insight.export_all_data()
                row_data['timestamp'] = pd.to_datetime(insight['date_start'])
                data.append(row_data)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error fetching Facebook ad insights: {e}")
            return pd.DataFrame()
    
    async def fetch_audience_insights(self,
                                   page_id: str) -> pd.DataFrame:
        """
        Fetch audience insights.
        
        Args:
            page_id: Facebook page ID
            
        Returns:
            DataFrame containing audience insights
        """
        try:
            page = Page(page_id)
            
            params = {
                'metric': [
                    'page_fans',
                    'page_fans_city',
                    'page_fans_country',
                    'page_fans_gender_age'
                ]
            }
            
            insights = page.get_insights(params=params)
            
            data = []
            for insight in insights:
                row_data = {
                    'metric': insight['name'],
                    'value': insight['values'][0]['value'],
                    'timestamp': pd.to_datetime(insight['values'][0]['end_time'])
                }
                data.append(row_data)
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error fetching Facebook audience insights: {e}")
            return pd.DataFrame()
