from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, computed_field

from common.models import MediaType
from src.schemas.common import BaseMessageResponse


class UploadMediaResult(BaseModel):
    """Элемент статуса загрузки конкретного файла из пакета."""

    filename: str = Field(
        ..., description="Оригинальное имя файла с расширением", examples=["photo.jpg"]
    )
    status: str = Field(
        ...,
        description="Статус обработки файла (success / skipped)",
        examples=["success"],
    )


class UploadMediaMessageResponse(BaseMessageResponse):
    """Ответ при успешной пакетной (мультипартовой) загрузке медиафайлов."""

    uploaded: list[UploadMediaResult] = Field(
        ..., description="Список результатов обработки каждого переданного файла"
    )


class MediaRead(BaseModel):
    """Схема для отдачи медиафайла в общую галерею или альбом события."""

    id: int = Field(..., description="Уникальный ID медиафайла в СУБД")
    user_id: Optional[int] = Field(
        None, description="ID администратора, загрузившего файл"
    )
    event_id: Optional[int] = Field(
        None, description="ID связанного события (если применимо)"
    )
    media_type: MediaType = Field(..., description="Тип контента (image / video)")
    caption: Optional[str] = Field(
        None,
        description="Текстовая подпись к медиафайлу",
        examples=["Вид на летнюю веранду"],
    )
    file_path: str = Field(..., description="Внутренний путь к файлу на сервере")
    created_at: datetime = Field(..., description="Дата и время загрузки файла (UTC)")

    @computed_field
    @property
    def media_url(self) -> str:
        """Автоматически преобразует внутренний путь во внешний веб-URL для фронтенда."""
        posix_path = Path(self.file_path).as_posix()
        return f"/{posix_path}" if not posix_path.startswith("/") else posix_path

    class Config:
        from_attributes = True


class MediaUploadPayload(BaseModel):
    """Схема валидации текстовых метаданных при пакетной загрузке."""

    event_id: Optional[int] = Field(
        None,
        description="ID события, если файлы загружаются целенаправленно в его альбом",
    )
    caption: Optional[str] = Field(
        None,
        max_length=200,
        description="Короткая текстовая подпись для всех файлов из текущего пакета (до 200 символов)",
    )
