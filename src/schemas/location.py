from pathlib import Path
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, EmailStr, Field, computed_field


class LocationFormPayload(BaseModel):
    """Схема Multipart-Form для создания или обновления контактных данных заведения."""

    address: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Физический адрес заведения",
        examples=["г. Москва, ул. Новый Арбат, д. 15"],
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Географическая широта для интерактивных карт (от -90 до 90)",
        examples=[55.75222],
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Географическая долгота для интерактивных карт (от -180 до 180)",
        examples=[37.61556],
    )
    working_hours: Optional[str] = Field(
        None,
        max_length=200,
        description="Режим работы заведения",
        examples=["Пн-Пт 09:00-21:00, Сб-Вс 10:00-22:00"],
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Контактный номер телефона для связи",
        examples=["+7 (495) 123-45-67"],
    )
    email: Optional[EmailStr] = Field(
        None,
        max_length=200,
        description="Официальный контактный email адрес",
        examples=["info@establishment.ru"],
    )

    @classmethod
    def as_form(
        cls,
        address: str = Form(
            ...,
            min_length=5,
            max_length=255,
            description="Физический адрес заведения",
        ),
        latitude: float = Form(
            ...,
            ge=-90.0,
            le=90.0,
            description="Географическая широта для интерактивных карт (от -90 до 90)",
        ),
        longitude: float = Form(
            ...,
            ge=-180.0,
            le=180.0,
            description="Географическая долгота для интерактивных карт (от -180 до 180)",
        ),
        working_hours: Optional[str] = Form(
            None,
            max_length=200,
            description="Режим работы заведения",
        ),
        phone: Optional[str] = Form(
            None,
            max_length=20,
            description="Контактный номер телефона для связи",
        ),
        # Примечание: В аргументе Form() мы используем str или EmailStr,
        # Pydantic при сборке класса cls() сам провалидирует структуру email.
        email: Optional[EmailStr] = Form(
            None,
            max_length=200,
            description="Официальный контактный email адрес",
        ),
    ):
        return cls(
            address=address,
            latitude=latitude,
            longitude=longitude,
            working_hours=working_hours,
            phone=phone,
            email=email,
        )


class LocationRead(BaseModel):
    """Схема ответа для отображения данных локации фронтенду."""

    id: int = Field(..., description="ID записи в СУБД")
    address: str = Field(..., description="Физический адрес")
    latitude: float = Field(..., description="Широта")
    longitude: float = Field(..., description="Долгота")
    working_hours: Optional[str] = Field(None, description="Режим работы")
    phone: Optional[str] = Field(None, description="Номер телефона")
    email: Optional[str] = Field(None, description="Email адрес")

    image_path: Optional[str] = Field(None, description="Внутренний путь к фото фасада")
    map_image_path: Optional[str] = Field(
        None, description="Внутренний путь к изображению карты"
    )

    @computed_field
    @property
    def map_image_url(self) -> Optional[str]:
        """Публичный URL схемы проезда/карты для фронтенда с нормализованными слэшами."""
        if not self.map_image_path:
            return None
        posix_path = Path(self.map_image_path).as_posix()
        return f"/{posix_path}" if not posix_path.startswith("/") else posix_path

    @computed_field
    @property
    def image_url(self) -> Optional[str]:
        """Публичный URL фото входа/здания для фронтенда с нормализованными слэшами."""
        if not self.image_path:
            return None
        posix_path = Path(self.image_path).as_posix()
        return f"/{posix_path}" if not posix_path.startswith("/") else posix_path

    class Config:
        from_attributes = True
