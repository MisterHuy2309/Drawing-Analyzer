from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.drawings import Drawing, Project
from app.schemas.projects import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """FE 1 gọi để lấy danh sách toàn bộ dự án trên Dashboard."""
    stmt = (
        select(Project, func.count(Drawing.id).label("total_drawings"))
        .outerjoin(Drawing, Drawing.project_id == Project.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    projects = []
    for proj, count in rows:
        projects.append(
            ProjectResponse(
                id=proj.id,
                name=proj.name,
                description=proj.description,
                total_drawings=count,
                created_at=proj.created_at,
                updated_at=getattr(proj, "updated_at", None),
            )
        )
    return projects


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Tạo mới hồ sơ công trình."""
    new_project = Project(
        name=payload.name,
        description=payload.description,
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    return ProjectResponse(
        id=new_project.id,
        name=new_project.name,
        description=new_project.description,
        total_drawings=0,
        created_at=new_project.created_at,
        updated_at=getattr(new_project, "updated_at", None),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_detail(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án.")

    stmt = select(func.count(Drawing.id)).where(Drawing.project_id == project_id)
    count = (await db.execute(stmt)).scalar() or 0

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        total_drawings=count,
        created_at=project.created_at,
        updated_at=getattr(project, "updated_at", None),
    )