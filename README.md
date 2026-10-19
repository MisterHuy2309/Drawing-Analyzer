# 🏗️ AI Drawing Analyzer - Fullstack Setup & API Documentation

Hệ thống phân tích bản vẽ kết cấu kỹ thuật: tiếp nhận hồ sơ PDF, bóc tách trang nền (Background Tasks), render ảnh độ phân giải cao (200 DPI), tạo thumbnail, trích xuất tọa độ Bounding Box văn bản và lưu trữ trong cơ sở dữ liệu PostgreSQL.

- **Sơ đồ thiết kế Database (DB Diagram):** [Xem tại dbdiagram.io](https://dbdiagram.io/d/Building-6ad58bdafe5cc8bda2f11289)

---

## 💻 Dành cho Frontend: Hướng dẫn Clone và Khởi chạy toàn bộ hệ thống

Khi clone repository về máy cục bộ, các bạn làm theo các bước tuần tự bên dưới để dựng Database, chạy Backend và kết nối Frontend.

### Yêu cầu cài đặt sẵn trên máy:
1. **Docker Desktop** (Bắt buộc phải bật Docker lên trước khi chạy lệnh).
2. **Python 3.12+** và công cụ quản lý gói **Poetry** (`pip install poetry`).
3. **Node.js** (v18 trở lên).

---

### PHẦN 1: KHỞI CHẠY DATABASE & BACKEND (Terminal 1)

#### Bước 1: Khởi động Database PostgreSQL qua Docker
Mở cửa sổ Terminal tại thư mục gốc dự án (`Building/`):
```powershell
# Bật container PostgreSQL chạy ngầm
docker compose up -d

# Kiểm tra container đã UP thành công (port 5434 -> 5432)
docker ps