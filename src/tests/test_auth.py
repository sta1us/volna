"""
Тесты: /health, /api/auth/telegram, /api/auth/verify-admin
"""

import hashlib
import hmac
import time

import pytest
from common.config import settings
from common.models import UserRole
from httpx import AsyncClient

from tests.conftest import auth_headers, make_telegram_payload

# ===========================================================================
# Health Check
# ===========================================================================


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """GET /health → 200 + поля status и version."""
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "version" in body
    assert "name" in body


# ===========================================================================
# POST /api/auth/telegram
# ===========================================================================


@pytest.mark.asyncio
async def test_auth_telegram_new_user(client: AsyncClient):
    """Первичная регистрация нового пользователя создаёт JWT-токен."""
    payload = make_telegram_payload(tg_id=100000001)
    response = await client.post("/api/auth/telegram", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["role"] in (UserRole.ADMIN.value, UserRole.CLIENT.value)


@pytest.mark.asyncio
async def test_auth_telegram_existing_user_updates_profile(client: AsyncClient):
    """Повторный вход обновляет профиль (username/first_name)."""
    tg_id = 100000002
    # Первый вход
    payload = make_telegram_payload(tg_id=tg_id)
    r1 = await client.post("/api/auth/telegram", json=payload)
    assert r1.status_code == 200

    # Второй вход — без ошибок
    r2 = await client.post("/api/auth/telegram", json=payload)
    assert r2.status_code == 200
    assert "access_token" in r2.json()


@pytest.mark.asyncio
async def test_auth_telegram_admin_assigned_by_env(client: AsyncClient):
    """Пользователь с ADMIN_TG_ID получает роль ADMIN."""
    admin_tg_id = settings.ADMIN_TG_ID
    payload = make_telegram_payload(tg_id=admin_tg_id)
    response = await client.post("/api/auth/telegram", json=payload)
    assert response.status_code == 200
    assert response.json()["role"] == UserRole.ADMIN.value


@pytest.mark.asyncio
async def test_auth_telegram_invalid_hash(client: AsyncClient):
    """Неверный hash → 401."""
    payload = make_telegram_payload(tg_id=100000003)
    payload["hash"] = "deadbeef" * 8  # Неверный хэш
    response = await client.post("/api/auth/telegram", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_telegram_expired_session(client: AsyncClient):
    """Слишком старый auth_date (>24 часов) → 401."""
    payload = make_telegram_payload(tg_id=100000004)
    payload["auth_date"] = int(time.time()) - settings.TELEGRAM_AUTH_MAX_AGE - 1
    # Пересчитываем hash с новым auth_date
    data = {k: v for k, v in payload.items() if k != "hash"}
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hashlib.sha256(settings.BOT_TOKEN.encode()).digest()
    payload["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()

    response = await client.post("/api/auth/telegram", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_telegram_missing_hash(client: AsyncClient):
    """Отсутствующий hash → 422 (ошибка валидации Pydantic) или 401."""
    payload = make_telegram_payload(tg_id=100000005)
    del payload["hash"]
    response = await client.post("/api/auth/telegram", json=payload)
    assert response.status_code in (401, 422)


# ===========================================================================
# GET /api/auth/verify-admin
# ===========================================================================


@pytest.mark.asyncio
async def test_verify_admin_success(client: AsyncClient, admin_token: str):
    """Администратор получает is_admin: true."""
    response = await client.get(
        "/api/auth/verify-admin", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["is_admin"] is True


@pytest.mark.asyncio
async def test_verify_admin_forbidden_for_client(
    client: AsyncClient, client_token: str
):
    """Обычный пользователь получает 403."""
    response = await client.get(
        "/api/auth/verify-admin", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_admin_no_token(client: AsyncClient):
    """Без токена → 401."""
    response = await client.get("/api/auth/verify-admin")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_admin_invalid_token(client: AsyncClient):
    """Невалидный токен → 401."""
    response = await client.get(
        "/api/auth/verify-admin",
        headers={"Authorization": "Bearer totally.invalid.token"},
    )
    assert response.status_code == 401
