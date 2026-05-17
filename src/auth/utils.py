import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwt

from common.config import settings


def create_access_token(data: dict) -> str:
    """
    Генерирует безопасный JWT access-токен.

    Принимает словарь с полезной нагрузкой (payload), добавляет таймштамп
    истечения срока действия (с учетом UTC) и подписывает секретным ключом.
    """
    # Создаем новый payload, изолируя данные
    to_encode = {**data}

    # Используем строгое явное указание таймзоны UTC
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Записываем стандартный claim "exp" (должен быть int timestamp или datetime с tz)
    to_encode.update({"exp": expire})

    # Кодируем токен
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_telegram_auth(data: Dict[str, Any]) -> bool:
    """
    Проверяет подлинность данных авторизации Telegram с помощью HMAC-SHA256.

    :param data: Словарь с данными от Telegram (включая auth_date и hash).
    :return: True, если данные подлинны, иначе False.
    """
    bot_token = settings.BOT_TOKEN
    # 1. Извлекаем хэш, который прислал клиент, его мы не включаем в строку подписи
    received_hash = data.get("hash")
    if not received_hash:
        return False

    # 2. Собираем все остальные ключи, сортируем их по алфавиту
    # и формируем строку в формате key=<value>, разделенную переносом строки (\n)
    data_check_list = []
    for key, value in sorted(data.items()):
        if key != "hash" and value is not None:
            data_check_list.append(f"{key}={value}")

    data_check_string = "\n".join(data_check_list)

    # 3. Вычисляем секретный ключ: SHA256 от токена бота
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # 4. Вычисляем HMAC-SHA256 от нашей строки данных с использованием секретного ключа
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    # 5. Безопасно сравниваем хэши (hmac.compare_digest защищает от атак по времени / Timing Attacks)
    return hmac.compare_digest(computed_hash, received_hash)
