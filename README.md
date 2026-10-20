# 🏗️ AI Drawing Analyzer - Backend Service & API Documentation

Hệ thống Backend FastAPI phục vụ phân tích bản vẽ kết cấu kỹ thuật:
- Tiếp nhận hồ sơ PDF và xử lý ngầm (Background Tasks).
- Tách trang tự động, render ảnh độ phân giải cao (200 DPI) và thumbnail (50 DPI).
- Trích xuất tọa độ Bounding Box của văn bản (Text Blocks) và hình học vector (Table Rects).
- Cung cấp API quản lý dự án, cấu kiện kết cấu dầm/cột và đối chiếu sai lệch.
- Sơ đồ Database: https://dbdiagram.io/d/Building-6ad58bdafe5cc8bda2f11289

---

## 🛠️ Yêu cầu môi trường trước khi cài đặt

1. **Docker Desktop**: Bắt buộc cài đặt và bật ứng dụng Docker Desktop trước khi chạy lệnh.
2. **Python 3.12+**: Đã tích hợp biến môi trường (Add Python to PATH).
3. **Poetry**: Công cụ quản lý môi trường ảo và thư viện độc lập.
   - Cài đặt bằng lệnh: `pip install poetry`
   - cd backend --> `pip install poetry`

---

## 🚀 Hướng dẫn khởi chạy Backend từng bước

### Bước 1: Khởi động Database PostgreSQL qua Docker

Mở Terminal tại thư mục gốc dự án (Building/):

```powershell
# Bật container PostgreSQL chạy ngầm
docker compose up -d

# Kiểm tra container đã hoạt động thành công
docker ps