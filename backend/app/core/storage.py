from pathlib import Path
from app.core.config import settings

# Thư mục gốc storage nằm cùng cấp với app/
BASE_STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage"


class ProjectStorage:
    def __init__(self, project_id: str):
        self.project_id = str(project_id)
        self.root = BASE_STORAGE_DIR / "projects" / self.project_id
        self.original_dir = self.root / "original"
        self.pages_dir = self.root / "pages"
        self.ai_artifacts_dir = self.root / "ai_artifacts"
        self.reports_dir = self.root / "reports"

    def init_project_structure(self) -> None:
        """Khởi tạo toàn bộ cây thư mục cho một project mới."""
        self.original_dir.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.ai_artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def get_page_dir(self, page_number: int) -> Path:
        """Đảm bảo chuẩn page_001, page_002 để thứ tự luôn chuẩn xác."""
        page_dir = self.pages_dir / f"page_{page_number:03d}"
        page_dir.mkdir(parents=True, exist_ok=True)
        return page_dir

    @property
    def original_pdf_path(self) -> Path:
        return self.original_dir / "document.pdf"

    def get_page_image_path(self, page_number: int) -> Path:
        return self.get_page_dir(page_number) / "image.png"

    def get_page_thumbnail_path(self, page_number: int) -> Path:
        return self.get_page_dir(page_number) / "thumbnail.png"

    def get_page_text_json_path(self, page_number: int) -> Path:
        return self.get_page_dir(page_number) / "text_layout.json"

    def get_ai_artifact_path(self, artifact_name: str) -> Path:
        return self.ai_artifacts_dir / f"{artifact_name}.json"

    def get_report_path(self, filename: str) -> Path:
        return self.reports_dir / filename