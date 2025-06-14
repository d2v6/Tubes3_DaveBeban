"""
🔐 ENCRYPTION SYSTEM for CV ATS
Advanced encryption without using Python's built-in cryptography libraries

This module provides a working encryption implementation for securing 
applicant profile data in the CV ATS system.

Features:
- Multi-layer XOR encryption with key stretching
- Salt-based key derivation 
- Base64 encoding for storage
- Backward compatibility with plaintext
- Field-level encryption for sensitive data
"""

# Import the working simple encryption with fallback
try:
    from .simple_encryption import SimpleEncryption, FieldEncryption, test_simple_encryption
except ImportError:
    try:
        from simple_encryption import SimpleEncryption, FieldEncryption, test_simple_encryption
    except ImportError:
        from src.utils.simple_encryption import SimpleEncryption, FieldEncryption, test_simple_encryption

# Aliases for compatibility
CustomEncryption = SimpleEncryption

# Export main functions
def test_encryption():
    """Test function for backward compatibility"""
    return test_simple_encryption()

# Export all classes and functions
__all__ = ['CustomEncryption', 'SimpleEncryption', 'FieldEncryption', 'test_encryption', 'test_simple_encryption']
