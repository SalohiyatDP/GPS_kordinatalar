"""Project persistence endpoints (SQLite)."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import Project, get_db
from app.schemas.models import ProjectCreate

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=payload.name,
        points_json=json.dumps(payload.points, ensure_ascii=False),
        area_json=json.dumps(payload.area, ensure_ascii=False),
        perimeter_json=json.dumps(payload.perimeter, ensure_ascii=False),
        analysis_json=json.dumps(payload.analysis, ensure_ascii=False),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.updated_at.desc()).all()
    return [{"id": p.id, "name": p.name,
             "created_at": p.created_at.isoformat() if p.created_at else None,
             "updated_at": p.updated_at.isoformat() if p.updated_at else None}
            for p in projects]


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"deleted": True}
