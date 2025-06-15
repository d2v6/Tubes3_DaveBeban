#!/usr/bin/env python3
"""
🗄️ DATABASE SETUP for CV ATS
Create the cv_ats database and basic tables for testing
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create the cv_ats database"""
    print("SETTING UP CV ATS DATABASE")
    print("=" * 50)
    
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306)),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("✅ Connected to MySQL server")
            
            # Create database
            database_name = os.getenv('DB_NAME', 'cv_ats')
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
            print(f"✅ Database '{database_name}' created/verified")
            
            # Use the database
            cursor.execute(f"USE {database_name}")
            print(f"✅ Switched to database '{database_name}'")
            
            # Create ApplicantProfile table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS ApplicantProfile (
                applicant_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                date_of_birth DATE,
                address VARCHAR(255),
                phone_number VARCHAR(20)
            )
            """
            
            cursor.execute(create_table_query)
            print("✅ Table 'ApplicantProfile' created/verified")
            
            # Create ApplicationDetail table  
            create_app_table_query = """
            CREATE TABLE IF NOT EXISTS ApplicationDetail (
                detail_id INT AUTO_INCREMENT PRIMARY KEY,
                application_role VARCHAR(100),
                applicant_id INT,
                cv_path TEXT,
                FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
            )
            """
            
            cursor.execute(create_app_table_query)
            print("✅ Table 'ApplicationDetail' created/verified")
                
            connection.commit()
            cursor.close()
            connection.close()
            
            print("✅ Database setup completed successfully!")
            return True
            
    except Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Setup Error: {e}")
        return False

def main():
    """Run database setup"""
    success = create_database()
    if success:
        print("✅ Success")
    else:
        print("❌ Failed")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
