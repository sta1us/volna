from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from common.models import ReviewStatus


class ReviewCreate(BaseModel):
    """Схема для отправки нового отзыва пользователем или гостем."""

    text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Текст отзыва (от 10 до 2000 символов)",
        examples=["Отличное заведение! Повар превзошел все ожидания, стейки сочные."],
    )
    rating: int = Field(
        5,
        ge=1,
        le=5,
        description="Оценка работы заведения по пятибалльной шкале",
        examples=[5],
    )
    is_anonymous: bool = Field(
        False,
        description="Флаг анонимности. Если true, имя пользователя скрывается на публичной витрине",
    )
    guest_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Имя гостя (обязательно, если пользователь не авторизован)",
        examples=["Александр"],
    )
    guest_contact: Optional[str] = Field(
        None,
        max_length=100,
        description="Телефон или Email гостя для обратной связи администрации (не публикуется)",
        examples=["+7 (999) 111-22-33"],
    )


class ReviewRead(BaseModel):
    """Публичная схема ответа для отображения отзывов на сайте (Безопасная)."""

    id: int = Field(..., description="ID отзыва")
    guest_name: Optional[str] = Field(
        None, description="Имя автора (для гостей или неанонимных пользователей)"
    )
    text: str = Field(..., description="Модерированный текст отзыва")
    rating: int = Field(..., description="Оценка")
    created_at: datetime = Field(..., description="Дата публикации (UTC)")

    class Config:
        from_attributes = True


class AdminReviewRead(BaseModel):
    """Расширенная схема ответа исключительно для панели администратора (Включает персональные данные)."""

    id: int = Field(..., description="ID отзыва")
    user_id: Optional[int] = Field(
        None, description="Внутренний ID пользователя (если авторизован)"
    )
    guest_name: Optional[str] = Field(
        None, description="Имя гостя или имя пользователя из профиля"
    )
    guest_contact: Optional[str] = Field(
        None, description="Личные контактные данные для связи"
    )
    text: str = Field(..., description="Исходный текст отзыва")
    rating: int = Field(..., description="Оценка")
    status: ReviewStatus = Field(
        ..., description="Текущий статус модерации (pending/approved/rejected)"
    )
    is_anonymous: bool = Field(
        ..., description="Просил ли пользователь скрыть его профиль на сайте"
    )
    created_at: datetime = Field(..., description="Дата создания отзыва")

    class Config:
        from_attributes = True


class ReviewStatusUpdate(BaseModel):
    """Схема модерации отзыва администратором."""

    status: ReviewStatus = Field(
        ...,
        description="Новый статус отзыва. Разрешены: APPROVED (одобрить) или REJECTED (отклонить).",
    )
