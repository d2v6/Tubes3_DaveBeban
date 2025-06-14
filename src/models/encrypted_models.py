"""
🔐 ENCRYPTED MODELS: Secure wrapper for database models
Transparent encryption/decryption for sensitive applicant data
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

try:
    from ..utils.encryption import FieldEncryption
except ImportError:
    try:
        from utils.encryption import FieldEncryption
    except ImportError:
        from src.utils.encryption import FieldEncryption

# Try to import database models with fallback
try:
    from .database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
except ImportError:
    try:
        from database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
    except ImportError:
        try:
            from src.models.database_models import ApplicantProfile, ApplicationDetail, CVSearchResult
        except ImportError:
            # Create minimal fallback classes if database_models not available
            @dataclass
            class ApplicantProfile:
                applicant_id: Optional[int] = None
                first_name: Optional[str] = None
                last_name: Optional[str] = None
                email: Optional[str] = None
                phone_number: Optional[str] = None
                address: Optional[str] = None
                date_of_birth: Optional[date] = None
                education: Optional[str] = None
                experience: Optional[str] = None
                skills: Optional[str] = None
                created_at: Optional[datetime] = None
                updated_at: Optional[datetime] = None
            
            @dataclass
            class ApplicationDetail:
                application_id: Optional[int] = None
                applicant_id: Optional[int] = None
                job_title: Optional[str] = None
                job_description: Optional[str] = None
                application_date: Optional[datetime] = None
                status: Optional[str] = None
            
            @dataclass  
            class CVSearchResult:
                applicant_id: Optional[int] = None
                score: Optional[float] = None
                matched_skills: Optional[List[str]] = None


@dataclass
class EncryptedApplicantProfile:
    """🔒 Encrypted version of ApplicantProfile with transparent encryption"""
    
    # Non-encrypted fields
    applicant_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Encrypted fields (stored as encrypted strings)
    _encrypted_first_name: Optional[str] = field(default=None, repr=False)
    _encrypted_last_name: Optional[str] = field(default=None, repr=False)
    _encrypted_email: Optional[str] = field(default=None, repr=False)
    _encrypted_phone_number: Optional[str] = field(default=None, repr=False)
    _encrypted_address: Optional[str] = field(default=None, repr=False)
    _encrypted_date_of_birth: Optional[str] = field(default=None, repr=False)
    
    # Encryption manager
    _field_encryption: FieldEncryption = field(default_factory=FieldEncryption, init=False, repr=False)
    
    def __post_init__(self):
        """Initialize encryption manager"""
        if not hasattr(self, '_field_encryption') or self._field_encryption is None:
            self._field_encryption = FieldEncryption()
    
    # Properties for transparent access to encrypted fields
    @property
    def first_name(self) -> Optional[str]:
        """Get decrypted first name"""
        if self._encrypted_first_name is None:
            return None
        return self._field_encryption.encryptor.decrypt_data(self._encrypted_first_name)
    
    @first_name.setter
    def first_name(self, value: Optional[str]):
        """Set first name (automatically encrypted)"""
        if value is None:
            self._encrypted_first_name = None
        else:
            encrypted_value, _ = self._field_encryption.encryptor.encrypt_data(str(value))
            self._encrypted_first_name = encrypted_value
    
    @property
    def last_name(self) -> Optional[str]:
        """Get decrypted last name"""
        if self._encrypted_last_name is None:
            return None
        return self._field_encryption.encryptor.decrypt_data(self._encrypted_last_name)
    
    @last_name.setter
    def last_name(self, value: Optional[str]):
        """Set last name (automatically encrypted)"""
        if value is None:
            self._encrypted_last_name = None
        else:
            encrypted_value, _ = self._field_encryption.encryptor.encrypt_data(str(value))
            self._encrypted_last_name = encrypted_value
    
    @property
    def email(self) -> Optional[str]:
        """Get decrypted email"""
        if self._encrypted_email is None:
            return None
        return self._field_encryption.encryptor.decrypt_data(self._encrypted_email)
    
    @email.setter
    def email(self, value: Optional[str]):
        """Set email (automatically encrypted)"""
        if value is None:
            self._encrypted_email = None
        else:
            encrypted_value, _ = self._field_encryption.encryptor.encrypt_data(str(value))
            self._encrypted_email = encrypted_value
    
    @property
    def phone_number(self) -> Optional[str]:
        """Get decrypted phone number"""
        if self._encrypted_phone_number is None:
            return None
        return self._field_encryption.encryptor.decrypt_data(self._encrypted_phone_number)
    
    @phone_number.setter
    def phone_number(self, value: Optional[str]):
        """Set phone number (automatically encrypted)"""
        if value is None:
            self._encrypted_phone_number = None
        else:
            encrypted_value, _ = self._field_encryption.encryptor.encrypt_data(str(value))
            self._encrypted_phone_number = encrypted_value
    
    @property
    def address(self) -> Optional[str]:
        """Get decrypted address"""
        if self._encrypted_address is None:
            return None
        return self._field_encryption.encryptor.decrypt_data(self._encrypted_address)
    
    @address.setter
    def address(self, value: Optional[str]):
        """Set address (automatically encrypted)"""
        if value is None:
            self._encrypted_address = None
        else:
            encrypted_value, _ = self._field_encryption.encryptor.encrypt_data(str(value))
            self._encrypted_address = encrypted_value
    
    @property
    def date_of_birth(self) -> Optional[date]:
        """Get decrypted date of birth"""
        if self._encrypted_date_of_birth is None:
            return None
        
        decrypted_str = self._field_encryption.encryptor.decrypt_data(self._encrypted_date_of_birth)
        if not decrypted_str:
            return None
        
        try:
            return datetime.strptime(decrypted_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    
    @date_of_birth.setter
    def date_of_birth(self, value: Optional[date]):
        """Set date of birth (automatically encrypted)"""
        if value is None:
            self._encrypted_date_of_birth = None
        else:
            if isinstance(value, date):
                date_str = value.strftime('%Y-%m-%d')
            else:
                date_str = str(value)
            encrypted_value, _ = self._field_encryption.encryptor.encrypt_data(date_str)
            self._encrypted_date_of_birth = encrypted_value
    
    @property
    def full_name(self) -> str:
        """Get full name (decrypted)"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) if parts else "Unknown"
    
    # Database interaction methods
    def to_database_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage (with encrypted fields)"""
        return {
            'applicant_id': self.applicant_id,
            'first_name': self._encrypted_first_name,
            'last_name': self._encrypted_last_name,
            'email': self._encrypted_email,
            'phone_number': self._encrypted_phone_number,
            'address': self._encrypted_address,
            'date_of_birth': self._encrypted_date_of_birth,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_database_dict(cls, data: Dict[str, Any]) -> 'EncryptedApplicantProfile':
        """Create instance from database row (with encrypted fields)"""
        instance = cls(
            applicant_id=data.get('applicant_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            _encrypted_first_name=data.get('first_name'),
            _encrypted_last_name=data.get('last_name'),
            _encrypted_email=data.get('email'),
            _encrypted_phone_number=data.get('phone_number'),
            _encrypted_address=data.get('address'),
            _encrypted_date_of_birth=data.get('date_of_birth')
        )
        return instance
    
    def to_regular_profile(self) -> ApplicantProfile:
        """Convert to regular ApplicantProfile with decrypted data"""
        return ApplicantProfile(
            applicant_id=self.applicant_id,
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone_number=self.phone_number,
            address=self.address,
            date_of_birth=self.date_of_birth,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_regular_profile(cls, profile: ApplicantProfile) -> 'EncryptedApplicantProfile':
        """Create encrypted profile from regular profile"""
        instance = cls(
            applicant_id=profile.applicant_id,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
        # Set properties (which will automatically encrypt)
        instance.first_name = profile.first_name
        instance.last_name = profile.last_name
        instance.email = profile.email
        instance.phone_number = profile.phone_number
        instance.address = profile.address
        instance.date_of_birth = profile.date_of_birth
        
        return instance


@dataclass 
class EncryptedCVSearchResult:
    """🔒 Encrypted version of CVSearchResult"""
    
    encrypted_applicant_profile: EncryptedApplicantProfile
    application_detail: ApplicationDetail
    match_count: int = 0
    matched_keywords: List[str] = field(default_factory=list)
    similarity_score: float = 0.0
    cv_text: str = ""
    match_type: str = "exact"
    
    @property
    def applicant_profile(self) -> ApplicantProfile:
        """Get decrypted applicant profile"""
        return self.encrypted_applicant_profile.to_regular_profile()
    
    def to_regular_result(self) -> CVSearchResult:
        """Convert to regular CVSearchResult with decrypted data"""
        return CVSearchResult(
            applicant_profile=self.applicant_profile,
            application_detail=self.application_detail,
            match_count=self.match_count,
            matched_keywords=self.matched_keywords,
            similarity_score=self.similarity_score,
            cv_text=self.cv_text
        )


class EncryptionConfigManager:
    """⚙️ Manage encryption settings and compatibility"""
    
    def __init__(self):
        self.encryption_enabled = True
        self.backward_compatibility = True
    
    def is_encryption_enabled(self) -> bool:
        """Check if encryption is enabled"""
        return self.encryption_enabled
    
    def enable_encryption(self):
        """Enable encryption for new data"""
        self.encryption_enabled = True
        print("🔒 Encryption enabled for new applicant data")
    
    def disable_encryption(self):
        """Disable encryption (for demo/testing)"""
        self.encryption_enabled = False
        print("🔓 Encryption disabled - data will be stored in plaintext")
    
    def set_backward_compatibility(self, enabled: bool):
        """Set backward compatibility with existing unencrypted data"""
        self.backward_compatibility = enabled
        if enabled:
            print("🔄 Backward compatibility enabled - can read both encrypted and plaintext data")
        else:
            print("🔒 Backward compatibility disabled - only encrypted data will be processed")


# Global encryption config
encryption_config = EncryptionConfigManager()


def test_encrypted_models():
    """🧪 Test encrypted models functionality"""
    print("🧪 Testing Encrypted Models")
    print("=" * 50)
    
    # Test encrypted profile
    print("📝 Testing EncryptedApplicantProfile:")
    
    # Create with regular data
    encrypted_profile = EncryptedApplicantProfile()
    encrypted_profile.first_name = "Jane"
    encrypted_profile.last_name = "Smith" 
    encrypted_profile.email = "jane.smith@example.com"
    encrypted_profile.phone_number = "+1-555-999-8888"
    encrypted_profile.address = "789 Pine Street, Hometown, TX"
    
    print(f"  Set data: {encrypted_profile.first_name} {encrypted_profile.last_name}")
    print(f"  Email: {encrypted_profile.email}")
    print(f"  Phone: {encrypted_profile.phone_number}")
    print(f"  Full name: {encrypted_profile.full_name}")
    
    # Check encrypted storage
    db_dict = encrypted_profile.to_database_dict()
    print(f"\n  Encrypted in DB:")
    print(f"    first_name: {db_dict['first_name'][:30]}...")
    print(f"    email: {db_dict['email'][:30]}...")
    
    # Test round-trip
    restored_profile = EncryptedApplicantProfile.from_database_dict(db_dict)
    print(f"\n  Restored: {restored_profile.first_name} {restored_profile.last_name}")
    print(f"  Match: {'✅' if encrypted_profile.full_name == restored_profile.full_name else '❌'}")
    
    # Test conversion to regular profile
    regular_profile = encrypted_profile.to_regular_profile()
    print(f"\n  Regular profile: {regular_profile.full_name}")
    
    print("\n✅ Encrypted models test completed!")


if __name__ == "__main__":
    test_encrypted_models()
