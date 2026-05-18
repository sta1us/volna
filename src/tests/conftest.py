"""
Конфигурация и фикстуры для тестов Volna API.
"""

import hashlib
import hmac
import os
import time
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Устанавливаем тестовые переменные окружения ДО импорта приложения
os.environ.setdefault("BOT_TOKEN", "1234567890:test_bot_token_for_testing_only")
os.environ.setdefault("ADMIN_TG_ID", "999999999")
os.environ.setdefault("DOMAIN", "http://localhost:3000")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("DB_URL", "sqlite+aiosqlite:///:memory:")

from common.config import settings  # noqa: E402
from common.database import get_db  # noqa: E402
from common.models import Base, User, UserRole  # noqa: E402
from src.auth.utils import create_access_token  # noqa: E402
from src.main import app  # noqa: E402

# ---------------------------------------------------------------------------
# База данных в памяти для тестов
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def create_test_tables():
    """Создаёт все таблицы перед каждым тестом и удаляет после."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Открывает тестовую сессию БД и откатывает изменения после каждого теста."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient с подменённой зависимостью get_db на тестовую сессию."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Фабрики пользователей
# ---------------------------------------------------------------------------


def make_token(user: User) -> str:
    payload = {"sub": str(user.id), "tg_id": user.tg_id, "role": user.role.value}
    return create_access_token(payload)


@pytest_asyncio.fixture()
async def client_user(db_session: AsyncSession) -> User:
    """Обычный пользователь (CLIENT)."""
    user = User(
        tg_id=111111111, username="testuser", first_name="Test", role=UserRole.CLIENT
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def admin_user(db_session: AsyncSession) -> User:
    """Пользователь с правами ADMIN."""
    user = User(
        tg_id=222222222, username="adminuser", first_name="Admin", role=UserRole.ADMIN
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture()
def client_token(client_user: User) -> str:
    return make_token(client_user)


@pytest.fixture()
def admin_token(admin_user: User) -> str:
    return make_token(admin_user)


# ---------------------------------------------------------------------------
# Вспомогательные утилиты
# ---------------------------------------------------------------------------


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_telegram_payload(tg_id: int = 123456789, bot_token: str | None = None) -> dict:
    """Генерирует корректный Telegram-payload с валидным hash."""
    bot_token = bot_token or settings.BOT_TOKEN
    auth_date = int(time.time())
    data = {
        "id": tg_id,
        "first_name": "Иван",
        "username": "ivan_test",
        "auth_date": auth_date,
    }
    data_check_list = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(data_check_list)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    data["hash"] = computed_hash
    return data
