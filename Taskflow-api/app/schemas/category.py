"""Schemas del recurso Categoría."""

from pydantic import ConfigDict, Field

from app.schemas.common import SchemaBase
from app.schemas.task import TaskRead

# Código hexadecimal (#RGB o #RRGGBB) o nombre de color en letras (red, blue...).
COLOR_PATTERN = r"^(#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}|[a-zA-Z]{3,20})$"


class CategoryBase(SchemaBase):
    """Campos comunes de una categoría (RF-20)."""

    name: str = Field(min_length=1, max_length=50, description="Nombre de la categoría (único).")
    color: str = Field(pattern=COLOR_PATTERN, description="Color en hex (#FF8800) o por nombre (red).")


class CategoryCreate(CategoryBase):
    """Datos para crear una categoría (POST)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Backend", "color": "#3F51B5"}]})


class CategoryUpdate(CategoryBase):
    """Datos para editar una categoría (PUT)."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Backend", "color": "#E91E63"}]})


class CategoryRead(CategoryBase):
    """Categoría tal y como la devuelve la API."""

    id: int = Field(description="Identificador único generado por el servidor.")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class CategoryDetail(CategoryRead):
    """Detalle de una categoría con sus tareas asociadas."""

    tasks: list[TaskRead] = Field(default_factory=list, description="Tareas con esta categoría.")
