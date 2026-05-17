from typing import Optional

from pydantic import BaseModel, Field

from common.models import UserRole


class UsersRead(BaseModel):
    """Схема для отображения полной информации о пользователе в админ-панели."""

    id: int = Field(..., description="Внутренний ID пользователя в системе")
    role: UserRole = Field(
        ..., description="Системная роль пользователя (ADMIN / CLIENT)"
    )
    tg_id: Optional[int] = Field(None, description="Уникальный Telegram ID аккаунта")
    username: Optional[str] = Field(
        None, description="Юзернейм в мессенджере (без @)", examples=["alex_manager"]
    )
    first_name: Optional[str] = Field(
        None, description="Имя пользователя из Telegram", examples=["Алексей"]
    )

    class Config:
        # ИСПРАВЛЕНО: Добавлен конфигурационный класс для автоматического парсинга SQLAlchemy-моделей
        from_attributes = True


class UsersRoleUpdate(BaseModel):
    """Схема для изменения уровня привилегий (роли) пользователя."""

    role: UserRole = Field(
        ...,
        description="Новая роль, назначаемая пользователю (например, перевод клиента в администраторы)",
    )
