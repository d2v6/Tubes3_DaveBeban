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
    print("🗄️ SETTING UP CV ATS DATABASE")
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
            
            # Create applicant_profiles table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS applicant_profiles (
                applicant_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                email VARCHAR(255),
                phone_number VARCHAR(50),
                address TEXT,
                date_of_birth DATE,
                education TEXT,
                experience TEXT,
                skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_table_query)
            print("✅ Table 'applicant_profiles' created/verified")
            
            # Create application_details table  
            create_app_table_query = """
            CREATE TABLE IF NOT EXISTS application_details (
                application_id INT AUTO_INCREMENT PRIMARY KEY,
                applicant_id INT,
                job_title VARCHAR(255),
                job_description TEXT,
                application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'pending',
                FOREIGN KEY (applicant_id) REFERENCES applicant_profiles(applicant_id)
            )
            """
            
            cursor.execute(create_app_table_query)
            print("✅ Table 'application_details' created/verified")
            
            # Show tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("\n📋 Available tables:")
            for table in tables:
                print(f"   📄 {table[0]}")
                
            connection.commit()
            cursor.close()
            connection.close()
            
            print("\n🎉 Database setup completed successfully!")
            return True
            
    except Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Setup Error: {e}")
        return False

def test_database_setup():
    """Test that the database setup worked"""
    print("\n🧪 TESTING DATABASE SETUP")
    print("=" * 50)
    
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'cv_ats'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            print("✅ Connected to cv_ats database")
            
            # Test insert
            test_query = """
            INSERT INTO applicant_profiles (first_name, last_name, email)
            VALUES ('Test', 'User', 'test@example.com')
            """
            cursor.execute(test_query)
            test_id = cursor.lastrowid
            
            # Test select
            cursor.execute("SELECT * FROM applicant_profiles WHERE applicant_id = %s", (test_id,))
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Test record created: {result['first_name']} {result['last_name']}")
                
                # Clean up
                cursor.execute("DELETE FROM applicant_profiles WHERE applicant_id = %s", (test_id,))
                connection.commit()
                print("✅ Test record cleaned up")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run database setup"""
    success = create_database()
    if success:
        success = test_database_setup()
    
    if success:
        print("\n🏆 DATABASE SETUP COMPLETE!")
        print("✅ You can now run encryption tests with database integration.")
    else:
        print("\n⚠️ Database setup had issues. Check MySQL connection settings.")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
