import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List
import fitz  # PyMuPDF
from PIL import Image

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.drawings import DrawingPage, ProcessingJob

logger = logging.getLogger(__name__)


def extract_page_layout_and_geometry(page: fitz.Page) -> Dict[str, Any]:
    """
    Trích xuất:
    1. Text blocks: Tọa độ, nội dung từng đoạn/khối chữ.
    2. Vector lines & rects: Đường biên bảng biểu, khung tên kỹ thuật.
    """
    # 1. Trích xuất Text Blocks
    blocks_raw = page.get_text("blocks")
    blocks: List[Dict[str, Any]] = []

    for idx, b in enumerate(blocks_raw):
        # Format block: (x0, y0, x1, y1, text, block_no, block_type)
        if len(b) >= 5:
            text_content = b[4].strip()
            if text_content:
                blocks.append({
                    "block_id": b[5] if len(b) > 5 else idx,
                    "text": text_content,
                    "bbox": [round(coord, 2) for coord in b[:4]],
                })

    # 2. Trích xuất hình học vector (Kẻ khung, bảng biểu)
    # page.get_drawings() trả về toàn bộ đường path/line/rect trong PDF
    drawings = page.get_drawings()
    table_rects: List[List[float]] = []

    for d in drawings:
        rect = d.get("rect")
        if rect:
            w = rect.width
            h = rect.height
            # Lọc bỏ các chấm/vạch quá nhỏ, chỉ giữ lại các khung bao tiềm năng
            if w >= 40.0 and h >= 15.0:
                table_rects.append([
                    round(rect.x0, 2),
                    round(rect.y0, 2),
                    round(rect.x1, 2),
                    round(rect.y1, 2),
                ])

    return {
        "page_width": round(page.rect.width, 2),
        "page_height": round(page.rect.height, 2),
        "blocks_count": len(blocks),
        "blocks": blocks,
        "table_rects_count": len(table_rects),
        "table_rects": table_rects[:100],  # Lưu tối đa 100 khung viền lớn nhất
    }


async def process_pdf_background(
    job_id: int,
    version_id: int,
    file_path: str,
    project_id: int,
    drawing_id: int,
):
    """
    Tác vụ chạy ngầm:
    - Mở PDF bằng PyMuPDF
    - Render ảnh HD 200 DPI và Thumbnail 50 DPI
    - Trích xuất Text & Vector layout
    - Cập nhật tiến độ vào database (bảng processing_jobs và drawing_pages)
    """
    async with AsyncSessionLocal() as db:
        job = await db.get(ProcessingJob, job_id)
        if not job:
            logger.error(f"Job {job_id} không tồn tại.")
            return

        try:
            # 1. Đánh dấu bắt đầu xử lý
            job.status = "running"
            job.progress_percent = 5
            await db.commit()

            doc = fitz.open(file_path)
            total_pages = len(doc)

            base_storage = Path(settings.STORAGE_DIR) / "projects" / f"proj_{project_id}_draw_{drawing_id}" / "pages"
            base_storage.mkdir(parents=True, exist_ok=True)

            # Cấu hình Matrix DPI: 72 dpi chuẩn -> scale lên 200 DPI (khoảng 2.77x)
            zoom = 200 / 72
            mat_hd = fitz.Matrix(zoom, zoom)
            mat_thumb = fitz.Matrix(0.5, 0.5)

            for index, page in enumerate(doc):
                page_number = index + 1
                page_dir = base_storage / f"page_{page_number:03d}"
                page_dir.mkdir(parents=True, exist_ok=True)

                # --- A. Render Ảnh HD (200 DPI) ---
                hd_path = page_dir / "image.png"
                pix_hd = page.get_pixmap(matrix=mat_hd, alpha=False)
                pix_hd.save(str(hd_path))

                # --- B. Render Thumbnail ---
                thumb_path = page_dir / "thumbnail.png"
                pix_thumb = page.get_pixmap(matrix=mat_thumb, alpha=False)
                pix_thumb.save(str(thumb_path))

                # --- C. Bóc tách Text Layout & Vector Geometry ---
                layout_data = extract_page_layout_and_geometry(page)
                json_path = page_dir / "text_layout.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(layout_data, f, ensure_ascii=False, indent=2)

                # --- D. Lưu Record vào Database ---
                relative_hd_url = f"/static/projects/proj_{project_id}_draw_{drawing_id}/pages/page_{page_number:03d}/image.png"
                relative_thumb_url = f"/static/projects/proj_{project_id}_draw_{drawing_id}/pages/page_{page_number:03d}/thumbnail.png"

                drawing_page = DrawingPage(
                    version_id=version_id,
                    page_number=page_number,
                    width=layout_data["page_width"],
                    height=layout_data["page_height"],
                    image_path=str(hd_path),
                    thumbnail_path=str(thumb_path),
                    image_url=relative_hd_url,
                    thumbnail_url=relative_thumb_url,
                    status="ready",
                    layout_data=layout_data,
                )
                db.add(drawing_page)

                # Cập nhật tiến độ % theo từng trang
                percent = int(10 + (page_number / total_pages) * 85)
                job.progress_percent = percent
                await db.commit()

            # 2. Hoàn tất toàn bộ tác vụ
            job.status = "completed"
            job.progress_percent = 100
            await db.commit()
            logger.info(f"Hoàn thành bóc tách PDF {file_path} cho Version {version_id}.")

        except Exception as e:
            logger.exception(f"Lỗi khi xử lý background PDF job {job_id}: {str(e)}")
            job.status = "failed"
            job.error_message = str(e)
            await db.commit()
        finally:
            if 'doc' in locals():
                doc.close()