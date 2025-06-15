import os
import time
import base64
from typing import Tuple, Dict, Any


class Encryption:
    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv(
            'ENCRYPTION_MASTER_KEY')
        self.rounds = 3  # Number of encryption rounds

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt"""
        key_material = password.encode('utf-8') + salt

        for _ in range(1000):  # 1000 rounds of key stretching
            key_material = self._simple_hash(key_material)

        return key_material

    def _simple_hash(self, data: bytes) -> bytes:
        """Simple hash function"""
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

            print(f"      Core encryption: '{plaintext}' -> ", end="")

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

            print(f"'{encoded[:20]}...'")
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
                combined_data = base64.b64decode(
                    encrypted_text.encode('ascii'))
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
                    decrypted_data = self._rotate_bytes(
                        decrypted_data, -(round_num + 1))

                # Modify key for this round
                round_key = self._simple_hash(
                    key + round_num.to_bytes(4, 'big'))

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
    def __init__(self):
        self.encryptor = Encryption()

        self.encrypted_fields = {
            'first_name', 'last_name', 'date_of_birth', 'address',
            'phone_number'
        }

    def encrypt_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        encrypted_data = profile_data.copy()
        print(f"🔒 FieldEncryption: Starting encryption for {len(self.encrypted_fields)} fields")

        for field in self.encrypted_fields:
            if field in encrypted_data and encrypted_data[field] is not None:
                original_value = str(encrypted_data[field])
                print(f"   Encrypting {field}: '{original_value}' -> ", end="")
                
                encrypted_value, _ = self.encryptor.encrypt_data(original_value)
                encrypted_data[field] = encrypted_value
                
                print(f"'{encrypted_value[:30]}...'")
            else:
                print(f"   Skipping {field}: not present or None")

        print(f"✅ FieldEncryption: Completed encryption")
        return encrypted_data

    def decrypt_profile_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        decrypted_data = encrypted_data.copy()

        for field in self.encrypted_fields:
            if field in decrypted_data and decrypted_data[field] is not None:
                encrypted_value = str(decrypted_data[field])
                decrypted_value = self.encryptor.decrypt_data(encrypted_value)

                # Handle special field types
                if field == 'date_of_birth' and decrypted_value:
                    try:
                        from datetime import datetime
                        decrypted_data[field] = datetime.strptime(
                            decrypted_value, '%Y-%m-%d').date()
                    except:
                        decrypted_data[field] = decrypted_value
                else:
                    decrypted_data[field] = decrypted_value

        return decrypted_data
