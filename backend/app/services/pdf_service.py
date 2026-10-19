import json
from pathlib import Path
import fitz  # PyMuPDF
from sqlalchemy import select

from app.core.storage import ProjectStorage
from app.db import AsyncSessionLocal
from app.models.drawings import DrawingPage, DrawingVersion, ProcessingJob


class PDFService:

    @staticmethod
    async def process_pdf_job(
        job_id: int,
        drawing_version_id: int,
        pdf_path: Path,
        storage: ProjectStorage,
        dpi: int = 200,
    ) -> None:
        async with AsyncSessionLocal() as db:
            # 1. Cập nhật job sang running
            job = await db.get(ProcessingJob, job_id)
            if not job:
                return

            job.status = "running"
            job.progress_percent = 10
            await db.commit()

            try:
                doc = fitz.open(pdf_path)
                total_pages = len(doc)

                # Cập nhật số trang vào drawing_version
                version = await db.get(DrawingVersion, drawing_version_id)
                if version:
                    version.page_count = total_pages

                scale = dpi / 72
                matrix = fitz.Matrix(scale, scale)
                thumb_matrix = fitz.Matrix(60 / 72, 60 / 72)

                pages_to_create = []

                for idx in range(total_pages):
                    page_num = idx + 1
                    page = doc[idx]

                    # Lưu ảnh độ phân giải cao và thumbnail
                    img_path = storage.get_page_image_path(page_num)
                    thumb_path = storage.get_page_thumbnail_path(page_num)

                    pix = page.get_pixmap(matrix=matrix)
                    pix.save(img_path)

                    thumb_pix = page.get_pixmap(matrix=thumb_matrix)
                    thumb_pix.save(thumb_path)

                    # Trích xuất text blocks kèm bounding box
                    raw_blocks = page.get_text("blocks")
                    blocks_data = [
                        {
                            "block_id": b[5],
                            "text": b[4].strip(),
                            "bbox": [round(c, 2) for c in b[:4]],
                        }
                        for b in raw_blocks
                    ]

                    # Ghi ra file JSON layout
                    layout_dict = {
                        "page": page_num,
                        "width": float(page.rect.width),
                        "height": float(page.rect.height),
                        "blocks": blocks_data,
                    }
                    with open(storage.get_page_text_json_path(page_num), "w", encoding="utf-8") as f:
                        json.dump(layout_dict, f, ensure_ascii=False, indent=2)

                    # Chuẩn bị model DrawingPage để insert vào DB
                    rel_img_url = f"/static/projects/{storage.project_id}/pages/page_{page_num:03d}/image.png"
                    rel_thumb_url = f"/static/projects/{storage.project_id}/pages/page_{page_num:03d}/thumbnail.png"

                    page_record = DrawingPage(
                        drawing_version_id=drawing_version_id,
                        page_number=page_num,
                        width=float(page.rect.width),
                        height=float(page.rect.height),
                        image_storage_key=rel_img_url,
                        thumbnail_storage_key=rel_thumb_url,
                        layout_data=layout_dict,
                        status="ready",
                    )
                    pages_to_create.append(page_record)

                    # Cập nhật tiến độ
                    job.progress_percent = 10 + int((idx + 1) / total_pages * 80)

                doc.close()

                # Lưu toàn bộ các trang vào PostgreSQL
                db.add_all(pages_to_create)

                # Hoàn thành job
                job.status = "completed"
                job.progress_percent = 100
                await db.commit()

            except Exception as e:
                await db.rollback()
                job.status = "failed"
                job.error_message = str(e)
                await db.commit()