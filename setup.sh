#!/bin/bash
# Setup script for CV ATS Encryption System

echo "🔐 CV ATS Encryption System Setup"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/Scripts/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check database connection
echo "🔗 Testing database connection..."
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

try:
    import mysql.connector
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME', 'cv_ats')
    )
    print('✅ Database connection successful')
    connection.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Please check your .env file and MySQL server')
"