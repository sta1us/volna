from typing import Optional

from common.models import UserRole
from pydantic import BaseModel, Field


class TelegramAuthPayload(BaseModel):
    """Схема входных данных, передаваемых виджетом авторизации Telegram или Mini App."""

    id: int = Field(
        ...,
        description="Уникальный Telegram ID пользователя (tg_id)",
        examples=[123456789],
    )
    first_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Имя пользователя, указанное в профиле Telegram",
        examples=["Иван"],
    )
    username: Optional[str] = Field(
        None,
        max_length=50,
        description="Публичный юзернейм пользователя без символа '@'",
        examples=["ivan_dev"],
    )
    last_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Имя пользователя, указанное в профиле Telegram",
        examples=["Иван"],
    )
    auth_date: int = Field(
        ...,
        description="Unix-время (timestamp) создания авторизационного хэша на стороне Telegram",
        examples=[1715889600],
    )
    hash: str = Field(
        ...,
        description="Хэш-подпись (SHA-256) параметров запроса, сгенерированная на основе токена бота",
        examples=["c9e59...78ba9f"],
    )
    photo_url: Optional[str] = Field(
        None,
        max_length=150,
        description="Ссылка на аватар, указанное в профиле Telegram",
        examples=[
            "https://t.me/i/userpic/320/eKY7RsV48pVRQn7ncwBNhRMFR347Eiad-XfP8He3Aww.jpg"
        ],
    )


class TokenResponse(BaseModel):
    """Схема успешного ответа с авторизационным токеном (Стандарт OAuth2 / Bearer)."""

    access_token: str = Field(
        ...,
        description="JWT access токен для аутентификации последующих запросов в заголовке Authorization",
    )
    token_type: str = Field(
        "bearer", description="Тип токена авторизации (всегда 'bearer')"
    )
    role: UserRole = Field(
        ...,
        description="Текущая роль пользователя в системе, определяющая его уровень доступа",
    )


class AdminVerificationResponse(BaseModel):
    """Схема ответа для валидации прав суперпользователя."""

    is_admin: bool = Field(
        True,
        description="Флаг-подтверждение. Возвращает true, если токен принадлежит администратору",
    )
