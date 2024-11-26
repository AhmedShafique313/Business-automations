import os
import json
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from PIL import Image
from io import BytesIO

class GMBManager:
    """Manages Google My Business profile optimization"""
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """Initialize GMB manager"""
        self.setup_logging()
        self.credentials = self._load_credentials(credentials_path)
        self.setup_gmb_service()
        
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gmb.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('GMBManager')
        
    def _load_credentials(self, credentials_path: str) -> Dict:
        """Load GMB credentials from file"""
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                return creds.get('GMB', {})
        except Exception as e:
            self.logger.error(f"Error loading credentials: {str(e)}")
            return {}
            
    def setup_gmb_service(self):
        """Set up Google My Business API service"""
        try:
            credentials = service_account.Credentials.from_service_account_info(
                self.credentials,
                scopes=['https://www.googleapis.com/auth/business.manage']
            )
            
            self.service = build('mybusiness', 'v4', credentials=credentials)
            self.logger.info("Successfully initialized GMB service")
            
        except Exception as e:
            self.logger.error(f"Error setting up GMB service: {str(e)}")
            
    def optimize_business_info(self):
        """Optimize basic business information"""
        try:
            account = self.service.accounts().list().execute()
            account_name = account['accounts'][0]['name']
            
            # Get the location
            locations = self.service.accounts().locations().list(
                parent=account_name
            ).execute()
            
            location = locations['locations'][0]
            location_name = location['name']
            
            # Update business information
            updated_location = {
                'locationName': 'Design Gaga - Luxury Home Staging',
                'primaryCategory': {
                    'displayName': 'Home Staging Service'
                },
                'additionalCategories': [
                    {'displayName': 'Interior Designer'},
                    {'displayName': 'Real Estate Service'}
                ],
                'websiteUrl': 'https://designgaga.com',
                'regularHours': {
                    'periods': [
                        {
                            'openDay': 'MONDAY',
                            'openTime': '09:00',
                            'closeDay': 'MONDAY',
                            'closeTime': '17:00'
                        },
                        # Add other days similarly
                    ]
                },
                'serviceArea': {
                    'businessType': 'CUSTOMER_AND_BUSINESS_LOCATION',
                    'places': [
                        {'regionCode': 'CA-ON'}
                    ]
                },
                'labels': [
                    'luxury home staging',
                    'real estate staging',
                    'interior design',
                    'luxury properties',
                    'home styling'
                ]
            }
            
            # Update the location
            self.service.accounts().locations().patch(
                name=location_name,
                body=updated_location,
                updateMask='locationName,primaryCategory,additionalCategories,websiteUrl,regularHours,serviceArea,labels'
            ).execute()
            
            self.logger.info("Successfully updated business information")
            
        except Exception as e:
            self.logger.error(f"Error updating business information: {str(e)}")
            
    def post_update(self, content: Dict):
        """Post an update to GMB profile"""
        try:
            account = self.service.accounts().list().execute()
            account_name = account['accounts'][0]['name']
            
            # Create post data
            post_data = {
                'topicType': 'STANDARD',
                'languageCode': 'en-US',
                'summary': content['text'],
                'callToAction': {
                    'actionType': 'BOOK',
                    'url': content.get('link', 'https://designgaga.com')
                }
            }
            
            # Add media if provided
            if content.get('image_url'):
                media_item = self._upload_media(content['image_url'])
                if media_item:
                    post_data['media'] = [{'mediaFormat': 'PHOTO', 'sourceUrl': media_item['sourceUrl']}]
            
            # Create the post
            self.service.accounts().locations().localPosts().create(
                parent=f"{account_name}/locations/{location_id}",
                body=post_data
            ).execute()
            
            self.logger.info("Successfully created GMB post")
            
        except Exception as e:
            self.logger.error(f"Error creating GMB post: {str(e)}")
            
    def _upload_media(self, image_url: str) -> Optional[Dict]:
        """Upload media to GMB"""
        try:
            # Download image
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            
            # Optimize image
            optimized_image = BytesIO()
            image.save(optimized_image, format='JPEG', quality=85, optimize=True)
            
            # Upload to GMB
            media_item = self.service.accounts().locations().media().create(
                parent=location_name,
                body={
                    'mediaFormat': 'PHOTO',
                    'sourceUrl': image_url
                }
            ).execute()
            
            return media_item
            
        except Exception as e:
            self.logger.error(f"Error uploading media: {str(e)}")
            return None
            
    def update_attributes(self):
        """Update business attributes"""
        try:
            attributes = {
                'attributes': [
                    {
                        'name': 'has_wheelchair_accessible_entrance',
                        'values': ['true']
                    },
                    {
                        'name': 'has_free_wifi',
                        'values': ['true']
                    },
                    {
                        'name': 'requires_appointments',
                        'values': ['true']
                    }
                ]
            }
            
            self.service.accounts().locations().attributes().patch(
                name=f"{location_name}/attributes",
                body=attributes,
                updateMask='attributes'
            ).execute()
            
            self.logger.info("Successfully updated business attributes")
            
        except Exception as e:
            self.logger.error(f"Error updating attributes: {str(e)}")
            
    def add_business_description(self):
        """Update business description"""
        try:
            description = """Design Gaga is Toronto's premier luxury home staging and interior design company. 
            We specialize in preparing high-end properties for the luxury real estate market, combining elegant design 
            with strategic staging to maximize property value. Our expert team transforms spaces into sophisticated, 
            market-ready environments that appeal to discerning buyers.

            Services include:
            • Custom Luxury Home Staging
            • Interior Design Consultation
            • Property Enhancement Strategy
            • Virtual Staging Solutions
            • Pre-listing Optimization

            Serving the Greater Toronto Area including Forest Hill, Rosedale, Yorkville, and other premium locations.
            Contact us to elevate your luxury property presentation."""
            
            self.service.accounts().locations().patch(
                name=location_name,
                body={'profile': {'description': description}},
                updateMask='profile.description'
            ).execute()
            
            self.logger.info("Successfully updated business description")
            
        except Exception as e:
            self.logger.error(f"Error updating description: {str(e)}")
            
    def manage_reviews(self):
        """Monitor and respond to reviews"""
        try:
            # Get all reviews
            reviews = self.service.accounts().locations().reviews().list(
                parent=location_name
            ).execute()
            
            for review in reviews.get('reviews', []):
                # Check if review needs response
                if not review.get('reviewReply'):
                    # Generate appropriate response
                    response = self._generate_review_response(review)
                    
                    # Reply to review
                    self.service.accounts().locations().reviews().updateReply(
                        name=f"{review['name']}/reply",
                        body={'comment': response}
                    ).execute()
                    
            self.logger.info("Successfully managed reviews")
            
        except Exception as e:
            self.logger.error(f"Error managing reviews: {str(e)}")
            
    def _generate_review_response(self, review: Dict) -> str:
        """Generate appropriate response to a review"""
        rating = review.get('starRating', 0)
        
        if rating >= 4:
            return f"""Thank you for your wonderful review! We're delighted that you enjoyed our luxury staging services. 
            Your satisfaction is our priority, and we look forward to working with you again on future projects."""
        elif rating == 3:
            return f"""Thank you for your feedback. We appreciate your input and are always looking to improve our services. 
            Please contact us directly to discuss how we can better meet your expectations for future projects."""
        else:
            return f"""We apologize that your experience didn't meet your expectations. Your feedback is important to us. 
            Please contact our customer service team directly so we can address your concerns and improve our service."""
            
    def optimize_photos(self):
        """Optimize GMB profile photos"""
        try:
            # Define photo categories
            photo_categories = {
                'LOGO': 'path/to/logo.jpg',
                'COVER': 'path/to/cover.jpg',
                'INTERIOR': [
                    'path/to/interior1.jpg',
                    'path/to/interior2.jpg'
                ],
                'PRODUCT': [
                    'path/to/staging1.jpg',
                    'path/to/staging2.jpg'
                ]
            }
            
            for category, photos in photo_categories.items():
                if isinstance(photos, str):
                    self._upload_categorized_photo(photos, category)
                else:
                    for photo in photos:
                        self._upload_categorized_photo(photo, category)
                        
            self.logger.info("Successfully optimized profile photos")
            
        except Exception as e:
            self.logger.error(f"Error optimizing photos: {str(e)}")
            
    def _upload_categorized_photo(self, photo_path: str, category: str):
        """Upload a photo with specific category"""
        try:
            with open(photo_path, 'rb') as photo_file:
                media_item = self.service.accounts().locations().media().create(
                    parent=location_name,
                    body={
                        'mediaFormat': 'PHOTO',
                        'category': category
                    },
                    media_body=photo_file
                ).execute()
                
            return media_item
            
        except Exception as e:
            self.logger.error(f"Error uploading categorized photo: {str(e)}")
            return None
            
    def optimize_services(self):
        """Update and optimize service list"""
        try:
            services = {
                'serviceItems': [
                    {
                        'displayName': 'Luxury Home Staging',
                        'description': 'Complete staging service for luxury properties',
                        'price': {
                            'currencyCode': 'CAD',
                            'units': '2500',
                            'nanos': 0
                        }
                    },
                    {
                        'displayName': 'Interior Design Consultation',
                        'description': 'Professional design consultation for high-end properties',
                        'price': {
                            'currencyCode': 'CAD',
                            'units': '500',
                            'nanos': 0
                        }
                    },
                    {
                        'displayName': 'Virtual Staging',
                        'description': 'Digital staging solutions for online listings',
                        'price': {
                            'currencyCode': 'CAD',
                            'units': '1000',
                            'nanos': 0
                        }
                    }
                ]
            }
            
            self.service.accounts().locations().services().patch(
                name=f"{location_name}/services",
                body=services,
                updateMask='serviceItems'
            ).execute()
            
            self.logger.info("Successfully updated service list")
            
        except Exception as e:
            self.logger.error(f"Error updating services: {str(e)}")
            
    def run_optimization(self):
        """Run complete GMB optimization"""
        try:
            # Update basic information
            self.optimize_business_info()
            
            # Update description
            self.add_business_description()
            
            # Update attributes
            self.update_attributes()
            
            # Optimize photos
            self.optimize_photos()
            
            # Update services
            self.optimize_services()
            
            # Manage reviews
            self.manage_reviews()
            
            self.logger.info("Successfully completed GMB optimization")
            
        except Exception as e:
            self.logger.error(f"Error in GMB optimization: {str(e)}")
