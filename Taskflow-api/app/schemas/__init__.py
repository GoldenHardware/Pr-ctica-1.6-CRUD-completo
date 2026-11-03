"""Schemas Pydantic: el contrato de entrada/salida de la API, separado por recurso."""

from app.schemas.category import CategoryCreate, CategoryDetail, CategoryRead, CategoryUpdate
from app.schemas.common import ErrorResponse, FieldError, Page, SchemaBase, TaskCounters
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectRead, ProjectUpdate
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.schemas.user import UserCreate, UserRead

__all__ = [
    "SchemaBase", "FieldError", "ErrorResponse", "Page", "TaskCounters",
    "ProjectCreate", "ProjectUpdate", "ProjectRead", "ProjectDetail",
    "CategoryCreate", "CategoryUpdate", "CategoryRead", "CategoryDetail",
    "TaskCreate", "TaskUpdate", "TaskRead",
    "UserCreate", "UserRead",
]
