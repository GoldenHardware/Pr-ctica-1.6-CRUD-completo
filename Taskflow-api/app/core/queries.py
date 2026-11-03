"""Consultas reutilizables por varios routers."""

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Task

# Nombre legible de cada modelo para los mensajes de error.
_LABELS = {"task": "La tarea", "project": "El proyecto", "category": "La categoría"}


def get_or_404(db: Session, model, obj_id: int, options: tuple = ()):
    """Devuelve el objeto o lanza un 404 con el código propio del recurso (TASK_NOT_FOUND...)."""
    obj = db.get(model, obj_id, options=options)
    if obj is None:
        resource = model.__tablename__.removesuffix("s").replace("categorie", "category")
        raise NotFoundError(resource, obj_id, _LABELS.get(resource, resource))
    return obj


def task_counters(db: Session, *conditions) -> dict:
    """
    Cuenta total / completadas / pendientes con UNA sola consulta de agregación
    (en vez de traer todas las tareas a Python y contarlas allí).
    """
    total, completed = db.execute(
        select(
            func.count(Task.id),
            func.coalesce(func.sum(case((Task.completed.is_(True), 1), else_=0)), 0),
        ).where(*conditions)
    ).one()
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": total - completed,
        "completion_rate": round(completed * 100 / total, 1) if total else 0.0,
    }
