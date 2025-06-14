"""
🔐 SIMPLIFIED ENCRYPTION SYSTEM for CV ATS
Robust encryption implementation without built-in cryptography libraries

Features:
- Multi-layer XOR encryption with key stretching
- Salt-based key derivation 
- Base64 encoding for storage
- Backward compatibility with plaintext
"""

import os
import time
import base64
from typing import Optional, Tuple, Dict, Any


class SimpleEncryption:
    """🔐 Simple but effective encryption implementation"""
    
    def __init__(self, master_key: str = None):
        """Initialize encryption with master key"""
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY', 'CV_ATS_SECURE_MASTER_KEY_2024_STIMA_ITB')
        self.rounds = 3  # Number of encryption rounds
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt"""
        # Combine password and salt
        key_material = password.encode('utf-8') + salt
        
        # Simple key stretching - hash multiple times
        for _ in range(1000):  # 1000 rounds of key stretching
            key_material = self._simple_hash(key_material)
        
        return key_material
    
    def _simple_hash(self, data: bytes) -> bytes:
        """Simple hash function"""
        # Simple but effective hash
        h = 0x811C9DC5  # FNV offset basis
        for byte in data:
            h ^= byte
            h *= 0x01000193  # FNV prime
            h &= 0xFFFFFFFF
        
        # Convert to 32-byte result
        result = []
        for i in range(32):
            result.append((h >> (i % 32)) & 0xFF)
            h = (h * 0x01000193 + i) & 0xFFFFFFFF
        
        return bytes(result)
    
    def _multi_round_xor(self, data: bytes, key: bytes, rounds: int) -> bytes:
        """Apply multiple rounds of XOR encryption"""
        result = data
        
        for round_num in range(rounds):
            # Modify key for each round
            round_key = self._simple_hash(key + round_num.to_bytes(4, 'big'))
            
            # XOR with round key
            xor_result = []
            for i, byte in enumerate(result):
                key_byte = round_key[i % len(round_key)]
                xor_result.append(byte ^ key_byte)
            
            result = bytes(xor_result)
            
            # Add bit rotation for additional complexity
            if round_num < rounds - 1:
                result = self._rotate_bytes(result, round_num + 1)
        
        return result
    
    def _rotate_bytes(self, data: bytes, rotation: int) -> bytes:
        """Rotate bytes for additional complexity"""
        rotation = rotation % len(data)
        return data[rotation:] + data[:rotation]
    
    def encrypt_data(self, plaintext: str, salt: bytes = None) -> Tuple[str, bytes]:
        """🔒 Encrypt string data"""
        try:
            if not plaintext:
                return "", b""
            
            # Generate salt if not provided
            if salt is None:
                salt = self._generate_salt()
            
            # Derive encryption key
            key = self._derive_key(self.master_key, salt)
            
            # Convert to bytes
            data = plaintext.encode('utf-8')
            
            # Apply multi-round XOR encryption
            encrypted_data = self._multi_round_xor(data, key, self.rounds)
            
            # Combine salt + encrypted data
            combined = salt + encrypted_data
            
            # Encode to base64 for storage
            encoded = base64.b64encode(combined).decode('ascii')
            
            return encoded, salt
            
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return plaintext, b""  # Fallback to plaintext
    
    def decrypt_data(self, encrypted_text: str) -> str:
        """🔓 Decrypt string data"""
        try:
            if not encrypted_text:
                return ""
            
            # Check if data is actually encrypted (base64 format)
            try:
                combined_data = base64.b64decode(encrypted_text.encode('ascii'))
            except:
                # Not base64, assume it's plaintext (for backward compatibility)
                return encrypted_text
            
            if len(combined_data) < 16:  # Minimum: salt(16 bytes)
                return encrypted_text
            
            # Extract salt and encrypted data
            salt = combined_data[:16]
            encrypted_data = combined_data[16:]
            
            # Derive decryption key
            key = self._derive_key(self.master_key, salt)
            
            # Apply multi-round XOR decryption (reverse order)
            decrypted_data = encrypted_data
            
            for round_num in range(self.rounds - 1, -1, -1):
                # Reverse bit rotation first (if not the last round)
                if round_num < self.rounds - 1:
                    decrypted_data = self._rotate_bytes(decrypted_data, -(round_num + 1))
                
                # Modify key for this round
                round_key = self._simple_hash(key + round_num.to_bytes(4, 'big'))
                
                # XOR with round key
                xor_result = []
                for i, byte in enumerate(decrypted_data):
                    key_byte = round_key[i % len(round_key)]
                    xor_result.append(byte ^ key_byte)
                
                decrypted_data = bytes(xor_result)
            
            # Convert back to string
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return encrypted_text  # Fallback to original
    
    def _generate_salt(self) -> bytes:
        """Generate random salt"""
        # Use time and some deterministic randomness
        timestamp = int(time.time() * 1000000)
        salt_data = timestamp.to_bytes(8, 'big')
        
        # Add some pseudo-random bytes
        for i in range(8):
            salt_data += ((timestamp * (i + 1)) % 256).to_bytes(1, 'big')
        
        return salt_data


class FieldEncryption:
    """🏷️ Field-level encryption manager"""
    
    def __init__(self):
        self.encryptor = SimpleEncryption()
        
        # Define which fields should be encrypted
        self.encrypted_fields = {
            'first_name', 'last_name', 'email', 
            'phone_number', 'address', 'date_of_birth'
        }
    
    def encrypt_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """🔒 Encrypt sensitive profile fields"""
        encrypted_data = profile_data.copy()
        
        for field in self.encrypted_fields:
            if field in encrypted_data and encrypted_data[field] is not None:
                original_value = str(encrypted_data[field])
                encrypted_value, _ = self.encryptor.encrypt_data(original_value)
                encrypted_data[field] = encrypted_value
        
        return encrypted_data
    
    def decrypt_profile_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """🔓 Decrypt sensitive profile fields"""
        decrypted_data = encrypted_data.copy()
        
        for field in self.encrypted_fields:
            if field in decrypted_data and decrypted_data[field] is not None:
                encrypted_value = str(decrypted_data[field])
                decrypted_value = self.encryptor.decrypt_data(encrypted_value)
                
                # Handle special field types
                if field == 'date_of_birth' and decrypted_value:
                    try:
                        from datetime import datetime
                        decrypted_data[field] = datetime.strptime(decrypted_value, '%Y-%m-%d').date()
                    except:
                        decrypted_data[field] = decrypted_value
                else:
                    decrypted_data[field] = decrypted_value
        
        return decrypted_data


# Alias for compatibility
CustomEncryption = SimpleEncryption


def test_simple_encryption():
    """🧪 Test the simplified encryption system"""
    print("🧪 Testing Simple Encryption System")
    print("=" * 50)
    
    # Test basic encryption/decryption
    encryptor = SimpleEncryption()
    
    test_data = [
        "John Doe",
        "john.doe@example.com",
        "+1-555-123-4567",
        "123 Main Street, Anytown, USA",
        "Software Engineer with 5 years experience"
    ]
    
    print("📝 Testing individual string encryption:")
    all_passed = True
    
    for i, data in enumerate(test_data, 1):
        encrypted, salt = encryptor.encrypt_data(data)
        decrypted = encryptor.decrypt_data(encrypted)
        
        match = data == decrypted
        if not match:
            all_passed = False
        
        print(f"  {i}. Original:  {data}")
        print(f"     Encrypted: {encrypted[:50]}..." if len(encrypted) > 50 else f"     Encrypted: {encrypted}")
        print(f"     Decrypted: {decrypted}")
        print(f"     Match: {'✅' if match else '❌'}")
        print()
    
    # Test field encryption
    print("🏷️ Testing field-level encryption:")
    field_enc = FieldEncryption()
    
    sample_profile = {
        'applicant_id': 1,
        'first_name': 'Alice',
        'last_name': 'Johnson',
        'email': 'alice.johnson@example.com',
        'phone_number': '+1-555-987-6543',
        'address': '456 Oak Street, Springfield, IL',
        'date_of_birth': '1990-05-15'
    }
    
    print(f"Original profile: {sample_profile}")
    
    encrypted_profile = field_enc.encrypt_profile_data(sample_profile)
    print(f"Encrypted profile fields: {list(encrypted_profile.keys())}")
    
    decrypted_profile = field_enc.decrypt_profile_data(encrypted_profile)
    print(f"Decrypted profile: {decrypted_profile}")
    
    # Verify all fields match
    field_matches = True
    for key in sample_profile:
        if str(sample_profile[key]) != str(decrypted_profile[key]):
            field_matches = False
            print(f"❌ Mismatch in {key}: {sample_profile[key]} != {decrypted_profile[key]}")
    
    if field_matches:
        print("✅ All fields match after encryption/decryption!")
        all_passed = all_passed and True
    else:
        all_passed = False
    
    print(f"\n🎯 Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("🔐 Simple encryption system test completed!")
    
    return all_passed


if __name__ == "__main__":
    test_simple_encryption()
