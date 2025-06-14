"""
🔐 ENCRYPTED REPOSITORY: Database layer with encryption support
Handles both encrypted and unencrypted data for backward compatibility
"""

from typing import List, Optional, Dict, Any
import os
import time

try:
    from .connection import DatabaseConnection
    from .repository import CVRepository
    from ..models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
    from ..models.encrypted_models import (
        EncryptedApplicantProfile, EncryptedCVSearchResult, 
        encryption_config, EncryptionConfigManager
    )
    from ..utils.encryption import FieldEncryption
    from ..utils.pdf_parser import PDFParser
    from ..algorithms.string_matcher import StringMatcher
except ImportError:
    try:
        from connection import DatabaseConnection
        from repository import CVRepository
        from models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
        from models.encrypted_models import (
            EncryptedApplicantProfile, EncryptedCVSearchResult,
            encryption_config, EncryptionConfigManager
        )
        from utils.encryption import FieldEncryption
        from utils.pdf_parser import PDFParser
        from algorithms.string_matcher import StringMatcher
    except ImportError:
        # Import from src package
        from src.database.connection import DatabaseConnection
        from src.database.repository import CVRepository
        from src.models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
        from src.models.encrypted_models import (
            EncryptedApplicantProfile, EncryptedCVSearchResult,
            encryption_config, EncryptionConfigManager
        )
        from src.utils.encryption import FieldEncryption
        from src.utils.pdf_parser import PDFParser
        from src.algorithms.string_matcher import StringMatcher


class EncryptedCVRepository(CVRepository):
    """🔐 CV Repository with encryption support"""
    
    def __init__(self):
        super().__init__()
        self.field_encryption = FieldEncryption()
        self.encryption_config = encryption_config
        
        # Track encryption status
        self._encryption_enabled = True
        
        print("🔐 Encrypted CV Repository initialized")
        print(f"   Encryption: {'Enabled' if self._encryption_enabled else 'Disabled'}")
        print(f"   Backward compatibility: {'Enabled' if self.encryption_config.backward_compatibility else 'Disabled'}")
    
    # =============================================================================
    # 🔐 ENCRYPTION MANAGEMENT
    # =============================================================================
    
    def enable_encryption(self):
        """Enable encryption for new data"""
        self._encryption_enabled = True
        self.encryption_config.enable_encryption()
    
    def disable_encryption(self):
        """Disable encryption (for demo/testing)"""
        self._encryption_enabled = False
        self.encryption_config.disable_encryption()
    
    def is_encryption_enabled(self) -> bool:
        """Check if encryption is currently enabled"""
        return self._encryption_enabled and self.encryption_config.is_encryption_enabled()
    
    # =============================================================================
    # 🔒 ENCRYPTED DATABASE OPERATIONS
    # =============================================================================
    
    def create_encrypted_applicant(self, profile: ApplicantProfile) -> Optional[int]:
        """Create new applicant with encrypted data"""
        try:
            if self.is_encryption_enabled():
                # Convert to encrypted profile
                encrypted_profile = EncryptedApplicantProfile.from_regular_profile(profile)
                db_data = encrypted_profile.to_database_dict()
                print(f"🔒 Creating encrypted applicant: {profile.full_name}")
            else:
                # Store in plaintext
                db_data = {
                    'first_name': profile.first_name,
                    'last_name': profile.last_name,
                    'email': profile.email,
                    'phone_number': profile.phone_number,
                    'address': profile.address,
                    'date_of_birth': profile.date_of_birth,
                    'created_at': profile.created_at,
                    'updated_at': profile.updated_at
                }
                print(f"📝 Creating plaintext applicant: {profile.full_name}")
            
            query = """
            INSERT INTO ApplicantProfile 
            (first_name, last_name, email, phone_number, address, date_of_birth)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                db_data['first_name'],
                db_data['last_name'], 
                db_data['email'],
                db_data['phone_number'],
                db_data['address'],
                db_data['date_of_birth']
            )
            
            applicant_id = self.db.execute_insert(query, params)
            
            if applicant_id:
                encryption_status = "🔒 encrypted" if self.is_encryption_enabled() else "📝 plaintext"
                print(f"✅ Created applicant {applicant_id} ({encryption_status})")
            
            return applicant_id
            
        except Exception as e:
            print(f"❌ Error creating encrypted applicant: {e}")
            return None
    
    def create_application(self, application: ApplicationDetail) -> Optional[int]:
        """Create application detail (not encrypted)"""
        try:
            query = """
            INSERT INTO ApplicationDetail 
            (applicant_id, application_role, cv_path, applied_date, status)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                application.applicant_id,
                application.application_role,
                application.cv_path,
                application.applied_date,
                application.status or 'active'
            )
            
            return self.db.execute_insert(query, params)
            
        except Exception as e:
            print(f"❌ Error creating application: {e}")
            return None
    
    def get_all_encrypted_cvs(self) -> List[EncryptedCVSearchResult]:
        """Get all CVs with automatic decryption support"""
        try:
            query = """
            SELECT 
                ap.applicant_id, ap.first_name, ap.last_name, ap.date_of_birth,
                ap.address, ap.phone_number, ap.email, ap.created_at as profile_created,
                ad.detail_id, ad.application_role, ad.cv_path, ad.applied_date, ad.status
            FROM ApplicantProfile ap
            JOIN ApplicationDetail ad ON ap.applicant_id = ad.applicant_id
            WHERE ad.status = 'active'
            ORDER BY ad.applied_date DESC
            """
            
            results = self.db.execute_query(query)
            cv_results = []
            
            if results:
                for row in results:
                    try:
                        # Create encrypted profile from database data
                        encrypted_profile = EncryptedApplicantProfile.from_database_dict({
                            'applicant_id': row['applicant_id'],
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'email': row['email'],
                            'phone_number': row['phone_number'],
                            'address': row['address'],
                            'date_of_birth': row['date_of_birth'],
                            'created_at': row['profile_created']
                        })
                        
                        # Create application detail
                        application = ApplicationDetail(
                            detail_id=row['detail_id'],
                            applicant_id=row['applicant_id'],
                            application_role=row['application_role'],
                            cv_path=row['cv_path'],
                            applied_date=row['applied_date'],
                            status=row['status']
                        )
                        
                        # Load CV text
                        cv_text = self._load_cv_text(row['cv_path'])
                        
                        # Create encrypted search result
                        cv_result = EncryptedCVSearchResult(
                            encrypted_applicant_profile=encrypted_profile,
                            application_detail=application,
                            cv_text=cv_text
                        )
                        
                        cv_results.append(cv_result)
                        
                    except Exception as e:
                        print(f"⚠️ Error loading encrypted CV: {e}")
                        continue
            
            return cv_results
            
        except Exception as e:
            print(f"❌ Error retrieving encrypted CVs: {e}")
            return []
    
    def search_encrypted_cvs_by_keywords(self, keywords: str, algorithm: str = "kmp", 
                                        top_matches: int = 10, similarity_threshold: float = 0.3) -> List[CVSearchResult]:
        """🔍 Search CVs with encryption support, return regular results"""
        try:
            print(f"🔍 Starting encrypted search with keywords: '{keywords}' using {algorithm.upper()}")
            
            # Get all encrypted CVs
            all_encrypted_cvs = self.get_all_encrypted_cvs()
            if not all_encrypted_cvs:
                print("❌ No CVs found in database!")
                return []
            
            print(f"📁 Found {len(all_encrypted_cvs)} CVs to search")
            
            # Convert to regular search results for processing
            regular_cvs = []
            for encrypted_cv in all_encrypted_cvs:
                regular_result = encrypted_cv.to_regular_result()
                regular_cvs.append(regular_result)
            
            # Use parent class search logic
            keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
            if not keyword_list:
                print("❌ No valid keywords provided!")
                return []
            
            print(f"🔑 Keywords to search: {keyword_list}")
            
            search_results = []
            search_times = {'exact': 0, 'fuzzy': 0}
            
            # Process each CV
            for i, cv_result in enumerate(regular_cvs, 1):
                try:
                    if not cv_result.cv_text:
                        continue
                    
                    # Exact match phase
                    exact_start = time.time()
                    exact_score, exact_matches = self._calculate_exact_match_score(
                        cv_result.cv_text, keyword_list, algorithm
                    )
                    search_times['exact'] += time.time() - exact_start
                    
                    if exact_score >= similarity_threshold:
                        cv_result.similarity_score = exact_score
                        cv_result.matched_keywords = exact_matches
                        cv_result.match_type = "exact"
                        search_results.append(cv_result)
                        print(f"✅ EXACT {i}: {cv_result.applicant_profile.full_name} - Score: {exact_score:.3f}")
                        continue
                    
                    # Fuzzy match phase
                    fuzzy_start = time.time()
                    fuzzy_score, fuzzy_matches = self._calculate_fuzzy_match_score(
                        cv_result.cv_text, keyword_list, 0.7
                    )
                    search_times['fuzzy'] += time.time() - fuzzy_start
                    
                    if fuzzy_score >= similarity_threshold:
                        cv_result.similarity_score = fuzzy_score
                        cv_result.matched_keywords = fuzzy_matches
                        cv_result.match_type = "fuzzy"
                        search_results.append(cv_result)
                        print(f"✅ FUZZY {i}: {cv_result.applicant_profile.full_name} - Score: {fuzzy_score:.3f}")
                
                except Exception as e:
                    print(f"❌ Error processing CV {i}: {e}")
                    continue
            
            # Sort by similarity score
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Limit results
            final_results = search_results[:top_matches]
            
            print(f"\n🎯 Search completed:")
            print(f"   📊 Found {len(final_results)} matches out of {len(regular_cvs)} CVs")
            print(f"   ⏱️ Exact match time: {search_times['exact']:.3f}s")
            print(f"   ⏱️ Fuzzy match time: {search_times['fuzzy']:.3f}s")
            print(f"   🔐 Data decryption: Automatic")
            
            return final_results
            
        except Exception as e:
            print(f"❌ Error in encrypted search: {e}")
            return []
    
    # =============================================================================
    # 🔄 BACKWARD COMPATIBILITY METHODS
    # =============================================================================
    
    def migrate_existing_data_to_encrypted(self) -> bool:
        """Migrate existing plaintext data to encrypted format"""
        try:
            print("🔄 Starting data migration to encrypted format...")
            
            # Get all existing plaintext profiles
            query = "SELECT * FROM ApplicantProfile"
            results = self.db.execute_query(query)
            
            if not results:
                print("ℹ️ No data to migrate")
                return True
            
            migrated_count = 0
            
            for row in results:
                try:
                    # Check if data is already encrypted (has base64-like format)
                    first_name = row.get('first_name', '')
                    if self._is_likely_encrypted(first_name):
                        print(f"⏭️ Skipping already encrypted profile {row['applicant_id']}")
                        continue
                    
                    # Create profile from plaintext data
                    profile = ApplicantProfile(
                        applicant_id=row['applicant_id'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        email=row['email'],
                        phone_number=row['phone_number'],
                        address=row['address'],
                        date_of_birth=row['date_of_birth'],
                        created_at=row['created_at']
                    )
                    
                    # Convert to encrypted
                    encrypted_profile = EncryptedApplicantProfile.from_regular_profile(profile)
                    db_data = encrypted_profile.to_database_dict()
                    
                    # Update database with encrypted data
                    update_query = """
                    UPDATE ApplicantProfile 
                    SET first_name = %s, last_name = %s, email = %s, 
                        phone_number = %s, address = %s, date_of_birth = %s
                    WHERE applicant_id = %s
                    """
                    
                    params = (
                        db_data['first_name'],
                        db_data['last_name'],
                        db_data['email'],
                        db_data['phone_number'],
                        db_data['address'],
                        db_data['date_of_birth'],
                        row['applicant_id']
                    )
                    
                    if self.db.execute_update(update_query, params):
                        migrated_count += 1
                        print(f"✅ Migrated profile {row['applicant_id']}: {profile.full_name}")
                
                except Exception as e:
                    print(f"❌ Error migrating profile {row.get('applicant_id', '?')}: {e}")
                    continue
            
            print(f"🎉 Migration completed: {migrated_count} profiles encrypted")
            return migrated_count > 0
            
        except Exception as e:
            print(f"❌ Error in data migration: {e}")
            return False
    
    def _is_likely_encrypted(self, value: str) -> bool:
        """Check if a value is likely already encrypted (base64 format)"""
        if not value or len(value) < 20:
            return False
        
        try:
            import base64
            # Try to decode as base64
            decoded = base64.b64decode(value.encode('ascii'))
            # If successful and reasonable length, likely encrypted
            return len(decoded) >= 32  # Minimum encrypted data size
        except:
            return False
    
    def create_backup_table(self) -> bool:
        """Create backup of original data before migration"""
        try:
            print("💾 Creating backup table...")
            
            backup_query = """
            CREATE TABLE IF NOT EXISTS ApplicantProfile_Backup AS 
            SELECT * FROM ApplicantProfile
            """
            
            return self.db.execute_update(backup_query)
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False
    
    # =============================================================================
    # 🧪 TESTING AND DEMONSTRATION
    # =============================================================================
    
    def test_encryption_functionality(self):
        """Test encryption functionality with sample data"""
        print("🧪 Testing Encryption Functionality")
        print("=" * 50)
        
        # Test profile creation with encryption
        test_profile = ApplicantProfile(
            first_name="Test",
            last_name="User",
            email="test.user@encrypted.com",
            phone_number="+1-555-TEST-001",
            address="123 Encrypted Street, Secure City, SC"
        )
        
        print(f"📝 Creating test profile: {test_profile.full_name}")
        
        # Test with encryption enabled
        self.enable_encryption()
        encrypted_id = self.create_encrypted_applicant(test_profile)
        
        if encrypted_id:
            print(f"✅ Created encrypted profile with ID: {encrypted_id}")
            
            # Retrieve and verify
            encrypted_cvs = self.get_all_encrypted_cvs()
            test_cv = next((cv for cv in encrypted_cvs if cv.encrypted_applicant_profile.applicant_id == encrypted_id), None)
            
            if test_cv:
                decrypted_profile = test_cv.applicant_profile
                print(f"🔓 Retrieved profile: {decrypted_profile.full_name}")
                print(f"   Email: {decrypted_profile.email}")
                print(f"   Phone: {decrypted_profile.phone_number}")
                
                # Verify data integrity
                if (test_profile.full_name == decrypted_profile.full_name and
                    test_profile.email == decrypted_profile.email):
                    print("✅ Encryption/Decryption test PASSED")
                else:
                    print("❌ Encryption/Decryption test FAILED")
            
            # Clean up test data
            self.db.execute_update(f"DELETE FROM ApplicantProfile WHERE applicant_id = {encrypted_id}")
            print("🗑️ Test data cleaned up")
        
        print("🔐 Encryption test completed!")
    
    def show_encryption_status(self):
        """Show current encryption status and statistics"""
        print("📊 Encryption Status Report")
        print("=" * 40)
        
        print(f"🔐 Encryption enabled: {self.is_encryption_enabled()}")
        print(f"🔄 Backward compatibility: {self.encryption_config.backward_compatibility}")
        
        # Check database for encrypted vs plaintext data
        try:
            query = "SELECT applicant_id, first_name FROM ApplicantProfile LIMIT 5"
            results = self.db.execute_query(query)
            
            if results:
                encrypted_count = 0
                plaintext_count = 0
                
                for row in results:
                    if self._is_likely_encrypted(row.get('first_name', '')):
                        encrypted_count += 1
                    else:
                        plaintext_count += 1
                
                print(f"📈 Sample data analysis (first 5 records):")
                print(f"   🔒 Encrypted: {encrypted_count}")
                print(f"   📝 Plaintext: {plaintext_count}")
        
        except Exception as e:
            print(f"⚠️ Error analyzing data: {e}")


def test_encrypted_repository():
    """🧪 Test the encrypted repository functionality"""
    print("🧪 Testing Encrypted Repository")
    print("=" * 50)
    
    repo = EncryptedCVRepository()
    
    if not repo.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        # Test encryption functionality
        repo.test_encryption_functionality()
        
        # Show status
        repo.show_encryption_status()
        
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    finally:
        repo.disconnect()


if __name__ == "__main__":
    test_encrypted_repository()
