from pathlib import Path

from pydantic import BaseModel, Field, computed_field

from common.models import MenuCategory


class MenuPageRead(BaseModel):
    """Схема ответа для отображения страницы меню на фронтенде."""

    id: int = Field(..., description="Уникальный ID страницы меню в СУБД")
    category: MenuCategory = Field(
        ..., description="Категория меню (kitchen - кухня, bar - бар)"
    )
    image_path: str = Field(
        ..., description="Внутренний относительный путь к файлу изображения на сервере"
    )
    order_num: int = Field(..., description="Порядковый номер страницы для сортировки")

    @computed_field
    @property
    def image_url(self) -> str:
        """Автоматически преобразует внутренний путь во внешний URL для фронтенда."""
        posix_path = Path(self.image_path).as_posix()
        return f"/{posix_path}" if not posix_path.startswith("/") else posix_path

    class Config:
        from_attributes = True  # Позволяет Pydantic работать с моделями SQLAlchemy


class MenuPageCreate(BaseModel):
    """Схема валидации Form-данных при создании/загрузке страницы меню."""

    category: MenuCategory = Field(
        ...,
        description="Категория меню: кухня (kitchen) или бар (bar)",
        examples=["kitchen"],
    )
    order_num: int = Field(
        default=0,
        ge=0,
        le=10000,
        description="Порядковый номер для сортировки при отображении (от 0 до 10000)",
        examples=[1],
    )
