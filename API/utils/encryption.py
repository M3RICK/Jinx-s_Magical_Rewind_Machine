import os
import hashlib
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


class PUUIDEncryption:
    def __init__(self):
        encryption_key = os.getenv("PUUID_ENCRYPTION_KEY")

        if not encryption_key:
            raise ValueError(
                "PUUID_ENCRYPTION_KEY not found in .env file. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()

        self.fernet = Fernet(encryption_key)

    def encrypt_puuid(self, puuid: str) -> str:
        if not puuid:
            raise ValueError("PUUID cannot be empty")

        encrypted = self.fernet.encrypt(puuid.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_puuid(self, encrypted_puuid: str) -> str:
        if not encrypted_puuid:
            raise ValueError("Encrypted PUUID cannot be empty")

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_puuid.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt PUUID: {e}")

    @staticmethod
    def hash_puuid(puuid: str) -> str:
        if not puuid:
            raise ValueError("PUUID cannot be empty...duh")
        return hashlib.sha256(puuid.encode()).hexdigest()


def generate_encryption_key():
    return Fernet.generate_key().decode()


if __name__ == "__main__":
    print("Generated encryption key:")
    print(generate_encryption_key())
    print("\nAdd to .env as: PUUID_ENCRYPTION_KEY=<key>")
