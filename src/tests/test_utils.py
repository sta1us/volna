"""
Тесты: утилиты (create_access_token, verify_telegram_auth)
"""

import hashlib
import hmac
import time

from common.config import settings
from jose import jwt
from src.auth.utils import create_access_token, verify_telegram_auth

# ===========================================================================
# Утилиты: create_access_token
# ===========================================================================


def test_create_access_token_returns_string():
    """create_access_token возвращает строку."""
    token = create_access_token({"sub": "1", "role": "CLIENT"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_contains_payload():
    """Payload корректно кодируется в токен."""
    payload = {"sub": "42", "role": "ADMIN", "tg_id": 123}
    token = create_access_token(payload)
    decoded = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == "42"
    assert decoded["role"] == "ADMIN"
    assert decoded["tg_id"] == 123


def test_create_access_token_has_expiration():
    """Токен содержит поле exp."""
    token = create_access_token({"sub": "1"})
    decoded = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    assert "exp" in decoded
    assert decoded["exp"] > int(time.time())


# ===========================================================================
# Утилиты: verify_telegram_auth
# ===========================================================================


def _make_valid_telegram_data(tg_id: int = 12345) -> dict:
    """Формирует данные с корректным hash для verify_telegram_auth."""
    auth_date = int(time.time())
    data = {
        "id": tg_id,
        "first_name": "Test",
        "username": "tester",
        "auth_date": auth_date,
    }
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hashlib.sha256(settings.BOT_TOKEN.encode()).digest()
    data["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return data


def test_verify_telegram_auth_valid():
    """Корректные данные возвращают True."""
    data = _make_valid_telegram_data()
    assert verify_telegram_auth(data) is True


def test_verify_telegram_auth_invalid_hash():
    """Поддельный hash возвращает False."""
    data = _make_valid_telegram_data()
    data["hash"] = "00" * 32  # Неверный хэш
    assert verify_telegram_auth(data) is False


def test_verify_telegram_auth_missing_hash():
    """Отсутствие hash возвращает False."""
    data = _make_valid_telegram_data()
    del data["hash"]
    assert verify_telegram_auth(data) is False


def test_verify_telegram_auth_tampered_data():
    """Изменение данных после подписи возвращает False."""
    data = _make_valid_telegram_data(tg_id=11111)
    data["id"] = 99999  # Подмена ID после подписи
    assert verify_telegram_auth(data) is False


def test_verify_telegram_auth_different_bot_token():
    """Данные, подписанные другим токеном бота, не проходят проверку."""
    wrong_token = "0000000000:wrong_token_for_testing"
    data = {"id": 77777, "auth_date": int(time.time()), "first_name": "Eve"}
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hashlib.sha256(wrong_token.encode()).digest()
    data["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    # Проверка будет использовать правильный токен из settings — должна вернуть False
    assert verify_telegram_auth(data) is False
