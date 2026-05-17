from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Настройки Базы Данных
    DB_URL: str = "sqlite+aiosqlite:///data/database.db"

    # Домен
    DOMAIN: str

    # Настройки Telegram (берем у @BotFather)
    BOT_TOKEN: str
    ADMIN_TG_ID: int  # Твой ID, чтобы система знала, кто главный админ

    # Безопасность (для JWT токенов админки)
    JWT_SECRET_KEY: str = "super-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 сутки

    # Пути для медиа
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: str = "uploads"

    # Время жизни авторизационных данных Telegram в секундах (24 часа)
    TELEGRAM_AUTH_MAX_AGE: int = 86400

    # Позволяет считывать настройки из файла .env
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
