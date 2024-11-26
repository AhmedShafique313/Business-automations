import os
import json
import requests
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class ServiceArea:
    name: str
    center: Dict[str, float]
    radius: int

@dataclass
class CitationData:
    business_name: str
    address: str
    phone: str
    website: str
    business_hours: Dict[str, str]
    categories: List[str]

class LocationManager:
    def __init__(self, config_path: str, work_dir: str):
        self.work_dir = Path(work_dir)
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.maps_api_key = os.getenv(self.config['map_integration']['api_key_env'])
        self.citation_data = CitationData(**self.config['citations']['citation_data'])
        self.service_areas = [ServiceArea(**area) for area in self.config['map_integration']['service_areas']]

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def generate_map_embed_code(self, width: str = '100%', height: str = '400px') -> str:
        """Generate Google Maps embed code with custom styling and markers."""
        center = self.config['map_integration']['default_center']
        zoom = self.config['map_integration']['default_zoom']
        
        map_features = ','.join(self.config['map_integration']['features'])
        
        embed_code = f'''
        <div id="map" style="width: {width}; height: {height};"></div>
        <script src="https://maps.googleapis.com/maps/api/js?key={self.maps_api_key}&libraries=places,geometry"></script>
        <script>
            function initMap() {{
                const map = new google.maps.Map(document.getElementById('map'), {{
                    center: {{ lat: {center['lat']}, lng: {center['lng']} }},
                    zoom: {zoom},
                    styles: {self._get_luxury_map_style()}
                }});

                // Add service area overlays
                {self._generate_service_area_js()}

                // Add custom markers for recent projects
                {self._generate_project_markers_js()}

                // Add main business marker
                const mainMarker = new google.maps.Marker({{
                    position: {{ lat: {center['lat']}, lng: {center['lng']} }},
                    map: map,
                    icon: '{self.config["map_integration"]["marker_settings"]["icon"]}',
                    animation: google.maps.Animation.DROP,
                    title: '{self.citation_data.business_name}'
                }});
            }}
            google.maps.event.addDomListener(window, 'load', initMap);
        </script>
        '''
        return embed_code

    def _get_luxury_map_style(self) -> str:
        """Return custom map styling for luxury appearance."""
        return '''[
            {
                "featureType": "all",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#2c2c2c"}]
            },
            {
                "featureType": "water",
                "elementType": "geometry",
                "stylers": [{"color": "#c8d7d4"}]
            },
            {
                "featureType": "landscape",
                "elementType": "geometry",
                "stylers": [{"color": "#f5f5f5"}]
            }
        ]'''

    def _generate_service_area_js(self) -> str:
        """Generate JavaScript code for service area circles."""
        circles_js = []
        for area in self.service_areas:
            circles_js.append(f'''
                new google.maps.Circle({{
                    strokeColor: '#FF0000',
                    strokeOpacity: 0.8,
                    strokeWeight: 2,
                    fillColor: '#FF0000',
                    fillOpacity: 0.1,
                    map: map,
                    center: {{ lat: {area.center['lat']}, lng: {area.center['lng']} }},
                    radius: {area.radius * 1000}
                }});
            ''')
        return '\n'.join(circles_js)

    def _generate_project_markers_js(self) -> str:
        """Generate JavaScript code for project location markers."""
        # This would typically load from a database or API
        # For now, using placeholder data
        return '''
            const projects = [
                {title: 'Luxury Condo Staging', lat: 43.6532, lng: -79.3832},
                {title: 'Executive Home Staging', lat: 43.8775, lng: -79.4088}
            ];
            
            projects.forEach(project => {
                new google.maps.Marker({
                    position: { lat: project.lat, lng: project.lng },
                    map: map,
                    icon: 'https://designgaga.com/project-marker.png',
                    title: project.title
                });
            });
        '''

    def verify_citations(self) -> Dict[str, List[str]]:
        """Verify business citations across directories."""
        issues = {
            'missing_listings': [],
            'inconsistent_data': [],
            'optimization_needed': []
        }
        
        for directory in self.config['citations']['local_directories'] + self.config['citations']['industry_directories']:
            # Implement directory-specific verification logic
            self._verify_directory_listing(directory, issues)
        
        return issues

    def _verify_directory_listing(self, directory: str, issues: Dict[str, List[str]]):
        """Verify listing in a specific directory."""
        # This would typically use directory-specific APIs or web scraping
        # For now, logging placeholder verification
        self.logger.info(f"Verifying listing in {directory}")
        
        # Example verification logic
        if directory == "google_business":
            # Check Google My Business listing using their API
            pass
        elif directory == "yelp":
            # Check Yelp listing using their API
            pass
        # Add more directory-specific verification logic

    def generate_citation_report(self) -> str:
        """Generate a report of citation status and recommendations."""
        issues = self.verify_citations()
        
        report = f'''
        Citation Audit Report for {self.citation_data.business_name}
        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        1. Missing Listings:
        {'- ' + '- '.join(issues['missing_listings']) if issues['missing_listings'] else 'None found'}
        
        2. Inconsistent Data:
        {'- ' + '- '.join(issues['inconsistent_data']) if issues['inconsistent_data'] else 'None found'}
        
        3. Optimization Opportunities:
        {'- ' + '- '.join(issues['optimization_needed']) if issues['optimization_needed'] else 'None found'}
        
        Recommendations:
        1. Ensure consistent NAP (Name, Address, Phone) across all directories
        2. Add high-quality images to all listings
        3. Regularly monitor and respond to reviews
        4. Keep business hours updated
        5. Maintain detailed service descriptions
        '''
        
        return report

    def update_schema_markup(self) -> str:
        """Generate updated schema markup for the website."""
        schema = {
            "@context": "https://schema.org",
            "@type": "HomeAndConstructionBusiness",
            "name": self.citation_data.business_name,
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Toronto",
                "addressRegion": "ON",
                "addressCountry": "CA"
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": self.config['map_integration']['default_center']['lat'],
                "longitude": self.config['map_integration']['default_center']['lng']
            },
            "url": self.citation_data.website,
            "telephone": self.citation_data.phone,
            "openingHoursSpecification": self._generate_opening_hours(),
            "areaServed": [area.name for area in self.service_areas]
        }
        
        return json.dumps(schema, indent=2)

    def _generate_opening_hours(self) -> List[Dict]:
        """Generate schema.org opening hours specification."""
        hours_spec = []
        for day, hours in self.citation_data.business_hours.items():
            if hours:
                start, end = hours.split('-')
                hours_spec.append({
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": day.capitalize(),
                    "opens": start,
                    "closes": end
                })
        return hours_spec
