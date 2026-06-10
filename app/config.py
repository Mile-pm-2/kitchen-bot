import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = ""
    admin_telegram_id: int = 0
    webapp_url: str = "http://localhost:8000"
    api_port: int = int(os.getenv("PORT", "8000"))
    secret_key: str = "dev-secret-key"
    database_url: str = "sqlite+aiosqlite:///./kitchen.db"
    webhook_mode: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
