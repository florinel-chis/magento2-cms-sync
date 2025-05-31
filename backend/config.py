from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./cmssync.db"
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()