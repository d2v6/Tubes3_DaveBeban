#!/usr/bin/env python3
"""
🔐🗄️ FULL INTEGRATION TEST for CV ATS Encryption System
========================================================
Test the complete encrypted repository system with all features.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our working components
from src.utils.simple_encryption import SimpleEncryption, FieldEncryption
from src.database.connection import DatabaseConnection
from datetime import date, datetime
import traceback

class EncryptedApplicantRepository:
    """Simple encrypted repository for testing full integration"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.encryption = SimpleEncryption()
        self.sensitive_fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
    
    def connect(self):
        """Connect to database"""
        return self.db.connect()
    
    def disconnect(self):
        """Disconnect from database"""
        self.db.disconnect()
    
    def _encrypt_profile(self, profile_data):
        """Encrypt sensitive fields in profile data"""
        encrypted_data = {}
        for field, value in profile_data.items():
            if field in self.sensitive_fields and value:
                encrypted_value, _ = self.encryption.encrypt_data(str(value))
                encrypted_data[field] = encrypted_value
            else:
                encrypted_data[field] = value
        return encrypted_data
    
    def _decrypt_profile(self, encrypted_data):
        """Decrypt sensitive fields in profile data"""
        decrypted_data = {}
        for field, value in encrypted_data.items():
            if field in self.sensitive_fields and value:
                try:
                    decrypted_data[field] = self.encryption.decrypt_data(value)
                except:
                    # If decryption fails, it might be plaintext (backward compatibility)
                    decrypted_data[field] = value
            else:
                decrypted_data[field] = value
        return decrypted_data
    
    def create_applicant(self, profile_data):
        """Create a new encrypted applicant profile"""
        try:
            encrypted_data = self._encrypt_profile(profile_data)
            
            insert_query = """
            INSERT INTO applicant_profiles 
            (first_name, last_name, email, phone_number, address, date_of_birth, education, experience, skills)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                encrypted_data.get('first_name'),
                encrypted_data.get('last_name'),
                encrypted_data.get('email'),
                encrypted_data.get('phone_number'),
                encrypted_data.get('address'),
                encrypted_data.get('date_of_birth'),
                encrypted_data.get('education'),
                encrypted_data.get('experience'),
                encrypted_data.get('skills')
            )
            
            self.db.cursor.execute(insert_query, values)
            self.db.connection.commit()
            return self.db.cursor.lastrowid
            
        except Exception as e:
            print(f"❌ Create applicant failed: {e}")
            return None
    
    def get_applicant(self, applicant_id):
        """Get an applicant profile and decrypt it"""
        try:
            select_query = """
            SELECT applicant_id, first_name, last_name, email, phone_number, address, 
                   date_of_birth, education, experience, skills, created_at, updated_at
            FROM applicant_profiles WHERE applicant_id = %s
            """
            
            self.db.cursor.execute(select_query, (applicant_id,))
            encrypted_data = self.db.cursor.fetchone()
            
            if encrypted_data:
                return self._decrypt_profile(encrypted_data)
            return None
            
        except Exception as e:
            print(f"❌ Get applicant failed: {e}")
            return None
    
    def update_applicant(self, applicant_id, update_data):
        """Update an applicant profile with encryption"""
        try:
            encrypted_updates = self._encrypt_profile(update_data)
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for field, value in encrypted_updates.items():
                if field != 'applicant_id':  # Don't update ID
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
            
            if not set_clauses:
                return True  # Nothing to update
            
            values.append(applicant_id)  # For WHERE clause
            
            update_query = f"""
            UPDATE applicant_profiles 
            SET {', '.join(set_clauses)}
            WHERE applicant_id = %s
            """
            
            self.db.cursor.execute(update_query, values)
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
            
        except Exception as e:
            print(f"❌ Update applicant failed: {e}")
            return False
    
    def delete_applicant(self, applicant_id):
        """Delete an applicant profile"""
        try:
            delete_query = "DELETE FROM applicant_profiles WHERE applicant_id = %s"
            self.db.cursor.execute(delete_query, (applicant_id,))
            self.db.connection.commit()
            return self.db.cursor.rowcount > 0
            
        except Exception as e:
            print(f"❌ Delete applicant failed: {e}")
            return False
    
    def search_applicants(self, search_term):
        """Search applicants (note: encrypted data won't match directly)"""
        try:
            # This is a simple example - in practice, you'd need special search methods for encrypted data
            search_query = """
            SELECT applicant_id, first_name, last_name, email, phone_number, address, 
                   date_of_birth, education, experience, skills
            FROM applicant_profiles 
            WHERE education LIKE %s OR experience LIKE %s OR skills LIKE %s
            """
            
            search_pattern = f"%{search_term}%"
            self.db.cursor.execute(search_query, (search_pattern, search_pattern, search_pattern))
            results = self.db.cursor.fetchall()
            
            # Decrypt results
            decrypted_results = []
            for result in results:
                decrypted_results.append(self._decrypt_profile(result))
            
            return decrypted_results
            
        except Exception as e:
            print(f"❌ Search applicants failed: {e}")
            return []

def test_encrypted_repository_crud():
    """Test Create, Read, Update, Delete operations with encryption"""
    print("🔐 TESTING ENCRYPTED REPOSITORY CRUD")
    print("=" * 60)
    
    try:
        repo = EncryptedApplicantRepository()
        
        if not repo.connect():
            print("❌ Repository connection failed!")
            return False
        
        print("✅ Repository connected successfully!")
        
        # Test data
        test_applicant = {
            'first_name': 'Sarah',
            'last_name': 'EncryptedTest',
            'email': 'sarah.encrypted@example.com',
            'phone_number': '+1-555-SECURE-123',
            'address': '456 Security Blvd, Encryption City, EC 12345',
            'date_of_birth': '1992-08-15',
            'education': 'MS Cybersecurity',
            'experience': '3 years in encryption and data security',
            'skills': 'Python, Encryption, Database Security, Cryptography'
        }
        
        print(f"📝 Creating applicant: {test_applicant['first_name']} {test_applicant['last_name']}")
        
        # CREATE
        applicant_id = repo.create_applicant(test_applicant)
        if not applicant_id:
            print("❌ Failed to create applicant!")
            return False
        
        print(f"✅ Created applicant with ID: {applicant_id}")
        
        # READ
        retrieved_applicant = repo.get_applicant(applicant_id)
        if not retrieved_applicant:
            print("❌ Failed to retrieve applicant!")
            return False
        
        print(f"✅ Retrieved applicant: {retrieved_applicant['first_name']} {retrieved_applicant['last_name']}")
        
        # Verify decrypted data matches original
        key_fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
        match = all(retrieved_applicant[field] == test_applicant[field] for field in key_fields)
        
        if match:
            print("✅ Decrypted data matches original!")
        else:
            print("❌ Data mismatch after decryption!")
            return False
        
        # UPDATE
        update_data = {
            'email': 'sarah.updated@example.com',
            'phone_number': '+1-555-UPDATED-456',
            'skills': 'Python, Advanced Encryption, Database Security, Quantum Cryptography'
        }
        
        print(f"📝 Updating applicant with new email: {update_data['email']}")
        
        if repo.update_applicant(applicant_id, update_data):
            print("✅ Applicant updated successfully!")
            
            # Verify update
            updated_applicant = repo.get_applicant(applicant_id)
            if (updated_applicant['email'] == update_data['email'] and 
                updated_applicant['phone_number'] == update_data['phone_number'] and
                updated_applicant['skills'] == update_data['skills']):
                print("✅ Updated data verified!")
            else:
                print("❌ Update verification failed!")
                return False
        else:
            print("❌ Failed to update applicant!")
            return False
        
        # SEARCH (limited functionality with encrypted data)
        search_results = repo.search_applicants('Cybersecurity')
        print(f"🔍 Search for 'Cybersecurity' returned {len(search_results)} results")
        
        # DELETE
        if repo.delete_applicant(applicant_id):
            print("✅ Applicant deleted successfully!")
            
            # Verify deletion
            deleted_check = repo.get_applicant(applicant_id)
            if deleted_check is None:
                print("✅ Deletion verified!")
            else:
                print("❌ Deletion verification failed!")
                return False
        else:
            print("❌ Failed to delete applicant!")
            return False
        
        repo.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Repository CRUD test failed: {e}")
        print(traceback.format_exc())
        return False

def test_backward_compatibility():
    """Test that the system can handle both encrypted and plaintext data"""
    print("\n🔄 TESTING BACKWARD COMPATIBILITY")
    print("=" * 60)
    
    try:
        repo = EncryptedApplicantRepository()
        
        if not repo.connect():
            print("❌ Repository connection failed!")
            return False
        
        # Insert plaintext data directly into database
        plaintext_data = {
            'first_name': 'PlainText',
            'last_name': 'User',
            'email': 'plaintext@example.com',
            'phone_number': '+1-555-PLAIN-123',
            'address': '123 Plain St, Clear City, CC',
            'date_of_birth': '1985-12-25',
            'education': 'BA Computer Science',
            'experience': 'Legacy system developer',
            'skills': 'Java, SQL, System Integration'
        }
        
        # Insert without encryption (simulating legacy data)
        insert_query = """
        INSERT INTO applicant_profiles 
        (first_name, last_name, email, phone_number, address, date_of_birth, education, experience, skills)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            plaintext_data['first_name'],
            plaintext_data['last_name'],
            plaintext_data['email'],
            plaintext_data['phone_number'],
            plaintext_data['address'],
            plaintext_data['date_of_birth'],
            plaintext_data['education'],
            plaintext_data['experience'],
            plaintext_data['skills']
        )
        
        repo.db.cursor.execute(insert_query, values)
        repo.db.connection.commit()
        plaintext_id = repo.db.cursor.lastrowid
        
        print(f"✅ Inserted plaintext data with ID: {plaintext_id}")
        
        # Try to read it through encrypted repository
        retrieved_data = repo.get_applicant(plaintext_id)
        
        if retrieved_data:
            print(f"✅ Retrieved plaintext data: {retrieved_data['first_name']} {retrieved_data['last_name']}")
            
            # Verify it matches original
            key_fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']
            match = all(retrieved_data[field] == plaintext_data[field] for field in key_fields)
            
            if match:
                print("✅ Backward compatibility confirmed - plaintext data reads correctly!")
            else:
                print("❌ Backward compatibility failed!")
                return False
        else:
            print("❌ Failed to retrieve plaintext data!")
            return False
        
        # Clean up
        repo.delete_applicant(plaintext_id)
        repo.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        print(traceback.format_exc())
        return False

def test_mixed_data_scenario():
    """Test scenario with both encrypted and plaintext data in the database"""
    print("\n🔀 TESTING MIXED DATA SCENARIO")
    print("=" * 60)
    
    try:
        repo = EncryptedApplicantRepository()
        
        if not repo.connect():
            print("❌ Repository connection failed!")
            return False
        
        # Create one encrypted applicant
        encrypted_applicant = {
            'first_name': 'Encrypted',
            'last_name': 'User',
            'email': 'encrypted@secure.com',
            'phone_number': '+1-555-SECURE-789',
            'address': '789 Secure Ave, Crypto City',
            'date_of_birth': '1990-01-01',
            'education': 'PhD Cryptography',
            'experience': 'Senior encryption engineer',
            'skills': 'Advanced Cryptography, Security Protocols'
        }
        
        encrypted_id = repo.create_applicant(encrypted_applicant)
        print(f"✅ Created encrypted applicant with ID: {encrypted_id}")
        
        # Create one plaintext applicant (simulating legacy data)
        plaintext_applicant = {
            'first_name': 'Legacy',
            'last_name': 'User',
            'email': 'legacy@old.com',
            'phone_number': '+1-555-OLD-456',
            'address': '456 Legacy Rd, Old City',
            'date_of_birth': '1980-05-10',
            'education': 'MS Software Engineering',
            'experience': 'Veteran software developer',
            'skills': 'COBOL, Legacy Systems, Mainframe'
        }
        
        # Insert plaintext directly
        insert_query = """
        INSERT INTO applicant_profiles 
        (first_name, last_name, email, phone_number, address, date_of_birth, education, experience, skills)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        repo.db.cursor.execute(insert_query, tuple(plaintext_applicant.values()))
        repo.db.connection.commit()
        plaintext_id = repo.db.cursor.lastrowid
        
        print(f"✅ Created plaintext applicant with ID: {plaintext_id}")
        
        # Retrieve both through encrypted repository
        encrypted_result = repo.get_applicant(encrypted_id)
        plaintext_result = repo.get_applicant(plaintext_id)
        
        if encrypted_result and plaintext_result:
            print(f"✅ Retrieved encrypted user: {encrypted_result['first_name']} {encrypted_result['last_name']}")
            print(f"✅ Retrieved plaintext user: {plaintext_result['first_name']} {plaintext_result['last_name']}")
            
            # Verify both are correct
            encrypted_match = encrypted_result['email'] == encrypted_applicant['email']
            plaintext_match = plaintext_result['email'] == plaintext_applicant['email']
            
            if encrypted_match and plaintext_match:
                print("✅ Mixed data scenario successful - both encrypted and plaintext data work!")
            else:
                print("❌ Mixed data scenario failed!")
                return False
        else:
            print("❌ Failed to retrieve mixed data!")
            return False
        
        # Clean up
        repo.delete_applicant(encrypted_id)
        repo.delete_applicant(plaintext_id)
        repo.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Mixed data scenario test failed: {e}")
        print(traceback.format_exc())
        return False

def main():
    """Run full integration tests"""
    print("🔐🗄️ FULL ENCRYPTION SYSTEM INTEGRATION TEST")
    print("=" * 80)
    
    tests = [
        ("Encrypted Repository CRUD", test_encrypted_repository_crud),
        ("Backward Compatibility", test_backward_compatibility),
        ("Mixed Data Scenario", test_mixed_data_scenario)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Final report
    print("\n🎯 FINAL RESULTS")
    print("=" * 80)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🏆 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ The complete encryption system is working perfectly!")
        print("✅ Ready for production deployment!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
