from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String, Integer, Float, ForeignKey, DateTime, Text, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.drawings import Base

class PageAnnotation(Base):
    """Luu cac vung phan chia bo cuc cua trang: Title block, Schedule table, Floor plan, Note"""
    __tablename__ = "page_annotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("drawing_pages.id", ondelete="CASCADE"), index=True)
    
    # Loai vung: 'title_block', 'schedule_table', 'floor_plan', 'legend', 'notes'
    region_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Toa do vung: [x0, y0, x1, y1] hoac polygon [[x,y],...]
    bbox: Mapped[List[float]] = mapped_column(JSON, nullable=False)
    
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    page: Mapped["DrawingPage"] = relationship("DrawingPage", backref="annotations")


class DrawingComponent(Base):
    """Luu thong so cau kien boc tach tu bang thong ke va mat bang"""
    __tablename__ = "drawing_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("drawing_versions.id", ondelete="CASCADE"), index=True)
    page_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("drawing_pages.id", ondelete="SET NULL"), nullable=True, index=True)

    # Loai cau kien: 'beam' (dam), 'column' (cot), 'brace' (giang), 'girder'
    component_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Ky hieu cau kien: 'G1', 'C1', 'B25', '2G1'
    mark: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Mac thep / Vat lieu: 'SN400B', 'BCP325', 'SS400'
    material: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Kich thuoc tiet dien: vi du 'H-400x200x8x13', '[]-300x300x12'
    dimensions: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    
    # Thong so chi tiet boc tach
    properties: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Toa do bounding box cua ky hieu nay tren mat bang (neu co)
    bbox: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Discrepancy(Base):
    """Luu cac diem sai lech doi chieu giua Mat bang va Bang thong ke"""
    __tablename__ = "discrepancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_id: Mapped[int] = mapped_column(Integer, ForeignKey("drawing_versions.id", ondelete="CASCADE"), index=True)
    page_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("drawing_pages.id", ondelete="SET NULL"), nullable=True)
    component_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("drawing_components.id", ondelete="SET NULL"), nullable=True)

    # Loai sai lech: 'missing_in_plan', 'missing_in_schedule', 'spec_mismatch'
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Muc do nghiem trong: 'error' (do), 'warning' (vang), 'info' (xanh)
    severity: Mapped[str] = mapped_column(String(20), default="warning")
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Vi tri can khoanh do canh bao tren man hinh Canvas
    location_bbox: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    
    # Trang thai xu ly: 'detected', 'confirmed', 'ignored'
    status: Mapped[str] = mapped_column(String(30), default="detected")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
