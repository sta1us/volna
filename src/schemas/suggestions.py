from datetime import datetime
from typing import Optional

from common.models import SuggestionStatus
from pydantic import BaseModel, ConfigDict, Field


class SuggestionCreate(BaseModel):
    """Схема для отправки нового предложения, идеи или жалобы."""

    guest_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Имя гостя (обязательно для неавторизованных пользователей)",
        examples=["Дмитрий"],
    )
    guest_contact: Optional[str] = Field(
        None,
        min_length=5,
        max_length=100,
        description="Контактные данные (телефон, email или @username для связи)",
        examples=["+7 (999) 555-44-33"],
    )
    subject: str = Field(
        default="Без темы",
        max_length=150,
        description="Тема обращения",
        examples=["Жалоба на обслуживание"],
    )
    text: str = Field(
        ...,
        min_length=10,
        max_length=3000,
        description="Детальный текст предложения или жалобы (от 10 до 3000 символов)",
        examples=["В прошлую пятницу долго не несли меню, разберитесь, пожалуйста."],
    )


class SuggestionRead(BaseModel):
    """Схема для чтения обращений внутри панели администратора (Полные данные)."""

    id: int = Field(..., description="Уникальный ID обращения")
    user_id: Optional[int] = Field(
        None, description="ID пользователя в системе (если авторизован)"
    )
    guest_name: Optional[str] = Field(None, description="Имя автора обращения")
    guest_contact: Optional[str] = Field(
        None, description="Контактные данные для ответа"
    )
    subject: str = Field(..., description="Тема обращения")
    text: str = Field(..., description="Текст обращения")
    is_read: bool = Field(..., description="Флаг прочтения администратором")
    status: SuggestionStatus = Field(..., description="Текущий статус обработки")
    created_at: datetime = Field(..., description="Дата и время отправки (UTC)")
    model_config = ConfigDict(from_attributes=True)


class SuggestionStatusUpdate(BaseModel):
    """Схема для перевода обращения на новые этапы обработки."""

    status: SuggestionStatus = Field(
        ..., description="Новый статус обращения (например: APPROVED, REJECTED, etc.)"
    )
