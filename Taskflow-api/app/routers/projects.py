"""
Router del recurso /projects: CRUD completo sobre la base de datos.

Al eliminar un proyecto se eliminan sus tareas (cascada): ver models.py.
"""

from fastapi import APIRouter, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession
from app.core.queries import get_or_404, task_counters
from app.models import Project, Task
from app.schemas import ErrorResponse, ProjectCreate, ProjectDetail, ProjectRead, ProjectUpdate, TaskCounters

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={422: {"model": ErrorResponse, "description": "Datos no válidos"}},
)

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Proyecto no encontrado"}}


@router.get("", response_model=list[ProjectRead], summary="Listar proyectos")
def list_projects(db: DbSession):
    return db.scalars(select(Project).order_by(Project.id)).all()


@router.get(
    "/{project_id}",
    response_model=ProjectDetail,
    summary="Detalle de un proyecto (con sus tareas)",
    responses=NOT_FOUND,
)
def get_project(project_id: int, db: DbSession):
    # selectinload: carga el proyecto y TODAS sus tareas en 2 consultas fijas,
    # en lugar de 1 + N (problema N+1) al acceder a project.tasks.
    return get_or_404(db, Project, project_id, options=(selectinload(Project.tasks),))


@router.get(
    "/{project_id}/summary",
    response_model=TaskCounters,
    summary="Resumen de un proyecto (contadores)",
    description="Total de tareas, completadas, pendientes y porcentaje de avance, calculados con una sola consulta.",
    responses=NOT_FOUND,
)
def project_summary(project_id: int, db: DbSession):
    get_or_404(db, Project, project_id)
    return task_counters(db, Task.project_id == project_id)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED, summary="Crear un proyecto")
def create_project(data: ProjectCreate, db: DbSession):
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectRead, summary="Editar un proyecto", responses=NOT_FOUND)
def update_project(project_id: int, data: ProjectUpdate, db: DbSession):
    project = get_or_404(db, Project, project_id)
    for field, value in data.model_dump().items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un proyecto (y sus tareas)",
    description=(
        "Elimina el proyecto **y todas sus tareas** (borrado en cascada, RF-12). "
        "La respuesta incluye la cabecera `X-Deleted-Tasks` con cuántas tareas se han borrado."
    ),
    responses=NOT_FOUND,
)
def delete_project(project_id: int, db: DbSession):
    project = get_or_404(db, Project, project_id)
    deleted_tasks = db.scalar(select(func.count(Task.id)).where(Task.project_id == project_id))
    db.delete(project)  # cascade="all, delete" borra también sus tareas
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers={"X-Deleted-Tasks": str(deleted_tasks)})
