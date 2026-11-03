"""
Router del recurso /tasks: CRUD completo sobre la base de datos.

GET    /tasks          lista con filtros, ordenación y paginación
GET    /tasks/{id}     detalle
POST   /tasks          crear
PUT    /tasks/{id}     editar (tarea completa)
DELETE /tasks/{id}     eliminar
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import func, select

from app.core.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.core.deps import DbSession
from app.core.queries import get_or_404
from app.models import Category, Project, Task
from app.schemas import ErrorResponse, Page, TaskCreate, TaskRead, TaskUpdate

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={422: {"model": ErrorResponse, "description": "Datos no válidos"}},
)

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Tarea, proyecto o categoría no encontrados"}}

# Columnas por las que se permite ordenar (lista cerrada: nunca se ordena por
# un texto libre que mande el cliente).
SORT_COLUMNS = {"id": Task.id, "title": Task.title, "created_at": Task.created_at, "completed": Task.completed}


def _check_relations(db: DbSession, data: TaskCreate | TaskUpdate) -> None:
    """Si la tarea apunta a un proyecto o categoría, deben existir (404 diferenciado)."""
    if data.project_id is not None:
        get_or_404(db, Project, data.project_id)
    if data.category_id is not None:
        get_or_404(db, Category, data.category_id)


@router.get(
    "",
    response_model=Page[TaskRead],
    summary="Listar tareas",
    description=(
        "Lista paginada de tareas. Filtros combinables: `project_id`, `category_id`, `completed` y `search` "
        "(busca en el título). Ordenación con `sort_by` y `order`. La respuesta incluye `total` y `has_more`."
    ),
)
def list_tasks(
    db: DbSession,
    project_id: Annotated[int | None, Query(gt=0, description="Solo tareas de este proyecto.")] = None,
    category_id: Annotated[int | None, Query(gt=0, description="Solo tareas de esta categoría.")] = None,
    completed: Annotated[bool | None, Query(description="true = completadas, false = pendientes.")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=100, description="Texto a buscar en el título.")] = None,
    sort_by: Annotated[Literal["id", "title", "created_at", "completed"], Query()] = "id",
    order: Annotated[Literal["asc", "desc"], Query()] = "asc",
    skip: Annotated[int, Query(ge=0, description="Cuántas tareas saltar.")] = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Tamaño de página.")] = DEFAULT_PAGE_SIZE,
):
    conditions = []
    if project_id is not None:
        conditions.append(Task.project_id == project_id)
    if category_id is not None:
        conditions.append(Task.category_id == category_id)
    if completed is not None:
        conditions.append(Task.completed == completed)
    if search:
        conditions.append(Task.title.ilike(f"%{search}%"))  # parámetro escapado por SQLAlchemy

    # Total con COUNT en la BD (no se cargan todas las filas para contarlas).
    total = db.scalar(select(func.count(Task.id)).where(*conditions))

    column = SORT_COLUMNS[sort_by]
    query = (
        select(Task)
        .where(*conditions)
        .order_by(column.desc() if order == "desc" else column.asc(), Task.id)
        .offset(skip)
        .limit(limit)
    )
    items = db.scalars(query).all()
    return Page(items=items, total=total, skip=skip, limit=limit, has_more=skip + len(items) < total)


@router.get("/{task_id}", response_model=TaskRead, summary="Detalle de una tarea", responses=NOT_FOUND)
def get_task(task_id: int, db: DbSession):
    return get_or_404(db, Task, task_id)


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una tarea",
    description="Proyecto y categoría son opcionales; si se indican deben existir.",
    responses=NOT_FOUND,
)
def create_task(data: TaskCreate, db: DbSession):
    _check_relations(db, data)
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put(
    "/{task_id}",
    response_model=TaskRead,
    summary="Editar una tarea",
    description="Reemplaza todos los campos editables de la tarea (RF-16), incluido `completed`.",
    responses=NOT_FOUND,
)
def update_task(task_id: int, data: TaskUpdate, db: DbSession):
    task = get_or_404(db, Task, task_id)
    _check_relations(db, data)
    for field, value in data.model_dump().items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una tarea",
    description="Elimina la tarea de forma permanente (RF-18).",
    responses=NOT_FOUND,
)
def delete_task(task_id: int, db: DbSession):
    task = get_or_404(db, Task, task_id)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
