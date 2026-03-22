#!/usr/bin/env python3
"""
NeuroRift Cryptography Module
Provides encryption and secure credential storage
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from base64 import b64encode, b64decode

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.backends import default_backend

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning(
        "cryptography library not available. Install with: pip install cryptography"
    )

from utils.security_utils import FilePermissionManager

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages encrypted credential storage"""

    def __init__(self, credentials_dir: Optional[Path] = None):
        """Initialize credential manager

        Args:
            credentials_dir: Directory to store encrypted credentials
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError(
                "cryptography library required. Install with: pip install cryptography"
            )

        if credentials_dir is None:
            credentials_dir = Path.home() / ".neurorift" / "credentials"

        self.credentials_dir = Path(credentials_dir)
        FilePermissionManager.create_secure_directory(self.credentials_dir, mode=0o700)

        self.credentials_file = self.credentials_dir / "credentials.enc"
        self.key_file = self.credentials_dir / ".key"

        self.cipher = self._initialize_cipher()
        self.credentials: Dict[str, str] = {}

        self._load_credentials()

    def _initialize_cipher(self) -> Fernet:
        """Initialize or load encryption cipher"""
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()

            with open(self.key_file, "wb") as f:
                f.write(key)

            FilePermissionManager.set_secure_permissions(self.key_file, mode=0o600)
            logger.info("Generated new encryption key")

        return Fernet(key)

    def _load_credentials(self) -> None:
        """Load and decrypt credentials from file"""
        if not self.credentials_file.exists():
            return

        try:
            with open(self.credentials_file, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)
            self.credentials = json.loads(decrypted_data.decode("utf-8"))

            logger.info("Loaded %d credentials", len(self.credentials))

        except Exception as e:
            logger.error("Error loading credentials: %s", e)
            self.credentials = {}

    def _save_credentials(self) -> None:
        """Encrypt and save credentials to file"""
        try:
            # Convert to JSON
            json_data = json.dumps(self.credentials, indent=2)

            # Encrypt
            encrypted_data = self.cipher.encrypt(json_data.encode("utf-8"))

            # Save to file
            with open(self.credentials_file, "wb") as f:
                f.write(encrypted_data)

            FilePermissionManager.set_secure_permissions(
                self.credentials_file, mode=0o600
            )

            logger.info("Saved %d credentials", len(self.credentials))

        except Exception as e:
            logger.error("Error saving credentials: %s", e)

    def set_credential(self, key: str, value: str) -> bool:
        """Store encrypted credential

        Args:
            key: Credential key (e.g., 'openai_api_key')
            value: Credential value

        Returns:
            True if successful, False otherwise
        """
        try:
            self.credentials[key] = value
            self._save_credentials()
            logger.info("Stored credential: %s", key)
            return True
        except Exception as e:
            logger.error("Error storing credential %s: %s", key, e)
            return False

    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve decrypted credential

        Args:
            key: Credential key

        Returns:
            Credential value or None if not found
        """
        return self.credentials.get(key)

    def delete_credential(self, key: str) -> bool:
        """Delete credential

        Args:
            key: Credential key

        Returns:
            True if successful, False otherwise
        """
        if key in self.credentials:
            del self.credentials[key]
            self._save_credentials()
            logger.info("Deleted credential: %s", key)
            return True

        return False

    def list_credentials(self) -> list:
        """List all credential keys (not values)

        Returns:
            List of credential keys
        """
        return list(self.credentials.keys())

    def import_from_env(self, env_vars: Dict[str, str]) -> int:
        """Import credentials from environment variables

        Args:
            env_vars: Dictionary of environment variable names to credential keys

        Returns:
            Number of credentials imported
        """
        count = 0

        for env_var, cred_key in env_vars.items():
            value = os.getenv(env_var)
            if value:
                self.set_credential(cred_key, value)
                count += 1

        logger.info("Imported %d credentials from environment", count)
        return count

    def export_to_env_file(self, output_file: Path) -> bool:
        """Export credentials to .env file format

        Args:
            output_file: Path to output .env file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_file, "w") as f:
                for key, value in self.credentials.items():
                    # Convert credential key to env var format
                    env_key = key.upper().replace("-", "_")
                    f.write(f"{env_key}={value}\n")

            FilePermissionManager.set_secure_permissions(output_file, mode=0o600)
            logger.info("Exported credentials to %s", output_file)
            return True

        except Exception as e:
            logger.error("Error exporting credentials: %s", e)
            return False


class ConfigEncryption:
    """Encrypt sensitive configuration data"""

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password

        Args:
            password: Password string
            salt: Salt bytes

        Returns:
            Derived key
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography library required")

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )

        return b64encode(kdf.derive(password.encode("utf-8")))

    @staticmethod
    def encrypt_config(config_data: Dict[str, Any], password: str) -> bytes:
        """Encrypt configuration data

        Args:
            config_data: Configuration dictionary
            password: Encryption password

        Returns:
            Encrypted data
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography library required")

        # Generate salt
        salt = os.urandom(16)

        # Derive key from password
        key = ConfigEncryption.derive_key_from_password(password, salt)
        cipher = Fernet(key)

        # Convert config to JSON
        json_data = json.dumps(config_data, indent=2)

        # Encrypt
        encrypted = cipher.encrypt(json_data.encode("utf-8"))

        # Prepend salt to encrypted data
        return salt + encrypted

    @staticmethod
    def decrypt_config(encrypted_data: bytes, password: str) -> Dict[str, Any]:
        """Decrypt configuration data

        Args:
            encrypted_data: Encrypted data with prepended salt
            password: Decryption password

        Returns:
            Decrypted configuration dictionary
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography library required")

        # Extract salt (first 16 bytes)
        salt = encrypted_data[:16]
        encrypted = encrypted_data[16:]

        # Derive key from password
        key = ConfigEncryption.derive_key_from_password(password, salt)
        cipher = Fernet(key)

        # Decrypt
        decrypted = cipher.decrypt(encrypted)

        # Parse JSON
        return json.loads(decrypted.decode("utf-8"))


# Global credential manager instance
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """Get global credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager


def migrate_env_to_encrypted() -> int:
    """Migrate API keys from .env file to encrypted storage

    Returns:
        Number of credentials migrated
    """
    env_mapping = {
        "OPENAI_API_KEY": "openai_api_key",
        "GOOGLE_API_KEY": "google_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "HIBP_API_KEY": "hibp_api_key",
        "SHODAN_API_KEY": "shodan_api_key",
        "CENSYS_API_SECRET": "censys_api_secret",
        "LLAMA_MAIN_MODEL": "llama_main_model",
        "LLAMA_ASSISTANT_MODEL": "llama_assistant_model",
    }

    manager = get_credential_manager()
    return manager.import_from_env(env_mapping)
