#!/bin/bash

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Create necessary directories
mkdir -p config
mkdir -p data
mkdir -p logs

echo "Setup completed successfully!"
