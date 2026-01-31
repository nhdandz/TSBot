# 🎯 BẮT ĐẦU TẠI ĐÂY - TSBOT BACKEND

## 🚀 CÁCH NHANH NHẤT

Chạy script tự động để thiết lập mọi thứ:

```bash
bash quickstart.sh
```

Script sẽ tự động:
✅ Kiểm tra môi trường
✅ Tải các LLM models cần thiết
✅ Khởi động Docker containers (PostgreSQL + Qdrant)
✅ Tạo Python virtual environment
✅ Cài đặt dependencies
✅ Setup database và import dữ liệu
✅ Chạy backend server

**Thời gian ước tính:** 30-60 phút (tùy tốc độ mạng)

---

## 📚 TÀI LIỆU HƯỚNG DẪN

| File | Mục đích |
|------|----------|
| **QUICKSTART.md** | Hướng dẫn ngắn gọn từng bước |
| **BACKEND_SETUP.md** | Hướng dẫn chi tiết và troubleshooting |
| **check_setup.sh** | Script kiểm tra môi trường |
| **quickstart.sh** | Script tự động thiết lập |

---

## 🔧 YÊU CẦU HỆ THỐNG

### Phần mềm cần thiết:
- ✅ **Python 3.11+** (Bạn có: 3.12.2)
- ⚠️ **Docker & Docker Desktop** (Cần khởi động)
- ✅ **Ollama** (Đã cài và đang chạy)

### Phần cứng khuyến nghị:
- **RAM**: 16GB+ (để chạy LLM models)
- **Disk**: 15GB+ trống (cho models và data)
- **GPU**: Không bắt buộc (CPU cũng chạy được)

---

## 📋 CÁC BƯỚC THỦ CÔNG (nếu không dùng script)

### 1. Kiểm tra môi trường
```bash
bash check_setup.sh
```

### 2. Khởi động Docker Desktop
```bash
# Mở Docker Desktop từ Applications menu
# Hoặc: systemctl --user start docker-desktop
```

### 3. Tải LLM models
```bash
ollama pull qwen2.5:7b-instruct
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### 4. Khởi động databases
```bash
cd docker
docker-compose up -d postgres qdrant
```

### 5. Tạo Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 6. Setup database
```bash
python scripts/setup_database.py
python scripts/seed_data.py
```

### 7. Chạy backend
```bash
uvicorn src.api.main:app --reload
```

---

## ✅ KIỂM TRA

Sau khi chạy backend, truy cập:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000

Response mong đợi từ `/health`:
```json
{
  "status": "healthy",
  "services": {
    "postgres": "up",
    "qdrant": "up",
    "ollama": "up",
    "main_model": "ready",
    "grader_model": "ready"
  }
}
```

---

## 🎯 KẾT NỐI VỚI FRONTEND

Sau khi backend chạy ở `http://localhost:8000`, frontend của bạn sẽ tự động kết nối.

Đảm bảo trong `.env` có:
```
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

---

## ❓ GẶP VẤN ĐỀ?

### Lỗi "Docker daemon not running"
→ Khởi động Docker Desktop

### Lỗi "Ollama models not found"
→ Chạy: `ollama pull qwen2.5:7b-instruct`

### Lỗi "Cannot connect to PostgreSQL"
→ Chạy: `cd docker && docker-compose restart postgres`

### Các lỗi khác
→ Xem chi tiết trong **BACKEND_SETUP.md** phần Troubleshooting

---

## 📞 HỖ TRỢ

- 📖 Xem **BACKEND_SETUP.md** cho hướng dẫn chi tiết
- 🔍 Chạy `bash check_setup.sh` để kiểm tra môi trường
- 📝 Xem logs: `docker-compose logs -f` (trong folder docker/)

---

## 🎉 SẴN SÀNG?

```bash
# Chạy ngay:
bash quickstart.sh
```

Hoặc theo từng bước trong **QUICKSTART.md**

**Chúc bạn thành công! 🚀**
