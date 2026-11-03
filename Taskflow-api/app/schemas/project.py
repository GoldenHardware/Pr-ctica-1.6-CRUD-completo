"""Schemas del recurso Proyecto."""

from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.common import SchemaBase
from app.schemas.task import TaskRead


class ProjectBase(SchemaBase):
    """Campos comunes de un proyecto."""

    name: str = Field(min_length=1, max_length=100, description="Nombre del proyecto (1-100 caracteres).")
    description: str | None = Field(
        default=None, max_length=500, description="Descripción opcional (máx. 500 caracteres)."
    )


class ProjectCreate(ProjectBase):
    """Datos para crear un proyecto (POST)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "TaskFlow", "description": "Gestor de tareas de 2ºDAW"}]}
    )


class ProjectUpdate(ProjectBase):
    """Datos para editar un proyecto (PUT): nombre y descripción (RF-11)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "TaskFlow v2", "description": "Proyecto del módulo de frameworks"}]}
    )


class ProjectRead(ProjectBase):
    """Proyecto tal y como lo devuelve la API."""

    id: int = Field(description="Identificador único generado por el servidor.")
    created_at: datetime = Field(description="Fecha y hora de creación.")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ProjectDetail(ProjectRead):
    """Detalle de un proyecto con sus tareas asociadas (RF-10)."""

    tasks: list[TaskRead] = Field(default_factory=list, description="Tareas del proyecto.")
