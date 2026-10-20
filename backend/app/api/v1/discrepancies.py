from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.components import Discrepancy
from app.schemas.components import DiscrepancyCreate, DiscrepancyResponse

router = APIRouter(prefix="/discrepancies", tags=["Discrepancies & Anomalies"])


@router.get("/versions/{version_id}", response_model=List[DiscrepancyResponse])
async def list_discrepancies_by_version(
    version_id: int,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Lấy toàn bộ danh sách cảnh báo sai lệch của một bản vẽ để hiển thị panel báo cáo."""
    stmt = select(Discrepancy).where(Discrepancy.version_id == version_id)
    if severity:
        stmt = stmt.where(Discrepancy.severity == severity)
    stmt = stmt.order_by(Discrepancy.id.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/pages/{page_id}", response_model=List[DiscrepancyResponse])
async def list_discrepancies_by_page(
    page_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách điểm bất thường trên 1 trang để Canvas vẽ bounding box khoanh đỏ."""
    stmt = select(Discrepancy).where(Discrepancy.page_id == page_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=DiscrepancyResponse, status_code=status.HTTP_201_CREATED)
async def create_discrepancy(
    payload: DiscrepancyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Ghi nhận một cảnh báo sai lệch từ AI hoặc quy tắc đối chiếu."""
    new_item = Discrepancy(**payload.model_dump())
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item
