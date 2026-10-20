from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.components import DrawingComponent
from app.schemas.components import DrawingComponentCreate, DrawingComponentResponse

router = APIRouter(prefix="/components", tags=["Drawing Components"])


@router.get("/versions/{version_id}", response_model=List[DrawingComponentResponse])
async def list_components_by_version(
    version_id: int,
    component_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách cấu kiện (dầm, cột, giằng) của một version bản vẽ."""
    stmt = select(DrawingComponent).where(DrawingComponent.version_id == version_id)
    if component_type:
        stmt = stmt.where(DrawingComponent.component_type == component_type)
    stmt = stmt.order_by(DrawingComponent.mark.asc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/pages/{page_id}", response_model=List[DrawingComponentResponse])
async def list_components_by_page(
    page_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách cấu kiện xuất hiện trên một trang cụ thể (phục vụ Canvas highlight)."""
    stmt = select(DrawingComponent).where(DrawingComponent.page_id == page_id).order_by(DrawingComponent.mark.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=DrawingComponentResponse, status_code=status.HTTP_201_CREATED)
async def create_component(
    payload: DrawingComponentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Dành cho AI Pipeline hoặc tạo thủ công cấu kiện mới."""
    new_comp = DrawingComponent(**payload.model_dump())
    db.add(new_comp)
    await db.commit()
    await db.refresh(new_comp)
    return new_comp
