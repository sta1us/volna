from pydantic import BaseModel, Field


class BaseMessageResponse(BaseModel):
    status: str = Field(..., description="Статус операции (success/error)")
    message: str = Field(..., description="Текстовое описание результата")
