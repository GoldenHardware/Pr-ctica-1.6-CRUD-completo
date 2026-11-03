"""
Router del recurso /categories: CRUD completo sobre la base de datos.

Al eliminar una categoría sus tareas NO se borran: se quedan sin categoría
(category_id = NULL). Ver models.py.
"""

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession
from app.core.errors import ConflictError
from app.core.queries import get_or_404, task_counters
from app.models import Category, Task
from app.schemas import (
    CategoryCreate, CategoryDetail, CategoryRead, CategoryUpdate, ErrorResponse, TaskCounters,
)

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={422: {"model": ErrorResponse, "description": "Datos no válidos"}},
)

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Categoría no encontrada"}}
CONFLICT = {409: {"model": ErrorResponse, "description": "Ya existe una categoría con ese nombre"}}


def _check_unique_name(db: DbSession, name: str, exclude_id: int | None = None) -> None:
    query = select(Category.id).where(func.lower(Category.name) == name.lower())
    if exclude_id is not None:
        query = query.where(Category.id != exclude_id)
    if db.scalar(query) is not None:
        raise ConflictError("CATEGORY_NAME_TAKEN", f"Ya existe una categoría llamada '{name}'")


@router.get("", response_model=list[CategoryRead], summary="Listar categorías")
def list_categories(db: DbSession):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.get(
    "/{category_id}",
    response_model=CategoryDetail,
    summary="Detalle de una categoría (con sus tareas)",
    responses=NOT_FOUND,
)
def get_category(category_id: int, db: DbSession):
    return get_or_404(db, Category, category_id, options=(selectinload(Category.tasks),))


@router.get(
    "/{category_id}/summary",
    response_model=TaskCounters,
    summary="Resumen de una categoría (contadores)",
    responses=NOT_FOUND,
)
def category_summary(category_id: int, db: DbSession):
    get_or_404(db, Category, category_id)
    return task_counters(db, Task.category_id == category_id)


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una categoría",
    responses=CONFLICT,
)
def create_category(data: CategoryCreate, db: DbSession):
    _check_unique_name(db, data.name)
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Editar una categoría",
    responses={**NOT_FOUND, **CONFLICT},
)
def update_category(category_id: int, data: CategoryUpdate, db: DbSession):
    category = get_or_404(db, Category, category_id)
    _check_unique_name(db, data.name, exclude_id=category_id)
    for field, value in data.model_dump().items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una categoría",
    description=(
        "Elimina la categoría. Sus tareas **no se borran**: se quedan sin categoría. "
        "La cabecera `X-Unlinked-Tasks` indica cuántas tareas se han desasociado."
    ),
    responses=NOT_FOUND,
)
def delete_category(category_id: int, db: DbSession):
    category = get_or_404(db, Category, category_id)
    unlinked = db.scalar(select(func.count(Task.id)).where(Task.category_id == category_id))
    db.delete(category)  # el ORM pone category_id = NULL en sus tareas (y la BD tiene ondelete=SET NULL)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers={"X-Unlinked-Tasks": str(unlinked)})
