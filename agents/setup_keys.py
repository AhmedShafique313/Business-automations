import os
import keyring
import getpass
from pathlib import Path

def setup_api_keys():
    """Set up all required API keys securely."""
    keys = {
        'GOOGLE_API_KEY': {
            'description': 'Google API Key (for search and maps)',
            'url': 'https://console.cloud.google.com/apis/credentials',
            'instructions': '''
1. Go to Google Cloud Console
2. Create a new project or select existing
3. Enable required APIs:
   - Google Custom Search API
   - Google Maps JavaScript API
   - Google Places API
4. Create credentials (API key)
5. Add restrictions if needed'''
        },
        'GOOGLE_CSE_ID': {
            'description': 'Google Custom Search Engine ID',
            'url': 'https://programmablesearchengine.google.com/controlpanel/create',
            'instructions': '''
1. Go to Programmable Search Engine
2. Click "Add" to create a new search engine
3. Configure your search engine settings
4. Get your Search Engine ID (cx)'''
        },
        'ASANA_ACCESS_TOKEN': {
            'description': 'Asana Personal Access Token',
            'url': 'https://app.asana.com/0/developer-console',
            'instructions': '''
1. Go to Asana Developer Console
2. Click "Create New Token"
3. Name your token
4. Copy the token immediately'''
        },
        'GOOGLE_MAPS_API_KEY': {
            'description': 'Google Maps API Key',
            'url': 'https://console.cloud.google.com/apis/credentials',
            'instructions': '''
1. Use same key as GOOGLE_API_KEY or create new
2. Enable Maps JavaScript API
3. Add HTTP referrers restriction'''
        }
    }

    # Create .env file
    env_path = Path(__file__).parent / '.env'
    existing_env = {}
    
    # Read existing .env if it exists
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    existing_env[key] = value.strip('"').strip("'")

    # Get keys from user
    new_env = {}
    for key, info in keys.items():
        print(f"\n{'-'*50}")
        print(f"Setting up: {info['description']}")
        print(f"Get it here: {info['url']}")
        print("\nInstructions:")
        print(info['instructions'])
        
        # Check if key exists in keyring
        existing = keyring.get_password('design_gaga', key)
        if existing:
            use_existing = input(f"\nExisting {key} found. Use it? (y/n): ").lower() == 'y'
            if use_existing:
                new_env[key] = existing
                continue

        # Get new key
        value = getpass.getpass(f"\nEnter {key} (input will be hidden): ")
        if value:
            keyring.set_password('design_gaga', key, value)
            new_env[key] = value

    # Update .env file
    with open(env_path, 'w') as f:
        for key, value in {**existing_env, **new_env}.items():
            f.write(f'{key}="{value}"\n')

    # Create a shell script to export variables
    with open(Path(__file__).parent / 'export_keys.sh', 'w') as f:
        f.write('#!/bin/bash\n\n')
        for key, value in new_env.items():
            f.write(f'export {key}="{value}"\n')
    
    # Make the shell script executable
    os.chmod(Path(__file__).parent / 'export_keys.sh', 0o755)

    print("\nAPI keys have been set up successfully!")
    print("To load the environment variables, run:")
    print("source ./export_keys.sh")

if __name__ == "__main__":
    setup_api_keys()
