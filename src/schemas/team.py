from pathlib import Path
from typing import Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field, computed_field


class TeamMemberRead(BaseModel):
    """Схема ответа для отображения карточки сотрудника на фронтенде."""

    id: int = Field(..., description="ID сотрудника")
    first_name: str = Field(..., description="Имя")
    last_name: str = Field(..., description="Фамилия")
    middle_name: Optional[str] = Field(None, description="Отчество (при наличии)")
    role: str = Field(..., description="Должность (например: Шеф-повар)")
    description: Optional[str] = Field(None, description="Информация о сотруднике/достижения")
    order_priority: int = Field(..., description="Приоритет ручной сортировки карточек")
    image_path: str = Field(..., description="Внутренний путь к файлу на сервере")
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def full_name(self) -> str:
        """Автоматическая сборка ФИО в одну строчку."""
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"

    @computed_field
    @property
    def image_url(self) -> str:
        """Автоматически преобразует внутренний путь во внешний веб-URL для фронтенда."""
        posix_path = Path(self.image_path).as_posix()
        return f"/{posix_path}" if not posix_path.startswith("/") else posix_path


class TeamMemberCreate(BaseModel):
    first_name: str = Field(..., description="Имя сотрудника")
    last_name: str = Field(..., description="Фамилия сотрудника")
    middle_name: Optional[str] = Field(None, description="Отчество (при наличии)")
    role: str = Field(..., description="Должность, например: Шеф-повар")
    description: str = Field(..., description="Биография или описание обязанностей")
    order_priority: int = Field(
        0, description="Приоритет выдачи (чем выше, тем раньше в списке)"
    )

    @classmethod
    def as_form(
        cls,
        first_name: str = Form(..., description="Имя сотрудника"),
        last_name: str = Form(..., description="Фамилия сотрудника"),
        middle_name: Optional[str] = Form(None, description="Отчество (при наличии)"),
        role: str = Form(..., description="Должность, например: Шеф-повар"),
        description: str = Form(..., description="Биография или описание обязанностей"),
        order_priority: int = Form(
            0, description="Приоритет выдачи (чем выше, тем раньше в списке)"
        ),
    ):
        return cls(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            role=role,
            description=description,
            order_priority=order_priority,
        )


# Новая схема для формы ОБНОВЛЕНИЯ сотрудника (все поля необязательны)
class TeamMemberUpdate(BaseModel):
    first_name: Optional[str] = Field(None, description="Имя сотрудника")
    last_name: Optional[str] = Field(None, description="Фамилия сотрудника")
    middle_name: Optional[str] = Field(None, description="Отчество")
    role: Optional[str] = Field(None, description="Должность")
    description: Optional[str] = Field(None, description="Биография или описание")
    order_priority: Optional[int] = Field(None, description="Приоритет выдачи")

    @classmethod
    def as_form(
        cls,
        first_name: Optional[str] = Form(None, description="Имя сотрудника"),
        last_name: Optional[str] = Form(None, description="Фамилия сотрудника"),
        middle_name: Optional[str] = Form(None, description="Отчество"),
        role: Optional[str] = Form(None, description="Должность"),
        description: Optional[str] = Form(None, description="Биография или описание"),
        order_priority: Optional[int] = Form(None, description="Приоритет выдачи"),
    ):
        return cls(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            role=role,
            description=description,
            order_priority=order_priority,
        )
