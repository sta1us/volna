from typing import Optional

from pydantic import BaseModel, Field


class UserShort(BaseModel):
    """Короткая информация о пользователе для списков участников внутри аналитики."""

    id: int = Field(..., description="Внутренний ID пользователя в системе")
    tg_id: Optional[int] = Field(None, description="Telegram ID пользователя")
    username: Optional[str] = Field(
        None, description="Юзернейм в Telegram (без @)", examples=["ivan_customer"]
    )
    first_name: Optional[str] = Field(
        None, description="Имя, указанное в мессенджере", examples=["Иван"]
    )

    class Config:
        from_attributes = True


class ReactionStats(BaseModel):
    """Агрегированная статистика по конкретному типу реакции."""

    count: int = Field(
        ...,
        description="Количество пользователей, выбравших этот статус",
        examples=[15],
    )
    users: list[UserShort] = Field(
        ..., description="Список детализированных объектов пользователей"
    )


class EventFullStats(BaseModel):
    """Полный срез аналитики реакций пользователей на конкретное мероприятие."""

    event_id: int = Field(..., description="Уникальный ID события")
    event_title: str = Field(
        ..., description="Название события", examples=["Пятничный StandUp & Lounge"]
    )
    going: ReactionStats = Field(
        ..., description="Метрики пользователей, которые точно придут"
    )
    maybe: ReactionStats = Field(
        ..., description="Метрики пользователей, которые выбрали 'Возможно'"
    )
    not_going: ReactionStats = Field(
        ..., description="Метрики пользователей, которые отказались от посещения"
    )


class GeneralStatsRead(BaseModel):
    """Ответ для главного экрана аналитики (Счетчики дашборда администратора)."""

    pendingReviews: int = Field(
        ...,
        description="Количество отзывов гостей, ожидающих проверки модератором",
        examples=[4],
    )
    newSuggestions: int = Field(
        ...,
        description="Количество новых предложений/жалоб со статусом PENDING",
        examples=[12],
    )
    totalEvents: int = Field(
        ...,
        description="Общее количество созданных в системе мероприятий (архив + будущие)",
        examples=[42],
    )
