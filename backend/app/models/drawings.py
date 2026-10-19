from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


# -----------------------------------------------------------------------------
# 1. BẢNG DỰ ÁN (PROJECTS)
# -----------------------------------------------------------------------------
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    drawings: Mapped[List["Drawing"]] = relationship(
        "Drawing", back_populates="project", cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_projects_owner_name", "owner_id", "name"),
    )


# -----------------------------------------------------------------------------
# 2. BẢNG BẢN VẼ LOGIC (DRAWINGS)
# -----------------------------------------------------------------------------
class Drawing(Base):
    __tablename__ = "drawings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    drawing_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    discipline: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    current_version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="uploaded", nullable=False)
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    uploaded_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="drawings")
    versions: Mapped[List["DrawingVersion"]] = relationship(
        "DrawingVersion", back_populates="drawing", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_drawings_project_status", "project_id", "status"),
        Index("idx_drawings_project_name", "project_id", "name"),
    )


# -----------------------------------------------------------------------------
# 3. BẢNG PHIÊN BẢN BẢN VẼ (DRAWING_VERSIONS)
# -----------------------------------------------------------------------------
class DrawingVersion(Base):
    __tablename__ = "drawing_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drawing_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    source_width: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    source_height: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, default=1, nullable=True)
    unit_system: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    coordinate_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    upload_status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    uploaded_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    drawing: Mapped["Drawing"] = relationship("Drawing", back_populates="versions")
    pages: Mapped[List["DrawingPage"]] = relationship(
        "DrawingPage", back_populates="version", cascade="all, delete-orphan"
    )
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="drawing_version"
    )

    __table_args__ = (
        UniqueConstraint("drawing_id", "version_number", name="uq_drawing_version"),
    )


# -----------------------------------------------------------------------------
# 4. BẢNG TỪNG TRANG BẢN VẼ (DRAWING_PAGES)
# -----------------------------------------------------------------------------
class DrawingPage(Base):
    __tablename__ = "drawing_pages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drawing_version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("drawing_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # floor_plan, schedule_table, detail
    width: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    height: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    image_storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    layout_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ready", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    version: Mapped["DrawingVersion"] = relationship("DrawingVersion", back_populates="pages")

    __table_args__ = (
        UniqueConstraint("drawing_version_id", "page_number", name="uq_version_page_number"),
        Index("idx_drawing_pages_version_type", "drawing_version_id", "page_type"),
    )


# -----------------------------------------------------------------------------
# 5. BẢNG TÁC VỤ XỬ LÝ NỀN (PROCESSING_JOBS)
# -----------------------------------------------------------------------------
class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    drawing_version_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("drawing_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_type: Mapped[str] = mapped_column(
        String(40), nullable=False
    )  # pdf_preprocessing, ocr, ai_detection, cross_check
    status: Mapped[str] = mapped_column(
        String(20), default="queued", nullable=False
    )  # queued, running, completed, failed
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requested_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    worker_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    input_parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="processing_jobs")
    drawing_version: Mapped[Optional["DrawingVersion"]] = relationship(
        "DrawingVersion", back_populates="processing_jobs"
    )

    __table_args__ = (
        Index("idx_processing_jobs_status_priority", "status", "priority"),
        Index("idx_processing_jobs_project_created", "project_id", "created_at"),
        Index("idx_processing_jobs_version_type", "drawing_version_id", "job_type"),
    )