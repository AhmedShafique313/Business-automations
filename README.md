# Design Gaga Automation System

A comprehensive automation system for Design Gaga's business operations, including real estate lead generation, customer outreach, and task management.

## Features

- Real estate listing monitoring
- Agent lead generation
- Automated cold calling
- Email outreach campaigns
- Social media management
- Task tracking via Asana
- Google My Business optimization

## Prerequisites

- Python 3.10 or higher
- Chrome/Chromium (for web automation)
- Google Cloud Platform account (for Google My Business)
- Asana account
- OpenAI API key
- Twilio account (optional, for voice calls)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/designgaga/automation.git
   cd automation
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up configuration:
   ```bash
   cp config/default_config.json.example config/default_config.json
   # Edit config/default_config.json with your settings
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

## Configuration

The system uses a hierarchical configuration system with the following precedence:
1. Environment variables
2. Configuration file (`config/default_config.json`)
3. Default values

### Required Configuration

- Company details in `config/default_config.json`:
  ```json
  {
    "company": {
      "name": "Your Company",
      "website": "https://example.com",
      "phone": "+1234567890",
      "business_type": "design",
      "location": "City"
    }
  }
  ```

- API credentials in `.env`:
  ```bash
  OPENAI_API_KEY=your_openai_key
  ASANA_ACCESS_TOKEN=your_asana_token
  ASANA_WORKSPACE_GID=your_workspace_id
  TWILIO_ACCOUNT_SID=your_twilio_sid
  TWILIO_AUTH_TOKEN=your_twilio_token
  ```

## Usage

1. Start the main automation system:
   ```bash
   python main.py
   ```

2. Run specific tasks:
   ```bash
   python run_agents.py  # Run agent discovery
   python social_media_manager.py  # Run social media tasks
   python task_executor.py  # Run scheduled tasks
   ```

3. Monitor the system:
   ```bash
   tail -f logs/business_generator.log  # View business generator logs
   tail -f logs/task_executor.log  # View task executor logs
   ```

## Project Structure

```
.
├── config/                 # Configuration files
├── templates/             # Email and message templates
├── logs/                  # Log files
├── data/                  # Data storage
├── models/               # AI model files
├── tests/                # Test files
├── utils/                # Utility functions
├── main.py              # Main entry point
├── business_generator.py # Business generation logic
├── task_executor.py     # Task execution and scheduling
├── config_manager.py    # Configuration management
└── requirements.txt     # Python dependencies
```

## Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

Run specific test files:
```bash
python -m pytest test_business_system.py -v
python -m pytest test_content_creation.py -v
```

## Logging

The system uses JSON-formatted logging with the following log files:
- `logs/business_generator.log`: Business generation activities
- `logs/task_executor.log`: Task execution and scheduling
- `logs/asana_manager.log`: Asana integration
- `logs/social_media.log`: Social media activities

## Optional Features

The system supports several optional features that can be enabled in the configuration:

1. Voice Commands:
   ```json
   "features": {
     "voice_commands": {
       "enabled": true,
       "language": "en-US"
     }
   }
   ```

2. Web Automation:
   ```json
   "features": {
     "web_automation": {
       "enabled": true,
       "headless": true
     }
   }
   ```

3. Google Integration:
   ```json
   "features": {
     "google_integration": {
       "enabled": true,
       "auto_post": true
     }
   }
   ```

## Error Handling

The system implements comprehensive error handling:
- Automatic retries for API calls
- Rate limiting for external services
- Fallback behaviors for missing dependencies
- Detailed error logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support, contact:
- Email: support@designgaga.com
- Website: https://designgaga.com/support