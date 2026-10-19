from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "AI Drawing Analyzer"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database Config
    # Format: postgresql+asyncpg://user:password@localhost:5432/dbname
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/drawing_analyzer"
    
    # DB Pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()