from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# 1. Khối văn bản và tọa độ (phục vụ Canvas Overlay & AI)
class TextBlockSchema(BaseModel):
    block_id: int = Field(..., description="Mã định danh thứ tự khối chữ")
    text: str = Field(..., description="Nội dung chữ")
    bbox: List[float] = Field(
        ...,
        description="Tọa độ bounding box [x0, y0, x1, y1]",
        min_length=4,
        max_length=4,
    )


# 2. Chi tiết từng trang bản vẽ
class DrawingPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    page_number: int = Field(..., ge=1, description="Số thứ tự trang")
    page_type: Optional[str] = Field(None, description="Loại trang: floor_plan, schedule_table, detail")
    width: float = Field(..., description="Chiều rộng gốc trang PDF (pt)")
    height: float = Field(..., description="Chiều cao gốc trang PDF (pt)")
    image_url: str = Field(..., description="Đường dẫn ảnh PNG 200-300 DPI")
    thumbnail_url: str = Field(..., description="Đường dẫn ảnh thumbnail")
    status: str = Field(default="ready", description="Trạng thái xử lý trang")


# 3. Danh mục toàn bộ trang của bản vẽ (phục vụ FE Canvas & Sidebar)
class DrawingPagesListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    drawing_id: int
    version_id: int
    total_pages: int
    pages: List[DrawingPageResponse]


# 4. Phản hồi khi vừa upload bản vẽ thành công
class UploadDrawingResponse(BaseModel):
    status: str = Field(default="ACCEPTED")
    message: str
    drawing_id: int
    version_id: int
    job_id: int
    check_status_url: str


# 5. Phản hồi trạng thái xử lý tác vụ ngầm (Polling status)
class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    job_id: int = Field(..., validation_alias="id", serialization_alias="job_id")
    status: str = Field(..., description="queued | running | completed | failed")
    progress_percent: int = Field(..., ge=0, le=100)
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# 6. Bố cục tọa độ chi tiết của trang (Overlay)
class PageLayoutResponse(BaseModel):
    page_number: int
    width: float
    height: float
    blocks_count: int
    blocks: List[TextBlockSchema]