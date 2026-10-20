from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.core.config import settings
from app.core.storage import BASE_STORAGE_DIR
from app.api.v1.drawings import router as drawings_router
from app.api.v1.projects import router as projects_router  
from app.api.v1.components import router as components_router    
from app.api.v1.discrepancies import router as discrepancies_router

app = FastAPI(
    title="AI Drawing Analyzer API",
    description="Backend API phục vụ phân tích bản vẽ kỹ thuật, bóc tách cấu kiện và đối chiếu.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. Danh sách các port thông dụng của FE (Vite, Next.js, Create React App)
origins = [
    "http://localhost:3000",   # Next.js / CRA default
    "http://localhost:5173",   # Vite default
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://localhost:8000",   # Local backend / docs
]

# 2. Cấu hình CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,             # Cho phép các origin của FE
    allow_credentials=True,            # Cho phép gửi cookie/authorization headers
    allow_methods=["*"],               # GET, POST, PUT, DELETE, OPTIONS...
    allow_headers=["*"],               # Content-Type, Authorization...
    expose_headers=["Content-Disposition"], # Để FE đọc được tên file khi export báo cáo (Ngày 6)
)

# 3. Mount Static Files với Header Cross-Origin
# FE dùng thẻ <canvas> hoặc PDF.js tải ảnh cần header 'Access-Control-Allow-Origin: *'
# để không bị lỗi "Canvas has been tainted by cross-origin data"
class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Cache-Control"] = "public, max-age=3600" # Cache 1h để zoom mượt mà
        return response

app.mount("/static", CORSStaticFiles(directory=str(BASE_STORAGE_DIR)), name="static")

# 4. Đăng ký các Router
## app.include_router(drawings_router, prefix="/api/v1")
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(drawings_router, prefix=settings.API_V1_STR)
app.include_router(components_router, prefix=settings.API_V1_STR)
app.include_router(discrepancies_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "message": "AI Drawing Analyzer API is running and Oke nhé Long Chun Thanks.",
        "docs": "/docs",
    }