import json
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./cmssync.db"
    
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