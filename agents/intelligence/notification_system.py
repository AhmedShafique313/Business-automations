import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationSystem:
    """Handles email notifications and report generation."""
    
    def __init__(self, config_path: str):
        """Initialize the notification system."""
        self.config = self._load_config(config_path)
        self.email_config = self.config['email']
        
    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def send_performance_report(self, 
                              report_data: Dict,
                              recipient: str = "gagan@designgaga.ca") -> None:
        """
        Send performance report via email.
        
        Args:
            report_data: Dictionary containing report data
            recipient: Email recipient
        """
        try:
            # Generate report content
            html_content = self._generate_html_report(report_data)
            attachments = self._generate_report_attachments(report_data)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Weekly Performance Report - {pd.Timestamp.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.email_config['sender']
            msg['To'] = recipient
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Attach additional files
            for filename, content in attachments.items():
                attachment = MIMEApplication(content, _subtype="pdf")
                attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(attachment)
            
            # Send email
            self._send_email(msg)
            logger.info(f"Performance report sent to {recipient}")
            
        except Exception as e:
            logger.error(f"Failed to send performance report: {e}")
            raise
    
    def _generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML content for the performance report."""
        
        # Create HTML template with styling
        html = """
            <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .section {
                        margin: 20px 0;
                        padding: 20px;
                        background-color: #ffffff;
                        border-radius: 5px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    h2 {
                        color: #2c3e50;
                        border-bottom: 2px solid #eee;
                        padding-bottom: 10px;
                    }
                    .metric {
                        margin: 10px 0;
                        padding: 10px;
                        background-color: #f8f9fa;
                        border-radius: 4px;
                    }
                    .metric-header {
                        font-weight: bold;
                        color: #2c3e50;
                    }
                    .metric-value {
                        float: right;
                    }
                    .excellent { color: #28a745; }
                    .good { color: #17a2b8; }
                    .warning { color: #ffc107; }
                    .poor { color: #dc3545; }
                    .pattern {
                        margin: 10px 0;
                        padding: 10px;
                        background-color: #e9ecef;
                        border-radius: 4px;
                    }
                    .recommendation {
                        margin: 10px 0;
                        padding: 10px;
                        background-color: #f8f9fa;
                        border-left: 4px solid #007bff;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Performance Intelligence Report</h1>
                    <p>Generated on: """ + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                </div>
        """
        
        # Add metrics section
        html += """
                <div class="section">
                    <h2>Key Metrics</h2>
        """
        
        for category, data in report_data['metrics'].items():
            html += f"""
                <div class="metric">
                    <div class="metric-header">{category.replace('_', ' ').title()}</div>
            """
            for key, value in data.items():
                html += f"""
                    <div>
                        <span>{key.replace('_', ' ').title()}</span>
                        <span class="metric-value {value['status']}">{value['rate'] if 'rate' in value else value['amount']} ({value['trend']})</span>
                    </div>
                """
            html += "</div>"
        
        # Add patterns section
        if 'patterns' in report_data:
            html += """
                    <div class="section">
                        <h2>Performance Patterns</h2>
            """
            
            for category, data in report_data['patterns'].items():
                html += f"""
                    <div class="pattern">
                        <div class="metric-header">{category.replace('_', ' ').title()}</div>
                """
                for key, value in data.items():
                    if isinstance(value, list):
                        value = ', '.join(map(str, value))
                    html += f"""
                        <div>
                            <span>{key.replace('_', ' ').title()}</span>
                            <span class="metric-value">{value}</span>
                        </div>
                    """
                html += "</div>"
        
        # Add recommendations section
        if 'recommendations' in report_data:
            html += """
                    <div class="section">
                        <h2>Recommendations</h2>
            """
            
            for rec in report_data['recommendations']:
                html += f'<div class="recommendation">{rec}</div>'
            
            html += "</div>"
        
        html += """
            </body>
        </html>
        """
        
        return html
    
    def _generate_report_attachments(self, report_data: Dict) -> Dict[str, bytes]:
        """Generate PDF attachments for the report."""
        attachments = {}
        
        # Generate performance trends chart
        fig = self._create_performance_trends(report_data)
        
        # Save as PDF
        pdf_path = Path("reports/temp/performance_trends.pdf")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(str(pdf_path))
        
        # Read PDF content
        with open(pdf_path, 'rb') as f:
            attachments['performance_trends.pdf'] = f.read()
        
        # Clean up temporary file
        pdf_path.unlink()
        
        return attachments
    
    def _create_performance_trends(self, report_data: Dict) -> go.Figure:
        """Create performance trends visualization."""
        # Create figure with secondary y-axis
        fig = make_subplots(rows=2, cols=2,
                           subplot_titles=('Content Performance',
                                         'Engagement Metrics',
                                         'Conversion Funnel',
                                         'Audience Growth'))
        
        # Add traces for each metric category
        self._add_content_traces(fig, report_data, row=1, col=1)
        self._add_engagement_traces(fig, report_data, row=1, col=2)
        self._add_conversion_traces(fig, report_data, row=2, col=1)
        self._add_audience_traces(fig, report_data, row=2, col=2)
        
        # Update layout
        fig.update_layout(height=800, width=1200,
                         showlegend=True,
                         title_text="Performance Trends")
        
        return fig
    
    def _add_content_traces(self, fig: go.Figure, data: Dict, row: int, col: int) -> None:
        """Add content performance traces to the figure."""
        metrics = data['metrics'].get('content', {})
        x = pd.date_range(end=pd.Timestamp.now(), periods=7, freq='D')
        
        fig.add_trace(
            go.Scatter(x=x, y=[metrics.get('posts_created', 0)] * 7,
                      name="Posts Created",
                      line=dict(color='blue')),
            row=row, col=col
        )
        
        fig.add_trace(
            go.Scatter(x=x, y=[metrics.get('content_quality_score', 0)] * 7,
                      name="Quality Score",
                      line=dict(color='green')),
            row=row, col=col
        )
    
    def _add_engagement_traces(self, fig: go.Figure, data: Dict, row: int, col: int) -> None:
        """Add engagement metric traces to the figure."""
        metrics = data['metrics'].get('engagement', {})
        x = pd.date_range(end=pd.Timestamp.now(), periods=7, freq='D')
        
        for metric in ['likes', 'comments', 'shares', 'saves']:
            fig.add_trace(
                go.Scatter(x=x, y=[metrics.get(metric, 0)] * 7,
                          name=metric.title(),
                          line=dict(color=self._get_metric_color(metric))),
                row=row, col=col
            )
    
    def _add_conversion_traces(self, fig: go.Figure, data: Dict, row: int, col: int) -> None:
        """Add conversion funnel traces to the figure."""
        metrics = data['metrics'].get('conversion', {})
        stages = ['awareness', 'consideration', 'action', 'retention']
        values = [metrics.get(f'{stage}_rate', 0) for stage in stages]
        
        fig.add_trace(
            go.Funnel(y=stages, x=values,
                      name="Conversion Funnel"),
            row=row, col=col
        )
    
    def _add_audience_traces(self, fig: go.Figure, data: Dict, row: int, col: int) -> None:
        """Add audience growth traces to the figure."""
        metrics = data['metrics'].get('audience', {})
        x = pd.date_range(end=pd.Timestamp.now(), periods=7, freq='D')
        
        fig.add_trace(
            go.Scatter(x=x, y=[metrics.get('follower_growth', 0)] * 7,
                      name="Follower Growth",
                      line=dict(color='purple')),
            row=row, col=col
        )
    
    @staticmethod
    def _get_metric_color(metric: str) -> str:
        """Get color for metric visualization."""
        colors = {
            'likes': 'red',
            'comments': 'blue',
            'shares': 'green',
            'saves': 'orange'
        }
        return colors.get(metric, 'gray')
    
    @staticmethod
    def _get_metric_status(performance: float) -> str:
        """Get status class based on performance value."""
        if performance >= 90:
            return 'excellent'
        elif performance >= 70:
            return 'good'
        elif performance >= 50:
            return 'warning'
        else:
            return 'poor'
    
    def _send_email(self, msg: MIMEMultipart) -> None:
        """Send email using SMTP."""
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], 
                            self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(
                    self.email_config['username'],
                    self.email_config['password']
                )
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
