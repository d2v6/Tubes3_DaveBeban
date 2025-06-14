import os
from datetime import datetime, date
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.database.connection import DatabaseConnection
    from src.utils.pdf_parser import PDFParser
    from src.utils.cv_extractor import CVExtractor
    from src.models.database_models import ApplicantProfile, ApplicationDetail
except ImportError:
    from database.connection import DatabaseConnection
    from utils.pdf_parser import PDFParser
    from utils.cv_extractor import CVExtractor
    from models.database_models import ApplicantProfile, ApplicationDetail

def seed_database():
    """Create MySQL database and seed with extracted CV data"""
    
    try:
        # Connect to database
        db = DatabaseConnection()
        if not db.connect():
            print("❌ Failed to connect to MySQL database")
            return False
        
        print("✅ Connected to MySQL database")
        
        # Initialize extractors
        pdf_parser = PDFParser()
        cv_extractor = CVExtractor()
        
        # Seed from data folder
        seed_from_data_folder(db, pdf_parser, cv_extractor)
        
        # Close connection
        db.disconnect()
        
        print("✅ Database seeding completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def find_pdf_files_recursive(base_path: str) -> list:
    """Recursively find all PDF files in directory structure"""
    pdf_files = []
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"⚠️ Base path '{base_path}' does not exist")
        return pdf_files
    
    print(f"🔍 Scanning directory: {base_path.absolute()}")
    
    # Walk through all subdirectories
    for file_path in base_path.rglob("*.pdf"):
        if file_path.is_file():
            # Get relative path from base directory for cv_path
            relative_path = file_path.relative_to(base_path)
            folder_path = str(relative_path.parent) if relative_path.parent != Path('.') else "root"
            
            # Create cv_path that matches your existing database structure
            cv_path = str(relative_path).replace('\\', '/')  # Ensure forward slashes
            
            pdf_files.append({
                'full_path': str(file_path.absolute()),
                'filename': file_path.name,
                'folder_path': folder_path,
                'cv_path': f"data/{cv_path}",  # Add data/ prefix to match your structure
            })
    
    return pdf_files

def seed_from_data_folder(db: DatabaseConnection, pdf_parser: PDFParser, cv_extractor: CVExtractor):
    """Seed database with extracted CV data from ./data folder recursively"""
    
    base_data_path = "./data"
    
    print(f"\n📁 Starting recursive PDF scan from: {os.path.abspath(base_data_path)}")
    
    # Find all PDF files recursively
    pdf_files = find_pdf_files_recursive(base_data_path)
    
    if not pdf_files:
        print("⚠️ No PDF files found in ./data directory")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files")
    
    successful_inserts = 0
    failed_inserts = 0
    
    for pdf_info in pdf_files:
        try:
            print(f"\n📖 Processing: {pdf_info['folder_path']}/{pdf_info['filename']}")
            
            # Extract CV information using CVExtractor
            cv_content=PDFParser.parse_pdf(pdf_info.full_path)
            
            if not cv_content:
                failed_inserts += 1
                continue
            
            # Display extracted information
            print(f"    First Name: {contact_information[0]}")
            print(f"    Last Name: {contact_information[1]}")
            print(f"   📱 Phone: {contact_information[2]}")
            print(f"   🏠 Address: {contact_information[3]}")
            
            
            # Insert applicant profile
            profile_query = """
            INSERT INTO ApplicantProfile 
            (first_name, last_name, phone_number, address, date_of_birth)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            profile_params = (
                applicant_profile.first_name,
                applicant_profile.last_name,
                applicant_profile.email,
                applicant_profile.phone_number,
                applicant_profile.address,
                applicant_profile.date_of_birth
            )
            
            applicant_id = db.execute_insert(profile_query, profile_params)
            
            if applicant_id:
                # Determine role from CV content and folder
                application_role = determine_role_from_cv_content(cv_summary, pdf_info['folder_path'])
                
                # Create ApplicationDetail
                application_query = """
                INSERT INTO ApplicationDetail 
                (applicant_id, application_role, cv_path, applied_date, status)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                application_params = (
                    applicant_id,
                    application_role,
                    pdf_info['cv_path'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'active'
                )
                
                if db.execute_insert(application_query, application_params):
                    successful_inserts += 1
                    print(f"   ✅ Added to database: {applicant_profile.first_name} {applicant_profile.last_name}")
                    print(f"      � CV Path: {pdf_info['cv_path']}")
                    print(f"      � Role: {application_role}")
                    
                    # Optionally, log extracted skills and experience for debugging
                    if cv_summary.skills:
                        print(f"      🔧 Key Skills: {', '.join(cv_summary.skills[:3])}")
                    if cv_summary.experience:
                        latest_exp = cv_summary.experience[0]
                        print(f"      📈 Latest Role: {latest_exp.get('position', 'N/A')}")
                        
                else:
                    failed_inserts += 1
                    print(f"   ❌ Failed to create application detail")
            else:
                failed_inserts += 1
                print(f"   ❌ Failed to create applicant profile")
                
        except Exception as e:
            failed_inserts += 1
            print(f"   ❌ Error processing {pdf_info['filename']}: {e}")
    
    print(f"\n📊 Seeding Summary:")
    print(f"   ✅ Successfully processed: {successful_inserts} CVs")
    print(f"   ❌ Failed to process: {failed_inserts} CVs")

def scan_data_folder():
    """Just scan and display what's in the data folder"""
    
    base_path = "./data"
    
    if not os.path.exists(base_path):
        print(f"❌ Data folder not found: {os.path.abspath(base_path)}")
        print("💡 Create a './data' folder and add PDF files to seed the database")
        return
    
    pdf_files = find_pdf_files_recursive(base_path)
    
    if not pdf_files:
        print(f"📁 Data folder exists but no PDF files found in: {os.path.abspath(base_path)}")
        return
    
    print(f"📂 Data Folder Structure:")
    print(f"Base: {os.path.abspath(base_path)}")
    
    # Group by folder
    folders = {}
    for pdf in pdf_files:
        folder = pdf['folder_path']
        if folder not in folders:
            folders[folder] = []
        folders[folder].append(pdf)
    
    for folder, files in folders.items():
        total_size = sum(f['file_size'] for f in files)
        print(f"\n📁 {folder}/ ({len(files)} files, {total_size:,} bytes)")
        for file_info in files:
            print(f"   📄 {file_info['filename']} → CV Path: {file_info['cv_path']}")

if __name__ == "__main__":
    print("🔍 Scanning ./data folder...")
    scan_data_folder()
    
    print("\n" + "=" * 70)
    
    success = seed_database()
    
    if success:
        print("\n✅ Database seeding successful!")
    else:
        print("\n❌ Database seeding failed!")