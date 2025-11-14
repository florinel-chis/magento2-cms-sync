"""
Token encryption utilities for secure storage.

Uses Fernet (symmetric encryption) for encrypting API tokens at rest.
Requires ENCRYPTION_KEY environment variable to be set.
"""
import logging
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional

logger = logging.getLogger(__name__)


class TokenEncryption:
    """Handle encryption and decryption of API tokens."""

    def __init__(self, encryption_key: str):
        """
        Initialize token encryption with a key.

        Args:
            encryption_key: Base64-encoded Fernet key (32 bytes)

        Raises:
            ValueError: If encryption key is invalid
        """
        try:
            self._fernet = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, token: str) -> str:
        """
        Encrypt an API token.

        Args:
            token: Plaintext API token

        Returns:
            Encrypted token as base64 string

        Raises:
            ValueError: If encryption fails
        """
        if not token:
            raise ValueError("Token cannot be empty")

        try:
            encrypted_bytes = self._fernet.encrypt(token.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt token: {e}", exc_info=True)
            raise ValueError(f"Encryption failed: {e}")

    def decrypt(self, encrypted_token: str) -> str:
        """
        Decrypt an API token.

        Args:
            encrypted_token: Encrypted token as base64 string

        Returns:
            Decrypted plaintext token

        Raises:
            ValueError: If decryption fails (invalid token or wrong key)
        """
        if not encrypted_token:
            raise ValueError("Encrypted token cannot be empty")

        try:
            decrypted_bytes = self._fernet.decrypt(encrypted_token.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            logger.error("Failed to decrypt token: invalid token or wrong key")
            raise ValueError("Invalid encrypted token or decryption key")
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}", exc_info=True)
            raise ValueError(f"Decryption failed: {e}")

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded encryption key as string

        Usage:
            from utils.encryption import TokenEncryption
            key = TokenEncryption.generate_key()
            print(f"Add to .env: ENCRYPTION_KEY={key}")
        """
        return Fernet.generate_key().decode()


# Singleton instance (initialized in main.py after settings are loaded)
_token_encryption: Optional[TokenEncryption] = None


def initialize_encryption(encryption_key: str) -> None:
    """
    Initialize global token encryption instance.

    Should be called once during application startup.

    Args:
        encryption_key: Base64-encoded Fernet key from settings
    """
    global _token_encryption
    _token_encryption = TokenEncryption(encryption_key)
    logger.info("Token encryption initialized")


def get_encryption() -> TokenEncryption:
    """
    Get the global token encryption instance.

    Returns:
        TokenEncryption instance

    Raises:
        RuntimeError: If encryption not initialized
    """
    if _token_encryption is None:
        raise RuntimeError(
            "Token encryption not initialized. "
            "Call initialize_encryption() during startup."
        )
    return _token_encryption


def encrypt_token(token: str) -> str:
    """Convenience function to encrypt a token."""
    return get_encryption().encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """Convenience function to decrypt a token."""
    return get_encryption().decrypt(encrypted_token)
