from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.drawings import Project
from app.schemas.projects import ProjectCreateRequest, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreateRequest, db: AsyncSession = Depends(get_db)):
    """Tạo mới một hồ sơ/dự án công trình."""
    new_project = Project(
        name=payload.name,
        description=payload.description,
        owner_id=1,  # Mặc định user id = 1
        status="active",
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách tất cả các dự án."""
    query = select(Project).where(Project.deleted_at.is_(None)).order_by(Project.id.desc())
    result = await db.execute(query)
    return result.scalars().all()