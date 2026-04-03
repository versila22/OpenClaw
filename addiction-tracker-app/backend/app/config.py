from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Addiction Tracker API"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./addiction_tracker.db"
    CORS_ORIGINS: list[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]
    CSAPA_DIRECTORY_URL: str = "https://www.drogues-info-service.fr/Adresses-utiles"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
