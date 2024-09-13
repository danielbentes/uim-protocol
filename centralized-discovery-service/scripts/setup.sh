#!/bin/bash

# scripts/setup.sh - Script to set up and run the project

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload