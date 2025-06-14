"""
🔐 ENCRYPTION MANAGER CLI
Command-line tool to manage encryption for CV ATS system

Usage:
    python encryption_manager.py --help
    python encryption_manager.py --test
    python encryption_manager.py --migrate
    python encryption_manager.py --status
    python encryption_manager.py --enable
    python encryption_manager.py --disable
"""

import sys
import os
import argparse

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

try:
    from src.database.encrypted_repository import EncryptedCVRepository
    from src.utils.encryption import test_encryption, CustomEncryption, FieldEncryption
    from src.models.encrypted_models import test_encrypted_models
    from src.models.database_models import ApplicantProfile
except ImportError as e:
    try:
        # Alternative import path
        sys.path.insert(0, os.path.join(current_dir, 'src'))
        from database.encrypted_repository import EncryptedCVRepository
        from utils.encryption import test_encryption, CustomEncryption, FieldEncryption
        from models.encrypted_models import test_encrypted_models
        from models.database_models import ApplicantProfile
    except ImportError as e2:
        print(f"❌ Import error: {e2}")
        print("Please make sure you're running this from the project root directory")
        print("Required modules:")
        print("  - Database connection module")
        print("  - Encryption modules")
        print("  - Model definitions")
        sys.exit(1)


def test_encryption_system():
    """🧪 Test the complete encryption system"""
    print("🧪 ENCRYPTION SYSTEM TEST")
    print("=" * 60)
    
    # Test basic encryption
    print("\n1️⃣ Testing Basic Encryption...")
    test_encryption()
    
    print("\n" + "=" * 60)
    
    # Test encrypted models
    print("\n2️⃣ Testing Encrypted Models...")
    test_encrypted_models()
    
    print("\n" + "=" * 60)
    
    # Test repository
    print("\n3️⃣ Testing Encrypted Repository...")
    repo = EncryptedCVRepository()
    
    if repo.connect():
        try:
            repo.test_encryption_functionality()
        except Exception as e:
            print(f"❌ Repository test error: {e}")
        finally:
            repo.disconnect()
    else:
        print("❌ Could not connect to database for repository test")
    
    print("\n✅ ENCRYPTION SYSTEM TEST COMPLETED")


def migrate_to_encryption():
    """🔄 Migrate existing data to encrypted format"""
    print("🔄 DATA MIGRATION TO ENCRYPTION")
    print("=" * 50)
    
    repo = EncryptedCVRepository()
    
    if not repo.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        print("⚠️ This will encrypt all existing applicant data in the database.")
        print("   This is a one-way operation that cannot be easily reversed.")
        print("   A backup table will be created automatically.")
        
        response = input("\n🤔 Do you want to proceed? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("❌ Migration cancelled")
            return False
        
        # Create backup
        print("\n📋 Creating backup table...")
        if repo.create_backup_table():
            print("✅ Backup table created: ApplicantProfile_Backup")
        else:
            print("⚠️ Warning: Could not create backup table")
            response = input("Continue anyway? (yes/no): ").strip().lower()
            if response != 'yes':
                print("❌ Migration cancelled")
                return False
        
        # Perform migration
        print("\n🔒 Starting encryption migration...")
        success = repo.migrate_existing_data_to_encrypted()
        
        if success:
            print("✅ Migration completed successfully!")
            repo.show_encryption_status()
        else:
            print("❌ Migration failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    
    finally:
        repo.disconnect()


def show_encryption_status():
    """📊 Show current encryption status"""
    print("📊 ENCRYPTION STATUS")
    print("=" * 40)
    
    repo = EncryptedCVRepository()
    
    if not repo.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        repo.show_encryption_status()
        
        # Show some sample data (anonymized)
        print("\n📋 Sample Data (first few characters only):")
        query = "SELECT applicant_id, LEFT(first_name, 10) as first_sample, LEFT(email, 15) as email_sample FROM ApplicantProfile LIMIT 3"
        results = repo.db.execute_query(query)
        
        if results:
            for row in results:
                print(f"   ID {row['applicant_id']}: {row['first_sample']}... | {row['email_sample']}...")
        else:
            print("   No data found")
    
    except Exception as e:
        print(f"❌ Error showing status: {e}")
    
    finally:
        repo.disconnect()


def enable_encryption():
    """🔒 Enable encryption for new data"""
    print("🔒 ENABLING ENCRYPTION")
    print("=" * 30)
    
    repo = EncryptedCVRepository()
    repo.enable_encryption()
    
    print("✅ Encryption enabled for new applicant data")
    print("   All new profiles will be automatically encrypted")
    print("   Existing data remains unchanged (use --migrate to encrypt)")


def disable_encryption():
    """🔓 Disable encryption (for demo/testing)"""
    print("🔓 DISABLING ENCRYPTION")
    print("=" * 30)
    
    print("⚠️ This will disable encryption for NEW data only.")
    print("   Existing encrypted data will still be readable.")
    print("   This is typically used for demo purposes.")
    
    response = input("\n🤔 Do you want to proceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Operation cancelled")
        return
    
    repo = EncryptedCVRepository()
    repo.disable_encryption()
    
    print("✅ Encryption disabled for new data")
    print("   New profiles will be stored in plaintext")


def benchmark_encryption():
    """⚡ Benchmark encryption performance"""
    print("⚡ ENCRYPTION PERFORMANCE BENCHMARK")
    print("=" * 50)
    
    import time
    
    encryptor = CustomEncryption()
    
    # Test data of various sizes
    test_cases = [
        ("Short", "John Doe"),
        ("Medium", "john.doe@example.com with some additional text"),
        ("Long", "This is a very long piece of text that represents a typical address or description field that might be found in an applicant profile. It contains multiple words and should provide a good test of encryption performance." * 3)
    ]
    
    print("📊 Testing encryption/decryption speed:")
    print()
    
    for name, data in test_cases:
        print(f"🧪 {name} text ({len(data)} chars):")
        
        # Encryption timing
        start_time = time.time()
        encrypted, salt = encryptor.encrypt_data(data)
        encrypt_time = time.time() - start_time
        
        # Decryption timing  
        start_time = time.time()
        decrypted = encryptor.decrypt_data(encrypted)
        decrypt_time = time.time() - start_time
        
        # Verify correctness
        correct = data == decrypted
        
        print(f"   🔒 Encrypt: {encrypt_time*1000:.2f}ms")
        print(f"   🔓 Decrypt: {decrypt_time*1000:.2f}ms")
        print(f"   📏 Size: {len(data)} → {len(encrypted)} chars ({len(encrypted)/len(data):.1f}x)")
        print(f"   ✅ Correct: {correct}")
        print()
    
    # Bulk test
    print("📦 Bulk encryption test (100 operations):")
    test_data = "Sample applicant data for bulk testing"
    
    start_time = time.time()
    for _ in range(100):
        encrypted, _ = encryptor.encrypt_data(test_data)
        decryptor = CustomEncryption()  # New instance
        decrypted = decryptor.decrypt_data(encrypted)
    
    total_time = time.time() - start_time
    print(f"   ⏱️ Total time: {total_time:.3f}s")
    print(f"   📊 Average per operation: {total_time*10:.2f}ms")
    
    print("✅ Performance benchmark completed!")


def create_demo_encrypted_data():
    """📝 Create demo data with encryption"""
    print("📝 CREATING DEMO ENCRYPTED DATA")
    print("=" * 40)
    
    repo = EncryptedCVRepository()
    
    if not repo.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        # Enable encryption
        repo.enable_encryption()
        
        demo_profiles = [
            ApplicantProfile(
                first_name="Alice",
                last_name="Encrypted",
                email="alice.encrypted@secure.com",
                phone_number="+1-555-ENC-0001",
                address="123 Secure Street, Encrypted City, EC 12345"
            ),
            ApplicantProfile(
                first_name="Bob",
                last_name="Protected",
                email="bob.protected@secure.com", 
                phone_number="+1-555-ENC-0002",
                address="456 Private Lane, Safe Town, ST 67890"
            ),
            ApplicantProfile(
                first_name="Carol",
                last_name="Confidential",
                email="carol.confidential@secure.com",
                phone_number="+1-555-ENC-0003", 
                address="789 Hidden Boulevard, Secret City, SC 11111"
            )
        ]
        
        print(f"🔒 Creating {len(demo_profiles)} encrypted demo profiles...")
        
        created_count = 0
        for profile in demo_profiles:
            applicant_id = repo.create_encrypted_applicant(profile)
            if applicant_id:
                created_count += 1
        
        print(f"✅ Created {created_count} encrypted demo profiles")
        
        # Show verification
        print("\n🔍 Verification - retrieving and decrypting data:")
        encrypted_cvs = repo.get_all_encrypted_cvs()
        
        for cv in encrypted_cvs[-created_count:]:  # Show last N created
            profile = cv.applicant_profile
            print(f"   📋 {profile.full_name} - {profile.email}")
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
    
    finally:
        repo.disconnect()


def main():
    """🎯 Main CLI function"""
    parser = argparse.ArgumentParser(
        description="🔐 CV ATS Encryption Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python encryption_manager.py --test           # Test encryption system
  python encryption_manager.py --migrate        # Migrate existing data to encrypted
  python encryption_manager.py --status         # Show encryption status
  python encryption_manager.py --enable         # Enable encryption for new data
  python encryption_manager.py --disable        # Disable encryption (demo mode)
  python encryption_manager.py --benchmark      # Run performance benchmarks
  python encryption_manager.py --demo           # Create demo encrypted data
        """
    )
    
    parser.add_argument('--test', action='store_true', 
                       help='🧪 Test the complete encryption system')
    parser.add_argument('--migrate', action='store_true',
                       help='🔄 Migrate existing plaintext data to encrypted format')
    parser.add_argument('--status', action='store_true',
                       help='📊 Show current encryption status')
    parser.add_argument('--enable', action='store_true',
                       help='🔒 Enable encryption for new data')
    parser.add_argument('--disable', action='store_true',
                       help='🔓 Disable encryption (demo/testing mode)')
    parser.add_argument('--benchmark', action='store_true',
                       help='⚡ Run encryption performance benchmarks')
    parser.add_argument('--demo', action='store_true',
                       help='📝 Create demo encrypted data')
    
    args = parser.parse_args()
    
    # Show help if no arguments
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("🔐 CV ATS Encryption Manager")
    print("=" * 50)
    
    try:
        if args.test:
            test_encryption_system()
        
        if args.migrate:
            migrate_to_encryption()
        
        if args.status:
            show_encryption_status()
        
        if args.enable:
            enable_encryption()
        
        if args.disable:
            disable_encryption()
        
        if args.benchmark:
            benchmark_encryption()
        
        if args.demo:
            create_demo_encrypted_data()
    
    except KeyboardInterrupt:
        print("\n⚠️ Operation interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
