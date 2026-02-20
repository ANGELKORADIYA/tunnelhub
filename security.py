"""
Security module for RSA encryption and password verification.
Handles RSA key generation, encryption, and decryption for secure password transmission.
Supports both file-based keys (local) and in-memory keys (Vercel/serverless).
"""

import os
import secrets
import base64
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

# Detect if running in serverless environment (Vercel, etc.)
IS_SERVERLESS = os.environ.get('VERCEL') == '1' or os.environ.get('AWS_LAMBDA_FUNCTION_VERSION') is not None

# Keys directory (only used for local development)
KEYS_DIR = Path(__file__).parent / "keys"
PRIVATE_KEY_PATH = KEYS_DIR / "private_key.pem"
PUBLIC_KEY_PATH = KEYS_DIR / "public_key.pem"

# In-memory key storage for serverless environments
_in_memory_private_key = None
_in_memory_public_key_pem = None


def generate_rsa_key_pair(key_size: int = 2048) -> tuple:
    """
    Generate RSA key pair and save to files (or store in memory for serverless).

    Args:
        key_size: RSA key size in bits (default: 2048)

    Returns:
        Tuple of (private_key, public_key_pem)
    """
    global _in_memory_private_key, _in_memory_public_key_pem

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )

    # Generate public key
    public_key = private_key.public_key()

    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Store in memory for serverless environments
    if IS_SERVERLESS:
        _in_memory_private_key = private_key
        _in_memory_public_key_pem = public_pem.decode('utf-8')
        print(f"✅ RSA key pair generated in memory ({key_size}-bit)")
        return private_key, _in_memory_public_key_pem

    # Save to files for local development
    try:
        KEYS_DIR.mkdir(exist_ok=True)
        with open(PRIVATE_KEY_PATH, 'wb') as f:
            f.write(private_pem)
        with open(PUBLIC_KEY_PATH, 'wb') as f:
            f.write(public_pem)
        print(f"✅ RSA key pair generated and saved ({key_size}-bit)")
        print(f"   Private key: {PRIVATE_KEY_PATH}")
        print(f"   Public key: {PUBLIC_KEY_PATH}")
    except (OSError, IOError) as e:
        # Fallback to in-memory if file write fails
        print(f"⚠️ Could not write keys to file: {e}")
        print(f"✅ Using in-memory key storage instead")
        _in_memory_private_key = private_key
        _in_memory_public_key_pem = public_pem.decode('utf-8')

    return private_key, public_pem.decode('utf-8')


def get_public_key_pem() -> str:
    """
    Get the public key in PEM format as a string.

    Returns:
        Public key in PEM format

    Raises:
        FileNotFoundError: If public key is not available
    """
    global _in_memory_public_key_pem

    # Check in-memory storage first (serverless)
    if _in_memory_public_key_pem:
        return _in_memory_public_key_pem

    # Try to load from environment variable (for Vercel)
    env_public_key = os.environ.get('RSA_PUBLIC_KEY')
    if env_public_key:
        return env_public_key

    # Try to load from file (local development)
    if PUBLIC_KEY_PATH.exists():
        with open(PUBLIC_KEY_PATH, 'rb') as f:
            return f.read().decode('utf-8')

    raise FileNotFoundError("Public key not found. Please generate keys first or set RSA_PUBLIC_KEY environment variable.")


def load_private_key():
    """
    Load the private key from memory, environment, or file.

    Returns:
        RSA private key object

    Raises:
        FileNotFoundError: If private key is not available
    """
    global _in_memory_private_key

    # Check in-memory storage first (serverless)
    if _in_memory_private_key:
        return _in_memory_private_key

    # Try to load from environment variable (for Vercel)
    env_private_key = os.environ.get('RSA_PRIVATE_KEY')
    if env_private_key:
        private_key = serialization.load_pem_private_key(
            env_private_key.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        return private_key

    # Try to load from file (local development)
    if PRIVATE_KEY_PATH.exists():
        with open(PRIVATE_KEY_PATH, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        return private_key

    raise FileNotFoundError("Private key not found. Please generate keys first or set RSA_PRIVATE_KEY environment variable.")


def decrypt_password(encrypted_password_b64: str) -> str:
    """
    Decrypt a password that was encrypted with the public key.

    Args:
        encrypted_password_b64: Base64-encoded encrypted password

    Returns:
        Decrypted password as string

    Raises:
        ValueError: If decryption fails
    """
    try:
        # Load private key
        private_key = load_private_key()

        # Decode base64
        encrypted_bytes = base64.b64decode(encrypted_password_b64)

        # Decrypt
        decrypted_bytes = private_key.decrypt(
            encrypted_bytes,
            padding.PKCS1v15()
        )

        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt password: {str(e)}")


def verify_password(password: str, stored_password: str) -> bool:
    """
    Verify a password using constant-time comparison.

    Args:
        password: Password to verify
        stored_password: Stored password to compare against

    Returns:
        True if passwords match, False otherwise
    """
    return secrets.compare_digest(password, stored_password)


def ensure_keys_exist(key_size: int = 2048) -> None:
    """
    Ensure RSA keys exist, generate them if they don't.
    For serverless environments, always generates keys in memory.

    Args:
        key_size: RSA key size in bits (default: 2048)
    """
    global _in_memory_private_key, _in_memory_public_key_pem

    # Check if keys are already in memory
    if _in_memory_private_key and _in_memory_public_key_pem:
        print("✅ RSA keys found in memory")
        return

    # Check if keys are in environment variables (Vercel deployment)
    if os.environ.get('RSA_PRIVATE_KEY') and os.environ.get('RSA_PUBLIC_KEY'):
        print("✅ RSA keys found in environment variables")
        # Load them into memory for faster access
        try:
            env_private_key = os.environ.get('RSA_PRIVATE_KEY')
            _in_memory_private_key = serialization.load_pem_private_key(
                env_private_key.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            _in_memory_public_key_pem = os.environ.get('RSA_PUBLIC_KEY')
        except Exception as e:
            print(f"⚠️ Failed to load keys from environment: {e}")

    # For serverless or when keys don't exist, generate new ones
    if IS_SERVERLESS or not _in_memory_private_key:
        print("🔐 Generating new RSA key pair...")
        generate_rsa_key_pair(key_size)
    else:
        print("✅ RSA keys found")


def generate_session_token() -> str:
    """
    Generate a secure random session token.

    Returns:
        Secure random token as hex string
    """
    return secrets.token_hex(32)


if __name__ == "__main__":
    # Test key generation
    print("Testing RSA key generation...")
    ensure_keys_exist(2048)
    print("\nPublic Key PEM:")
    print(get_public_key_pem())
