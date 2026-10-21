from pydantic_settings import BaseSettings
from pydantic import validator, Field
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./cmssync.db"

    # Security - Token Encryption
    encryption_key: str = Field(
        ...,
        description="Fernet encryption key for API tokens (base64, 32 bytes). "
                    "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    )

    # API Settings
    api_prefix: str = "/api"

    # Data Storage
    data_dir: Path = Path("data")
    instances_data_dir: Path = Path("data/instances")

    # CORS Origins
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Magento API Settings
    magento_timeout: int = 30
    magento_retry_attempts: int = 3
    magento_retry_delay: int = 1

    # JSON Storage Settings
    json_indent: int = 2
    json_ensure_ascii: bool = False

    @validator('encryption_key')
    def validate_encryption_key(cls, v):
        """Validate encryption key format and length."""
        if not v or len(v) < 32:
            raise ValueError(
                "ENCRYPTION_KEY must be set and at least 32 characters. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()