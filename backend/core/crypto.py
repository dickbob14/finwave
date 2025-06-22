"""
Encryption utilities for sensitive data
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Get encryption key from environment or generate
ENCRYPTION_KEY = os.getenv('FINWAVE_ENCRYPTION_KEY')

if not ENCRYPTION_KEY:
    # Generate a key from a password if not provided
    password = os.getenv('FINWAVE_SECRET', 'default-dev-secret').encode()
    salt = b'finwave-salt-v1'  # In production, use random salt per deployment
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    ENCRYPTION_KEY = key
else:
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

# Initialize Fernet cipher
cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt(plaintext: str) -> str:
    """
    Encrypt a string and return base64-encoded ciphertext
    
    Args:
        plaintext: String to encrypt
        
    Returns:
        Base64-encoded encrypted string
    """
    if not plaintext:
        return ""
    
    # Convert to bytes and encrypt
    plaintext_bytes = plaintext.encode('utf-8')
    encrypted_bytes = cipher_suite.encrypt(plaintext_bytes)
    
    # Return as base64 string for storage
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def decrypt(ciphertext: str) -> Optional[str]:
    """
    Decrypt a base64-encoded ciphertext
    
    Args:
        ciphertext: Base64-encoded encrypted string
        
    Returns:
        Decrypted string or None if decryption fails
    """
    if not ciphertext:
        return None
    
    try:
        # Decode from base64
        encrypted_bytes = base64.b64decode(ciphertext.encode('utf-8'))
        
        # Decrypt
        decrypted_bytes = cipher_suite.decrypt(encrypted_bytes)
        
        # Convert back to string
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # Log error in production
        print(f"Decryption error: {e}")
        return None


def generate_key() -> str:
    """
    Generate a new Fernet encryption key
    
    Returns:
        Base64-encoded encryption key
    """
    return Fernet.generate_key().decode('utf-8')


def hash_value(value: str) -> str:
    """
    Create a one-way hash of a value (for comparison without storing plaintext)
    
    Args:
        value: String to hash
        
    Returns:
        Hex-encoded hash
    """
    import hashlib
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


# Utility functions for OAuth state
def create_oauth_state(workspace_id: str, source: str, user_id: str) -> str:
    """
    Create a secure OAuth state parameter
    
    Args:
        workspace_id: Workspace ID
        source: Integration source
        user_id: User ID
        
    Returns:
        Encrypted state string
    """
    import json
    import time
    
    state_data = {
        'workspace_id': workspace_id,
        'source': source,
        'user_id': user_id,
        'timestamp': int(time.time()),
        'nonce': base64.b64encode(os.urandom(16)).decode('utf-8')
    }
    
    state_json = json.dumps(state_data)
    return encrypt(state_json)


def verify_oauth_state(state: str, max_age_seconds: int = 600) -> Optional[dict]:
    """
    Verify and decode OAuth state parameter
    
    Args:
        state: Encrypted state string
        max_age_seconds: Maximum age of state (default 10 minutes)
        
    Returns:
        Decoded state data or None if invalid
    """
    import json
    import time
    
    try:
        decrypted = decrypt(state)
        if not decrypted:
            return None
        
        state_data = json.loads(decrypted)
        
        # Check age
        current_time = int(time.time())
        state_time = state_data.get('timestamp', 0)
        
        if current_time - state_time > max_age_seconds:
            return None
        
        return state_data
    except Exception:
        return None