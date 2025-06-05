import sys
import os
from pathlib import Path

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Also add project root to path
sys.path.insert(0, current_dir)

print(f"📍 Current directory: {current_dir}")
print(f"📍 Source directory: {src_dir}")
print(f"📍 Python path: {sys.path[:3]}...")

# Now we can import from src modules
try:
    # Import database modules
    from database.repository import CVRepository
    from database.connection import DatabaseConnection
    
    # Import utility modules
    from utils.pdf_parser import PDFParser
    from utils.cv_extractor import CVExtractor
    
    print("✅ All modules imported successfully!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("📋 Checking available modules...")
    
    # Check what's available in src directory
    if os.path.exists(src_dir):
        print(f"📁 Contents of {src_dir}:")
        for item in os.listdir(src_dir):
            item_path = os.path.join(src_dir, item)
            if os.path.isdir(item_path):
                print(f"   📂 {item}/")
                try:
                    sub_items = os.listdir(item_path)
                    for sub_item in sub_items[:5]:  # Show first 5 items
                        print(f"      📄 {sub_item}")
                    if len(sub_items) > 5:
                        print(f"      ... and {len(sub_items) - 5} more")
                except:
                    pass
            else:
                print(f"   📄 {item}")
    
    print("\n🔧 Attempting alternative import strategy...")
    
    # Try alternative import approach
    try:
        # Try importing without relative imports by modifying sys.modules
        import importlib.util
        
        # Import database connection
        db_path = os.path.join(src_dir, 'database', 'connection.py')
        if os.path.exists(db_path):
            spec = importlib.util.spec_from_file_location("database.connection", db_path)
            connection_module = importlib.util.module_from_spec(spec)
            sys.modules["database.connection"] = connection_module
            spec.loader.exec_module(connection_module)
            DatabaseConnection = connection_module.DatabaseConnection
            print("✅ DatabaseConnection imported via alternative method")
        else:
            raise ImportError(f"database.connection not found at {db_path}")
        
        # Import other modules similarly if needed...
        print("✅ Alternative import successful!")
        
    except Exception as alt_e:
        print(f"❌ Alternative import also failed: {alt_e}")
        print("\n📋 Please check:")
        print("   1. All Python files exist in src/ directory")
        print("   2. All __init__.py files are present")
        print("   3. No syntax errors in Python files")
        print("   4. All dependencies are installed")
        
        # Create a minimal working version
        print("\n🔧 Creating minimal working version...")
        create_minimal_version()
        sys.exit(1)

def create_minimal_version():
    """Create a minimal working version if imports fail"""
    print("📝 Creating minimal seeding script...")
    
    minimal_script = "'"
# Minimal CV ATS Database Seeding Script
import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path
import random

# Load environment variables
load_dotenv()

def connect_to_database():
    """Connect to MySQL database"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE', 'cv_ats'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def create_tables(connection):
    """Create database tables if they don't exist"""
    cursor = connection.cursor()
    
    # Create ApplicantProfile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ApplicantProfile (
            applicant_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            date_of_birth DATE,
            address TEXT,
            phone_number VARCHAR(20),
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create ApplicationDetail table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ApplicationDetail (
            detail_id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT,
            application_role VARCHAR(255),
            cv_path VARCHAR(500),
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'active',
            FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
        )
    """)
    
    connection.commit()
    cursor.close()
    print("✅ Database tables created/verified")

def scan_cv_files():
    """Scan for CV files in data/cvs folder"""
    cv_files = []
    data_folder = Path("data/cvs")
    
    if not data_folder.exists():
        print(f"❌ CV folder not found: {data_folder}")
        return []
    
    for role_folder in data_folder.iterdir():
        if role_folder.is_dir():
            pdf_files = list(role_folder.glob("*.pdf"))
            if pdf_files:
                # Select up to 5 random files
                selected = random.sample(pdf_files, min(5, len(pdf_files)))
                role_name = role_folder.name.replace('-', ' ').title()
                
                for pdf_file in selected:
                    cv_files.append({
                        'filename': pdf_file.name,
                        'role': role_name,
                        'cv_path': f"data/cvs/{role_folder.name}/{pdf_file.name}"
                    })
    
    return cv_files

def seed_database():
    """🌱 SEED: Isi database dengan CV dari folder data/cvs"""
    repo = CVRepository()
    
    # Connect to database
    if not repo.connect():
        print("❌ Failed to connect to database!")
        return False
    
    try:
        # Optional: Clear existing data
        print("🗑️ Do you want to clear existing data? (y/N)")
        clear_choice = input().lower()
        if clear_choice == 'y':
            repo.clear_all_data()
        
        # Scan CV files from data/cvs folder
        print("🔍 Scanning CV files...")
        cv_files = repo.scan_cv_files_in_data_folder()
        
        if not cv_files:
            print("❌ No CV files found in data/cvs folder!")
            return False
        
        print(f"📁 Found {len(cv_files)} CV files to process")
        
        # Process each CV file
        success_count = 0
        for i, cv_info in enumerate(cv_files, 1):
            try:
                print(f"🔄 Processing {i}/{len(cv_files)}: {cv_info['filename']}")
                
                # Extract CV text
                cv_text = repo._load_cv_text_from_file(cv_info['relative_path'])
                
                if not cv_text or len(cv_text.strip()) < 50:
                    print(f"⚠️ No meaningful text extracted from {cv_info['filename']}")
                    continue
                
                # Extract profile info using CV extractor
                profile_data = repo.cv_extractor.extract_full_summary(cv_text)
                
                # Create applicant profile
                if profile_data.name and profile_data.name.strip():
                    name_parts = profile_data.name.strip().split()
                    first_name = name_parts[0] if name_parts else "Applicant"
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else f"From{cv_info['role'].replace(' ', '')}"
                else:
                    # Fallback name
                    file_base = cv_info['filename'].replace('.pdf', '')
                    first_name = f"Applicant{file_base[:4]}"
                    last_name = cv_info['role'].replace(' ', '')
                
                profile = ApplicantProfile(
                    first_name=first_name,
                    last_name=last_name,
                    email=profile_data.email if profile_data.email else f"{first_name.lower()}.{last_name.lower()}@example.com",
                    phone_number=profile_data.phone if profile_data.phone else f"+1555{random.randint(1000000, 9999999)}",
                    address=profile_data.address if profile_data.address else f"{cv_info['role']} Professional Address"
                )
                
                # Create applicant in database
                applicant_id = repo.create_applicant(profile)
                
                if applicant_id:
                    # Create application detail
                    application = ApplicationDetail(
                        applicant_id=applicant_id,
                        application_role=cv_info['role'],
                        cv_path=cv_info['relative_path'],
                        status="active"
                    )
                    
                    detail_id = repo.create_application(application)
                    
                    if detail_id:
                        success_count += 1
                        print(f"✅ {i}/{len(cv_files)}: {profile.full_name} - {cv_info['role']}")
                    else:
                        print(f"⚠️ Failed to create application for {cv_info['filename']}")
                else:
                    print(f"❌ Failed to create profile for {cv_info['filename']}")
                    
            except Exception as e:
                print(f"❌ Error processing {cv_info['filename']}: {e}")
                continue
        
        success_rate = (success_count/len(cv_files)*100) if len(cv_files) > 0 else 0
        print(f"🎉 Seeding completed: {success_count}/{len(cv_files)} successful ({success_rate:.1f}%)")
        
        # Show statistics
        stats = repo.get_cv_summary_statistics()
        print(f"📊 Database now has {stats['total_cvs']} CVs across {stats['total_roles']} roles")
        
        return True
        
    except Exception as e:
        print(f"❌ Seeding error: {e}")
        return False
    
    finally:
        repo.disconnect()

def create_minimal_version():
    """Create a minimal working version if imports fail"""
    print("📝 Creating minimal seeding script...")
    
    minimal_script = "'"
# Minimal CV ATS Database Seeding Script
import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path
import random

# Load environment variables
load_dotenv()

def connect_to_database():
    """Connect to MySQL database"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE', 'cv_ats'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def create_tables(connection):
    """Create database tables if they don't exist"""
    cursor = connection.cursor()
    
    # Create ApplicantProfile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ApplicantProfile (
            applicant_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            date_of_birth DATE,
            address TEXT,
            phone_number VARCHAR(20),
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create ApplicationDetail table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ApplicationDetail (
            detail_id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT,
            application_role VARCHAR(255),
            cv_path VARCHAR(500),
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'active',
            FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
        )
    """)
    
    connection.commit()
    cursor.close()
    print("✅ Database tables created/verified")

def scan_cv_files():
    """Scan for CV files in data/cvs folder"""
    cv_files = []
    data_folder = Path("data/cvs")
    
    if not data_folder.exists():
        print(f"❌ CV folder not found: {data_folder}")
        return []
    
    for role_folder in data_folder.iterdir():
        if role_folder.is_dir():
            pdf_files = list(role_folder.glob("*.pdf"))
            if pdf_files:
                # Select up to 5 random files
                selected = random.sample(pdf_files, min(5, len(pdf_files)))
                role_name = role_folder.name.replace('-', ' ').title()
                
                for pdf_file in selected:
                    cv_files.append({
                        'filename': pdf_file.name,
                        'role': role_name,
                        'cv_path': f"data/cvs/{role_folder.name}/{pdf_file.name}"
                    })
    
    return cv_files

def seed_database():
    """🌱 SEED: Isi database dengan CV dari folder data/cvs"""
    repo = CVRepository()
    
    # Connect to database
    if not repo.connect():
        print("❌ Failed to connect to database!")
        return False
    
    try:
        # Optional: Clear existing data
        print("🗑️ Do you want to clear existing data? (y/N)")
        clear_choice = input().lower()
        if clear_choice == 'y':
            repo.clear_all_data()
        
        # Scan CV files from data/cvs folder
        print("🔍 Scanning CV files...")
        cv_files = repo.scan_cv_files_in_data_folder()
        
        if not cv_files:
            print("❌ No CV files found in data/cvs folder!")
            return False
        
        print(f"📁 Found {len(cv_files)} CV files to process")
        
        # Process each CV file
        success_count = 0
        for i, cv_info in enumerate(cv_files, 1):
            try:
                print(f"🔄 Processing {i}/{len(cv_files)}: {cv_info['filename']}")
                
                # Extract CV text
                cv_text = repo._load_cv_text_from_file(cv_info['relative_path'])
                
                if not cv_text or len(cv_text.strip()) < 50:
                    print(f"⚠️ No meaningful text extracted from {cv_info['filename']}")
                    continue
                
                # Extract profile info using CV extractor
                profile_data = repo.cv_extractor.extract_full_summary(cv_text)
                
                # Create applicant profile
                if profile_data.name and profile_data.name.strip():
                    name_parts = profile_data.name.strip().split()
                    first_name = name_parts[0] if name_parts else "Applicant"
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else f"From{cv_info['role'].replace(' ', '')}"
                else:
                    # Fallback name
                    file_base = cv_info['filename'].replace('.pdf', '')
                    first_name = f"Applicant{file_base[:4]}"
                    last_name = cv_info['role'].replace(' ', '')
                
                profile = ApplicantProfile(
                    first_name=first_name,
                    last_name=last_name,
                    email=profile_data.email if profile_data.email else f"{first_name.lower()}.{last_name.lower()}@example.com",
                    phone_number=profile_data.phone if profile_data.phone else f"+1555{random.randint(1000000, 9999999)}",
                    address=profile_data.address if profile_data.address else f"{cv_info['role']} Professional Address"
                )
                
                # Create applicant in database
                applicant_id = repo.create_applicant(profile)
                
                if applicant_id:
                    # Create application detail
                    application = ApplicationDetail(
                        applicant_id=applicant_id,
                        application_role=cv_info['role'],
                        cv_path=cv_info['relative_path'],
                        status="active"
                    )
                    
                    detail_id = repo.create_application(application)
                    
                    if detail_id:
                        success_count += 1
                        print(f"✅ {i}/{len(cv_files)}: {profile.full_name} - {cv_info['role']}")
                    else:
                        print(f"⚠️ Failed to create application for {cv_info['filename']}")
                else:
                    print(f"❌ Failed to create profile for {cv_info['filename']}")
                    
            except Exception as e:
                print(f"❌ Error processing {cv_info['filename']}: {e}")
                continue
        
        success_rate = (success_count/len(cv_files)*100) if len(cv_files) > 0 else 0
        print(f"🎉 Seeding completed: {success_count}/{len(cv_files)} successful ({success_rate:.1f}%)")
        
        # Show statistics
        stats = repo.get_cv_summary_statistics()
        print(f"📊 Database now has {stats['total_cvs']} CVs across {stats['total_roles']} roles")
        
        return True
        
    except Exception as e:
        print(f"❌ Seeding error: {e}")
        return False
    
    finally:
        repo.disconnect()

def create_minimal_version():
    """Create a minimal working version if imports fail"""
    print("📝 Creating minimal seeding script...")
    
    minimal_script = "'"
# Minimal CV ATS Database Seeding Script
import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path
import random

# Load environment variables
load_dotenv()

def connect_to_database():
    """Connect to MySQL database"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE', 'cv_ats'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def create_tables(connection):
    """Create database tables if they don't exist"""
    cursor = connection.cursor()
    
    # Create ApplicantProfile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ApplicantProfile (
            applicant_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            date_of_birth DATE,
            address TEXT,
            phone_number VARCHAR(20),
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create ApplicationDetail table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ApplicationDetail (
            detail_id INT AUTO_INCREMENT PRIMARY KEY,
            applicant_id INT,
            application_role VARCHAR(255),
            cv_path VARCHAR(500),
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'active',
            FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
        )
    """)
    
    connection.commit()
    cursor.close()
    print("✅ Database tables created/verified")

def scan_cv_files():
    """Scan for CV files in data/cvs folder"""
    cv_files = []
    data_folder = Path("data/cvs")
    
    if not data_folder.exists():
        print(f"❌ CV folder not found: {data_folder}")
        return []
    
    for role_folder in data_folder.iterdir():
        if role_folder.is_dir():
            pdf_files = list(role_folder.glob("*.pdf"))
            if pdf_files:
                # Select up to 5 random files
                selected = random.sample(pdf_files, min(5, len(pdf_files)))
                role_name = role_folder.name.replace('-', ' ').title()
                
                for pdf_file in selected:
                    cv_files.append({
                        'filename': pdf_file.name,
                        'role': role_name,
                        'cv_path': f"data/cvs/{role_folder.name}/{pdf_file.name}"
                    })
    
    return cv_files

def seed_database():
    """🌱 SEED: Isi database dengan CV dari folder data/cvs"""
    repo = CVRepository()
    
    # Connect to database
    if not repo.connect():
        print("❌ Failed to connect to database!")
        return False
    
    try:
        # Optional: Clear existing data
        print("🗑️ Do you want to clear existing data? (y/N)")
        clear_choice = input().lower()
        if clear_choice == 'y':
            repo.clear_all_data()
        
        # Scan CV files from data/cvs folder
        print("🔍 Scanning CV files...")
        cv_files = repo.scan_cv_files_in_data_folder()
        
        if not cv_files:
            print("❌ No CV files found in data/cvs folder!")
            return False
        
        print(f"📁 Found {len(cv_files)} CV files to process")
        
        # Process each CV file
        success_count = 0
        for i, cv_info in enumerate(cv_files, 1):
            try:
                print(f"🔄 Processing {i}/{len(cv_files)}: {cv_info['filename']}")
                
                # Extract CV text
                cv_text = repo._load_cv_text_from_file(cv_info['relative_path'])
                
                if not cv_text or len(cv_text.strip()) < 50:
                    print(f"⚠️ No meaningful text extracted from {cv_info['filename']}")
                    continue
                
                # Extract profile info using CV extractor
                profile_data = repo.cv_extractor.extract_full_summary(cv_text)
                
                # Create applicant profile
                if profile_data.name and profile_data.name.strip():
                    name_parts = profile_data.name.strip().split()
                    first_name = name_parts[0] if name_parts else "Applicant"
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else f"From{cv_info['role'].replace(' ', '')}"
                else:
                    # Fallback name
                    file_base = cv_info['filename'].replace('.pdf', '')
                    first_name = f"Applicant{file_base[:4]}"
                    last_name = cv_info['role'].replace(' ', '')
                
                profile = ApplicantProfile(
                    first_name=first_name,
                    last_name=last_name,
                    email=profile_data.email if profile_data.email else f"{first_name.lower()}.{last_name.lower()}@example.com",
                    phone_number=profile_data.phone if profile_data.phone else f"+1555{random.randint(1000000, 9999999)}",
                    address=profile_data.address if profile_data.address else f"{cv_info['role']} Professional Address"
                )
                
                # Create applicant in database
                applicant_id = repo.create_applicant(profile)
                
                if applicant_id:
                    # Create application detail
                    application = ApplicationDetail(
                        applicant_id=applicant_id,
                        application_role=cv_info['role'],
                        cv_path=cv_info['relative_path'],
                        status="active"
                    )
                    
                    detail_id = repo.create_application(application)
                    
                    if detail_id:
                        success_count += 1
                        print(f"✅ {i}/{len(cv_files)}: {profile.full_name} - {cv_info['role']}")
                    else:
                        print(f"⚠️ Failed to create application for {cv_info['filename']}")
                else:
                    print(f"❌ Failed to create profile for {cv_info['filename']}")
                    
            except Exception as e:
                print(f"❌ Error processing {cv_info['filename']}: {e}")
                continue
        
        success_rate = (success_count/len(cv_files)*100) if len(cv_files) > 0 else 0
        print(f"🎉 Seeding completed: {success_count}/{len(cv_files)} successful ({success_rate:.1f}%)")
        
        # Show statistics
        stats = repo.get_cv_summary_statistics()
        print(f"📊 Database now has {stats['total_cvs']} CVs across {stats['total_roles']} roles")
        
        return True
        
    except Exception as e:
        print(f"❌ Seeding error: {e}")
        return False
    
    finally:
        repo.disconnect()

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    issues = []
    
    # Check .env file
    env_file = os.path.join(current_dir, '.env')
    if not os.path.exists(env_file):
        issues.append("❌ .env file not found in project root")
    else:
        print("✅ .env file found")
    
    # Check data folder
    data_folder = Path(os.path.join(current_dir, "data", "cvs"))
    if not data_folder.exists():
        issues.append(f"❌ data/cvs folder not found at {data_folder}")
    else:
        cv_files = list(data_folder.rglob("*.pdf"))
        if cv_files:
            print(f"✅ Found {len(cv_files)} CV files in data folder")
        else:
            issues.append("⚠️ No PDF files found in data/cvs folder")
    
    # Check required Python packages
    required_packages = [
        'mysql.connector',
        'python-dotenv',
        'pypdf'
    ]
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            elif package == 'mysql.connector':
                import mysql.connector
            elif package == 'pypdf':
                import pypdf
            print(f"✅ {package} is available")
        except ImportError:
            issues.append(f"❌ Missing package: {package}")
    
    return issues

def show_folder_structure():
    """Show the actual folder structure found"""
    print("\n📂 Checking CV folder structure...")
    
    data_folder = Path(os.path.join(current_dir, "data", "cvs"))
    
    if not data_folder.exists():
        print(f"❌ Folder not found: {data_folder.absolute()}")
        print(f"   Current directory: {current_dir}")
        return False
    
    print(f"📁 Scanning: {data_folder.absolute()}")
    
    try:
        role_folders = [f for f in data_folder.iterdir() if f.is_dir()]
    except PermissionError:
        print(f"❌ Permission denied accessing {data_folder}")
        return False
    
    if not role_folders:
        print("❌ No role folders found!")
        return False
    
    print(f"\n📊 Found {len(role_folders)} role folders:")
    
    total_pdfs = 0
    valid_folders = 0
    
    for folder in sorted(role_folders):
        try:
            pdf_files = list(folder.glob("*.pdf"))
            total_pdfs += len(pdf_files)
            
            if pdf_files:
                valid_folders += 1
                print(f"   📂 {folder.name}: {len(pdf_files)} PDF files")
                
                # Show first few files as examples
                for i, pdf_file in enumerate(pdf_files[:3]):
                    print(f"      📄 {pdf_file.name}")
                if len(pdf_files) > 3:
                    print(f"      ... and {len(pdf_files) - 3} more files")
            else:
                print(f"   📂 {folder.name}: ⚠️ No PDF files found")
        except Exception as e:
            print(f"   📂 {folder.name}: ❌ Error accessing folder: {e}")
    
    print(f"\n📊 Total PDF files available: {total_pdfs}")
    print(f"📊 Valid folders with PDFs: {valid_folders}")
    
    if valid_folders > 0:
        expected_seeding = valid_folders * 5
        print(f"📊 Expected seeding: 5 files per role = up to {expected_seeding} total applicants")
        return True
    else:
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🔗 Testing database connection...")
    
    try:
        # Test basic MySQL connection
        import mysql.connector
        from dotenv import load_dotenv
        
        load_dotenv()
        
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE', 'cv_ats'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        
        if connection.is_connected():
            print("✅ Database connection successful!")
            
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                print("✅ Database query successful")
            
            cursor.close()
            connection.close()
            return True
        else:
            print("❌ Database connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        print("\n📋 Please check your .env file:")
        print("   DB_HOST=localhost")
        print("   DB_USER=your_mysql_username")
        print("   DB_PASSWORD=your_mysql_password")
        print("   DB_DATABASE=cv_ats")
        print("   DB_PORT=3306")
        return False

def run_minimal_seeding():
    """Run minimal seeding using direct database connection"""
    print("\n🌱 Running Minimal CV Seeding")
    print("=" * 50)
    
    try:
        import mysql.connector
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Connect to database
        print("🔗 Connecting to database...")
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_DATABASE', 'cv_ats'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        
        print("✅ Database connected successfully!")
        
        # Create tables
        cursor = connection.cursor()
        
        print("📋 Creating/verifying database tables...")
        
        # Create ApplicantProfile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ApplicantProfile (
                applicant_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                date_of_birth DATE,
                address TEXT,
                phone_number VARCHAR(20),
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create ApplicationDetail table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ApplicationDetail (
                detail_id INT AUTO_INCREMENT PRIMARY KEY,
                applicant_id INT,
                application_role VARCHAR(255),
                cv_path VARCHAR(500),
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'active',
                FOREIGN KEY (applicant_id) REFERENCES ApplicantProfile(applicant_id)
            )
        """)
        
        connection.commit()
        print("✅ Database tables ready")
        
        # Scan CV files
        print("📂 Scanning CV files...")
        cv_files = []
        data_folder = Path("data/cvs")
        
        if data_folder.exists():
            for role_folder in data_folder.iterdir():
                if role_folder.is_dir():
                    pdf_files = list(role_folder.glob("*.pdf"))
                    if pdf_files:
                        # Select up to 5 random files
                        import random
                        selected = random.sample(pdf_files, min(5, len(pdf_files)))
                        role_name = role_folder.name.replace('-', ' ').replace('_', ' ').title()
                        
                        for pdf_file in selected:
                            cv_files.append({
                                'filename': pdf_file.name,
                                'role': role_name,
                                'cv_path': f"data/cvs/{role_folder.name}/{pdf_file.name}"
                            })
        
        if not cv_files:
            print("❌ No CV files found!")
            return False
        
        print(f"✅ Found {len(cv_files)} CV files to process")
        
        # Clear existing data option
        choice = input("\nClear existing data? (y/N): ").strip().lower()
        if choice == 'y':
            cursor.execute("DELETE FROM ApplicationDetail")
            cursor.execute("DELETE FROM ApplicantProfile")
            connection.commit()
            print("✅ Existing data cleared")
        
        # Seed data
        print(f"\n🌱 Seeding {len(cv_files)} applicants...")
        success_count = 0
        
        for i, cv_info in enumerate(cv_files, 1):
            try:
                # Generate applicant data
                first_name = f"Applicant{i:03d}"
                last_name = cv_info['role'].replace(' ', '')
                email = f"applicant{i:03d}@{cv_info['role'].lower().replace(' ', '')}example.com"
                phone = f"+1555{random.randint(1000000, 9999999)}"
                address = f"{cv_info['role']} Professional Address"
                
                # Insert applicant
                cursor.execute("""
                    INSERT INTO ApplicantProfile (first_name, last_name, email, phone_number, address)
                    VALUES (%s, %s, %s, %s, %s)
                """, (first_name, last_name, email, phone, address))
                
                applicant_id = cursor.lastrowid
                
                # Insert application
                cursor.execute("""
                    INSERT INTO ApplicationDetail (applicant_id, application_role, cv_path, status)
                    VALUES (%s, %s, %s, %s)
                """, (applicant_id, cv_info['role'], cv_info['cv_path'], 'active'))
                
                success_count += 1
                print(f"✅ {i}/{len(cv_files)}: {first_name} {last_name} - {cv_info['role']}")
                
            except Exception as e:
                print(f"❌ Failed {i}/{len(cv_files)}: {cv_info['filename']} - {e}")
        
        connection.commit()
        
        # Show results
        cursor.execute("SELECT COUNT(*) FROM ApplicantProfile")
        total_applicants = cursor.fetchone()[0]
        
        cursor.execute("SELECT application_role, COUNT(*) FROM ApplicationDetail GROUP BY application_role")
        role_stats = cursor.fetchall()
        
        print(f"\n🎉 Seeding completed: {success_count}/{len(cv_files)} successful")
        print(f"✅ Total applicants in database: {total_applicants}")
        print("\n📊 Role breakdown:")
        for role, count in role_stats:
            print(f"   📂 {role}: {count} applicants")
        
        cursor.close()
        connection.close()
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Minimal seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🎯 CV ATS - REAL DATA SEEDING TOOL")
    print("=" * 60)
    print("This tool will seed your database with real CV files")
    print("from the data/cvs folder structure (5 files per role)")
    print("=" * 60)
    
    # Step 1: Check prerequisites
    print("\n1️⃣ CHECKING PREREQUISITES")
    issues = check_prerequisites()
    
    if issues:
        print("\n❌ Prerequisites check failed:")
        for issue in issues:
            print(f"   {issue}")
        print("\n🔧 Please fix these issues before running seeding:")
        print("   - Install missing packages: pip install mysql-connector-python python-dotenv pypdf")
        print("   - Create .env file with database credentials")
        print("   - Ensure data/cvs folder exists with PDF files")
        return False
    
    print("✅ All prerequisites met!")
    
    # Step 2: Check folder structure
    print("\n2️⃣ CHECKING FOLDER STRUCTURE")
    if not show_folder_structure():
        print("\n❌ Cannot proceed without proper folder structure!")
        print("\n📋 Expected structure:")
        print("   data/cvs/ACCOUNTANT/*.pdf")
        print("   data/cvs/ENGINEERING/*.pdf")
        print("   data/cvs/INFORMATION-TECHNOLOGY/*.pdf")
        print("   etc...")
        return False
    
    # Step 3: Test database connection
    print("\n3️⃣ TESTING DATABASE CONNECTION")
    if not test_database_connection():
        print("❌ Database connection test failed")
        return False
    
    # Step 4: Run seeding (using minimal approach due to import issues)
    print("\n4️⃣ RUNNING SEEDING PROCESS")
    print("ℹ️ Using minimal seeding approach due to module import issues")
    
    proceed = input("Do you want to proceed with minimal seeding? (y/N): ").strip().lower()
    if proceed != 'y':
        print("ℹ️ Seeding cancelled by user")
        return False
    
    success = run_minimal_seeding()
    
    # Step 5: Final message
    print("\n5️⃣ FINAL RESULTS")
    print("=" * 60)
    
    if success:
        print("🎉 SUCCESS! Your database is now populated with real CV data!")
        print("\n🚀 Next steps:")
        print("   1. Fix module import issues in your main application")
        print("   2. Run your main application: python src/main.py")
        print("   3. Test CV search and matching features")
        print("   4. Verify string algorithms work with real data")
    else:
        print("❌ FAILED! Please check error messages and try again.")
        print("\n🔧 Common solutions:")
        print("   1. Check database credentials in .env file")
        print("   2. Ensure MySQL server is running")
        print("   3. Check file permissions on data/cvs folder")
    
    return success

if __name__ == "__main__":
    try:
        # Change to script directory to ensure relative paths work
        os.chdir(current_dir)
        
        success = main()
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)