from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# --- SCHEMAS CHO DRAWING COMPONENTS ---
class DrawingComponentBase(BaseModel):
    version_id: int
    page_id: Optional[int] = None
    component_type: str = Field(..., description="Loại cấu kiện: beam, column, brace, girder...")
    mark: str = Field(..., description="Ký hiệu cấu kiện: G1, C1, B25...")
    material: Optional[str] = Field(None, description="Mác thép: SN400B, BCP325...")
    dimensions: Optional[str] = Field(None, description="Kích thước tiết diện: H-400x200x8x13...")
    properties: Optional[Dict[str, Any]] = None
    bbox: Optional[List[float]] = Field(None, description="Tọa độ trên mặt bằng [x0, y0, x1, y1]")


class DrawingComponentCreate(DrawingComponentBase):
    pass


class DrawingComponentResponse(DrawingComponentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# --- SCHEMAS CHO DISCREPANCIES (SAI LỆCH) ---
class DiscrepancyBase(BaseModel):
    version_id: int
    page_id: Optional[int] = None
    component_id: Optional[int] = None
    issue_type: str = Field(..., description="Loại sai lệch: missing_in_plan, missing_in_schedule, spec_mismatch...")
    severity: str = Field("warning", description="Mức độ: error (đỏ), warning (vàng), info (xanh)")
    title: str
    description: str
    location_bbox: Optional[List[float]] = Field(None, description="Vị trí khoanh đỏ cảnh báo trên Canvas [x0, y0, x1, y1]")
    status: str = Field("detected", description="Trạng thái: detected, confirmed, ignored")


class DiscrepancyCreate(DiscrepancyBase):
    pass


class DiscrepancyResponse(DiscrepancyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
