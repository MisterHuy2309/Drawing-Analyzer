import shutil
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import ProjectStorage
from app.db import get_db
from app.models.drawings import Drawing, DrawingPage, DrawingVersion, ProcessingJob, Project
from app.schemas.drawings import (
    DrawingPageResponse,
    DrawingPagesListResponse,
    JobStatusResponse,
    PageLayoutResponse,
    UploadDrawingResponse,
)
from app.services.pdf_service import PDFService

router = APIRouter(prefix="/drawings", tags=["Drawings"])


@router.post(
    "/projects/{project_id}/upload",
    response_model=UploadDrawingResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_drawing(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận file định dạng PDF.",
        )

    # 1. Kiểm tra Project, nếu chưa có thì tự động tạo mới
    project = await db.get(Project, project_id)
    if not project:
        project = Project(
            id=project_id,
            name=f"Dự án {project_id} - {file.filename}",
            description="Dự án tự động khởi tạo khi upload",
            owner_id=1,
            status="active",
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)

    # 2. Tạo bản ghi Drawing
    drawing = Drawing(
        project_id=project.id,
        name=file.filename,
        uploaded_by=project.owner_id,
        status="processing",
    )
    db.add(drawing)
    await db.flush()

    # 3. Khởi tạo Storage
    storage_identifier = f"proj_{project.id}_draw_{drawing.id}"
    storage = ProjectStorage(storage_identifier)
    storage.init_project_structure()

    try:
        with open(storage.original_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()

    # 4. Tạo bản ghi DrawingVersion
    version = DrawingVersion(
        drawing_id=drawing.id,
        version_number=1,
        original_file_name=file.filename,
        file_format="pdf",
        storage_key=str(storage.original_pdf_path),
        uploaded_by=project.owner_id,
        upload_status="completed",
    )
    db.add(version)
    await db.flush()

    # 5. Tạo Job ngầm
    job = ProcessingJob(
        project_id=project.id,
        drawing_version_id=version.id,
        job_type="pdf_preprocessing",
        status="queued",
        priority=1,
        requested_by=project.owner_id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # 6. Kích hoạt tác vụ nền
    background_tasks.add_task(
        PDFService.process_pdf_job,
        job_id=job.id,
        drawing_version_id=version.id,
        pdf_path=storage.original_pdf_path,
        storage=storage,
    )

    return UploadDrawingResponse(
        status="ACCEPTED",
        message="Bản vẽ đã tải lên thành công và đang được tách trang ngầm.",
        drawing_id=drawing.id,
        version_id=version.id,
        job_id=job.id,
        check_status_url=f"/api/v1/drawings/jobs/{job.id}/status",
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: int, db: AsyncSession = Depends(get_db)):
    """FE thăm dò (poll) tiến độ xử lý tác vụ render ảnh PDF."""
    job = await db.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tác vụ với mã ID: {job_id}",
        )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress_percent=job.progress_percent,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/versions/{version_id}/pages", response_model=DrawingPagesListResponse)
async def get_drawing_pages(version_id: int, db: AsyncSession = Depends(get_db)):
    """FE Canvas lấy danh sách trang (URL ảnh phân giải cao, kích thước, thumbnail)."""
    version = await db.get(DrawingVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên bản bản vẽ.")

    query = select(DrawingPage).where(DrawingPage.drawing_version_id == version_id).order_by(DrawingPage.page_number)
    result = await db.execute(query)
    pages = result.scalars().all()

    page_responses = [
        DrawingPageResponse(
            id=p.id,
            page_number=p.page_number,
            page_type=p.page_type,
            width=float(p.width),
            height=float(p.height),
            image_url=p.image_storage_key,
            thumbnail_url=p.thumbnail_storage_key,
            status=p.status,
        )
        for p in pages
    ]

    return DrawingPagesListResponse(
        drawing_id=version.drawing_id,
        version_id=version_id,
        total_pages=len(page_responses),
        pages=page_responses,
    )


@router.get("/pages/{page_id}/layout", response_model=PageLayoutResponse)
async def get_page_layout(page_id: int, db: AsyncSession = Depends(get_db)):
    """Lấy dữ liệu bounding box văn bản của một trang phục vụ lớp phủ Canvas."""
    page = await db.get(DrawingPage, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang bản vẽ.")

    layout = page.layout_data or {}
    blocks = layout.get("blocks", [])

    return PageLayoutResponse(
        page_number=page.page_number,
        width=float(page.width),
        height=float(page.height),
        blocks_count=len(blocks),
        blocks=blocks,
    )