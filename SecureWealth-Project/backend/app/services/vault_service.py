import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from backend.app.config import get_settings

logger = logging.getLogger("securewealth.vault")
settings = get_settings()

class VaultService:
    """
    Secure Credential Management Service.
    Implements a HashiCorp Vault-like interface for managing sensitive API keys,
    Blockchain private keys, and Account Aggregator credentials.
    """

    def __init__(self):
        # In production, this would be the Vault Master Key / Unseal Key
        # Here we use a key derived from the app settings
        secret = settings.SECRET_KEY[:32].ljust(32, "0")
        self.fernet = Fernet(base64.urlsafe_b64encode(secret.encode()))
        
        # Local storage for encrypted secrets (simulating a Vault KV engine)
        self.secret_dir = "secure_vault"
        if not os.path.exists(self.secret_dir):
            os.makedirs(self.secret_dir)

    def write_secret(self, path: str, data: str):
        """Encrypt and write a secret to the vault."""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            file_path = os.path.join(self.secret_dir, path.replace("/", "_"))
            with open(file_path, "wb") as f:
                f.write(encrypted_data)
            logger.info(f"Secret written to vault: {path}")
        except Exception as e:
            logger.error(f"Vault write failed for {path}: {e}")
            raise

    def read_secret(self, path: str) -> Optional[str]:
        """Read and decrypt a secret from the vault."""
        try:
            file_path = os.path.join(self.secret_dir, path.replace("/", "_"))
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data).decode()
            return decrypted_data
        except Exception as e:
            logger.error(f"Vault read failed for {path}: {e}")
            return None

    def store_user_kyc(self, user_id: str, kyc_data: str):
        """Store sensitive KYC information in the vault."""
        self.write_secret(f"users/{user_id}/kyc", kyc_data)

    def get_blockchain_key(self, user_id: str) -> Optional[str]:
        """Retrieve a user's blockchain signing key from the vault."""
        return self.read_secret(f"users/{user_id}/eth_key")

# Global instance
vault_service = VaultService()
