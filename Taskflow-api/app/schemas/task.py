"""Schemas del recurso Tarea."""

from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.common import SchemaBase


class TaskBase(SchemaBase):
    """Campos comunes de una tarea."""

    title: str = Field(min_length=1, max_length=100, description="Título de la tarea (1-100 caracteres).")
    description: str | None = Field(
        default=None, max_length=500, description="Descripción opcional (máx. 500 caracteres)."
    )
    project_id: int | None = Field(default=None, gt=0, description="Id del proyecto (opcional).")
    category_id: int | None = Field(default=None, gt=0, description="Id de la categoría (opcional).")


class TaskCreate(TaskBase):
    """Datos para crear una tarea (POST)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"title": "Hacer la práctica 1.6", "description": "CRUD completo", "project_id": 1, "category_id": 1}
            ]
        }
    )


class TaskUpdate(TaskBase):
    """Datos para editar una tarea (PUT): se envía la tarea completa, incluido su estado."""

    completed: bool = Field(default=False, description="Si la tarea está terminada.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Hacer la práctica 1.6",
                    "description": "CRUD completo y colección Postman",
                    "project_id": 1,
                    "category_id": 1,
                    "completed": True,
                }
            ]
        }
    )


class TaskRead(TaskBase):
    """Tarea tal y como la devuelve la API."""

    id: int = Field(description="Identificador único generado por el servidor.")
    completed: bool = Field(default=False, description="Si la tarea está terminada.")
    created_at: datetime = Field(description="Fecha y hora de creación.")

    model_config = ConfigDict(from_attributes=True, extra="ignore")
