import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    ENV: str = Field(default="dev", validation_alias="ENV")
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # Project Paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    
    # We define these as properties or post-initialized fields to handle directories dynamically
    @property
    def DATA_DIR(self) -> Path:
        path = self.PROJECT_ROOT / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def CACHE_DIR(self) -> Path:
        path = self.DATA_DIR / "cache"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def LOG_DIR(self) -> Path:
        path = self.PROJECT_ROOT / "backend" / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # Database URL
    DATABASE_URL: str = Field(default="", validation_alias="DATABASE_URL")

    # API Keys
    GEMINI_API_KEY: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    GROQ_API_KEY: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    OPENROUTER_API_KEY: str | None = Field(default=None, validation_alias="OPENROUTER_API_KEY")
    OLLAMA_HOST: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_HOST")
    FRED_API_KEY: str | None = Field(default=None, validation_alias="FRED_API_KEY")

    # Settings configuration
    model_config = SettingsConfigDict(
        env_file=os.path.join(Path(__file__).resolve().parent.parent.parent, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        # Set default DATABASE_URL pointing to the data folder if not provided
        if not self.DATABASE_URL:
            db_path = self.DATA_DIR / "aegis.db"
            self.DATABASE_URL = f"sqlite:///{db_path.as_posix()}"

# Global settings instance
settings = Settings()
