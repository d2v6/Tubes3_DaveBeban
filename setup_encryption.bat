@echo off
REM Setup script for CV ATS Encryption System (Windows)

echo 🔐 CV ATS Encryption System Setup
echo ==================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo 📥 Installing requirements...
pip install -r requirements.txt

REM Check database connection
echo 🔗 Testing database connection...
python -c "import os; from dotenv import load_dotenv; load_dotenv(); import mysql.connector; connection = mysql.connector.connect(host=os.getenv('DB_HOST', 'localhost'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME', 'cv_ats')); print('✅ Database connection successful'); connection.close()" 2>nul || echo ❌ Database connection failed - check .env file and MySQL server

REM Test encryption system
echo 🧪 Testing encryption system...
python encryption_manager.py --test

echo.
echo ✅ Setup completed!
echo.
echo 🎯 Next steps:
echo    1. Run: python encryption_manager.py --status
echo    2. To migrate existing data: python encryption_manager.py --migrate
echo    3. To run the application: flet run src/main.py
echo.
echo 🔐 Encryption Commands:
echo    - Enable encryption: python encryption_manager.py --enable
echo    - Disable encryption: python encryption_manager.py --disable
echo    - Show status: python encryption_manager.py --status
echo    - Create demo data: python encryption_manager.py --demo
echo    - Run benchmarks: python encryption_manager.py --benchmark

pause
