import json
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

KEY_HINT = ("Generate one with: python -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())' and set ENCRYPTION_KEY in the environment or backend/.env")


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./cmssync.db"

    # Security - Token Encryption (Fernet key, base64, 44 characters)
    encryption_key: str = Field(..., description=f"Fernet key used to encrypt Magento API tokens at rest. {KEY_HINT}")

    # Data Storage
    data_dir: Path = Path("data")
    instances_data_dir: Path = Path("data/instances")

    # CORS Origins: comma-separated string or JSON list (see cors_origin_list)
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Magento API Settings
    magento_timeout: int = 30
    magento_retry_attempts: int = 3
    magento_retry_delay: int = 1

    # JSON Storage Settings
    json_indent: int = 2
    json_ensure_ascii: bool = False

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, value: str) -> str:
        """A Fernet key is 44 base64 characters; reject anything that cannot be one."""
        if not value or len(value) < 32:
            raise ValueError(f"ENCRYPTION_KEY must be a Fernet key. {KEY_HINT}")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS_ORIGINS parsed into a list; accepts 'a,b' as well as '["a","b"]'."""
        value = self.cors_origins.strip()
        if value.startswith("["):
            return [str(origin) for origin in json.loads(value)]
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # obsolete keys in an existing .env must not prevent startup


settings = Settings()
