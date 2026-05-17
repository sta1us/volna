from datetime import datetime
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, Field, computed_field

from common.models import ReactionStatus
from src.schemas.common import BaseMessageResponse


class EventRead(BaseModel):
    """Схема для отображения полной информации о событии."""

    id: int = Field(
        ..., description="Уникальный ID события в базе данных", examples=[1]
    )
    title: str = Field(
        ..., description="Название мероприятия", examples=["Концерт рок-группы"]
    )
    description: str = Field(
        ...,
        description="Детальное описание события",
        examples=["Большой живой концерт..."],
    )
    date_time: datetime = Field(
        ..., description="Дата и время проведения мероприятия (UTC)"
    )
    image_path: str = Field(
        ..., description="Относительный путь к файлу афиши на сервере"
    )
    tg_file_id: Optional[str] = Field(
        None, description="ID файла в системе Telegram для ботов"
    )

    @computed_field
    @property
    def image_url(self) -> str:
        """Динамически вычисляемый абсолютный/относительный URL для фронтенда."""
        return f"/{self.image_path}"

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    """Схема Form-Data для создания нового события."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Название мероприятия (от 3 до 150 символов)",
        examples=["Фестиваль уличной еды"],
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=3000,
        description="Детальное описание (от 10 до 3000 символов)",
        examples=["Ждем всех любителей вкусной еды на центральной площади..."],
    )
    date_time: datetime = Field(
        ...,
        description="Дата и время в формате ISO-8601",
        examples=["2026-12-31T20:00:00"],
    )
    tg_file_id: Optional[str] = Field(
        None,
        description="Необязательный ID афиши внутри Telegram для кэширования ботом",
    )

    @classmethod
    def as_form(
        cls,
        title: str = Form(
            ...,
            min_length=3,
            max_length=150,
            description="Название мероприятия (от 3 до 150 символов)",
        ),
        description: str = Form(
            ...,
            min_length=10,
            max_length=3000,
            description="Детальное описание (от 10 до 3000 символов)",
        ),
        date_time: datetime = Form(
            ...,
            description="Дата и время проведения в формате ISO (например: 2026-12-31T20:00:00)",
        ),
        tg_file_id: Optional[str] = Form(
            None,
            description="Необязательный ID афиши внутри Telegram для кэширования ботом",
        ),
    ):
        return cls(
            title=title,
            description=description,
            date_time=date_time,
            tg_file_id=tg_file_id,
        )


class EventUpdate(BaseModel):
    """Схема Form-Data для обновления существующего события."""

    title: Optional[str] = Field(
        None, min_length=3, max_length=150, description="Новое название"
    )
    description: Optional[str] = Field(
        None, min_length=10, max_length=3000, description="Новое описание"
    )
    date_time: Optional[datetime] = Field(
        None, description="Новая дата и время проведения"
    )
    tg_file_id: Optional[str] = Field(None, description="Новый ID файла Telegram")

    @classmethod
    def as_form(
        cls,
        title: Optional[str] = Form(
            None, min_length=3, max_length=150, description="Новое название"
        ),
        description: Optional[str] = Form(
            None, min_length=10, max_length=3000, description="Новое описание"
        ),
        date_time: Optional[datetime] = Form(
            None, description="Новая дата и время проведения"
        ),
        tg_file_id: Optional[str] = Form(None, description="Новый ID файла Telegram"),
    ):
        return cls(
            title=title,
            description=description,
            date_time=date_time,
            tg_file_id=tg_file_id,
        )


class ReactionCreate(BaseModel):
    """Схема для установки/изменения реакции пользователя."""

    status: ReactionStatus = Field(
        ReactionStatus.GOING,
        description="Статус участия пользователя (going - пойду, maybe - возможно, not - не пойду)",
    )


class EventReactionRead(BaseModel):
    """Схема ответа после успешной установки реакции."""

    event_id: int = Field(..., description="ID события")
    user_id: int = Field(..., description="ID пользователя, оставившего отклик")
    status: ReactionStatus = Field(..., description="Текущий статус отклика")

    class Config:
        from_attributes = True


class StatMessageResponse(BaseMessageResponse):
    """Схема агрегированной статистики по откликам на событие."""

    total: int = Field(
        ..., description="Общее число уникальных пользователей, выбравших любую реакцию"
    )
    going: int = Field(
        ..., description="Количество пользователей со статусом 'пойду' (going)"
    )
    maybe: int = Field(
        ..., description="Количество пользователей со статусом 'возможно пойду' (maybe)"
    )
