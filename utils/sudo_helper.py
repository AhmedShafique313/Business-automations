"""
Helper script for running sudo commands using credentials from .env
"""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def load_credentials():
    """Load credentials from .env file."""
    env_path = Path(__file__).parents[1] / '.env'
    load_dotenv(env_path)
    return os.getenv('SUDO_PASSWORD')

def run_sudo_command(command: list[str]) -> tuple[int, str, str]:
    """Run a sudo command using stored credentials.
    
    Args:
        command: List of command parts (e.g. ['apt-get', 'install', '-y', 'tmux'])
    
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    sudo_password = load_credentials()
    if not sudo_password:
        raise ValueError("SUDO_PASSWORD not found in .env file")
    
    # Construct the full command
    full_command = ['sudo', '-S'] + command
    
    # Run the command
    process = subprocess.Popen(
        full_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send password to stdin
    stdout, stderr = process.communicate(input=f"{sudo_password}\n")
    return process.returncode, stdout, stderr
