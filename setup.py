import os
import subprocess
import sys
from pathlib import Path

def setup_environment():
    """Setup the project environment"""
    print("Setting up project environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists('venv'):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])
    
    # Activate virtual environment
    if os.name == 'nt':  # Windows
        activate_script = os.path.join('venv', 'Scripts', 'activate')
    else:  # Unix/Linux
        activate_script = os.path.join('venv', 'bin', 'activate')
    
    # Install/upgrade pip
    print("Upgrading pip...")
    subprocess.run([
        os.path.join('venv', 'bin', 'python'), 
        '-m', 'pip', 'install', '--upgrade', 'pip'
    ])
    
    # Install requirements
    print("Installing requirements...")
    subprocess.run([
        os.path.join('venv', 'bin', 'pip'), 
        'install', '-r', 'requirements.txt'
    ])
    
    # Create necessary directories
    dirs = ['logs', 'data', 'config', 'temp']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        print("Creating .env file template...")
        with open('.env', 'w') as f:
            f.write("""# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Asana Configuration
ASANA_ACCESS_TOKEN=your_asana_access_token_here
ASANA_WORKSPACE_GID=your_workspace_gid_here

# Other Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
""")
        print("Please update the .env file with your API keys and configuration.")

if __name__ == "__main__":
    setup_environment()
