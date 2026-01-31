# 🚀 HƯỚNG DẪN CHẠY BACKEND - TSBOT

## 📌 Tổng quan

Backend TSBot cần **4 thành phần** chính:
1. **Ollama** - Server LLM (chạy model Qwen2.5)
2. **PostgreSQL** - Database chính (lưu dữ liệu điểm chuẩn, trường học)
3. **Qdrant** - Vector database (lưu embeddings cho RAG)
4. **Python FastAPI** - Backend API server

---

## ✅ Bước 1: Cài đặt Ollama và tải Models

### 1.1. Cài đặt Ollama

```bash
# Trên Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Hoặc tải từ: https://ollama.com/download
```

### 1.2. Khởi động Ollama server

```bash
ollama serve
```

Giữ terminal này chạy, hoặc chạy dưới dạng service.

### 1.3. Tải các models cần thiết (trong terminal mới)

```bash
# Model chính cho generation (7GB)
ollama pull qwen2.5:7b-instruct

# Model nhỏ cho grading (1GB)
ollama pull qwen2.5:1.5b

# Model embedding (500MB)
ollama pull nomic-embed-text
```

**⏱️ Lưu ý**: Quá trình tải model có thể mất 10-30 phút tùy tốc độ mạng.

### 1.4. Kiểm tra Ollama

```bash
# Test xem Ollama có chạy không
curl http://localhost:11434/api/tags

# Test model
ollama run qwen2.5:7b-instruct "Xin chào"
```

---

## ✅ Bước 2: Khởi động PostgreSQL và Qdrant bằng Docker

### 2.1. Di chuyển vào thư mục docker

```bash
cd /home/admin123/Downloads/NHDanDz/TSBot/docker
```

### 2.2. Khởi động database containers

```bash
# Khởi động PostgreSQL và Qdrant
docker-compose up -d postgres qdrant

# Kiểm tra trạng thái
docker-compose ps
```

Bạn sẽ thấy 2 containers:
- `tsbot-postgres` - Chạy trên port 5432
- `tsbot-qdrant` - Chạy trên port 6333

### 2.3. Kiểm tra kết nối

```bash
# Kiểm tra PostgreSQL
docker exec -it tsbot-postgres pg_isready -U tsbot

# Kiểm tra Qdrant (mở trong browser)
# http://localhost:6333/dashboard
```

---

## ✅ Bước 3: Cài đặt Python Environment

### 3.1. Quay lại thư mục gốc dự án

```bash
cd /home/admin123/Downloads/NHDanDz/TSBot
```

### 3.2. Kiểm tra Python version (cần >= 3.11)

```bash
python3 --version
```

### 3.3. Tạo virtual environment

```bash
# Tạo virtual environment
python3 -m venv venv

# Kích hoạt virtual environment
source venv/bin/activate
```

### 3.4. Cài đặt dependencies

```bash
# Upgrade pip trước
pip install --upgrade pip

# Cài đặt tất cả dependencies (có thể mất 5-15 phút)
pip install -e .
```

**⚠️ Lưu ý**:
- Nếu gặp lỗi khi cài `torch`, có thể cần cài riêng:
  ```bash
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  ```
- Nếu thiếu build tools: `sudo apt install build-essential python3-dev`

---

## ✅ Bước 4: Thiết lập Database và Dữ liệu

### 4.1. Tạo schema và extensions cho PostgreSQL

```bash
python scripts/setup_database.py
```

### 4.2. Import dữ liệu mẫu (điểm chuẩn, trường học)

```bash
python scripts/seed_data.py
```

### 4.3. Xử lý và index documents (văn bản pháp luật)

```bash
# Đảm bảo có file văn bản trong data/documents/
python scripts/process_legal_docs.py
python scripts/index_documents.py
```

---

## ✅ Bước 5: Chạy Backend Server

### 5.1. Đảm bảo virtual environment đã được kích hoạt

```bash
source venv/bin/activate  # Nếu chưa kích hoạt
```

### 5.2. Chạy FastAPI server

```bash
# Cách 1: Dùng uvicorn trực tiếp
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Cách 2: Dùng script có sẵn
python -m src.api.main

# Cách 3: Dùng command đã định nghĩa
tsbot
```

### 5.3. Kiểm tra server

Mở trình duyệt và truy cập:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000

Bạn sẽ thấy API documentation và có thể test các endpoints.

---

## 🧪 Kiểm tra toàn bộ hệ thống

### Kiểm tra Health Check

```bash
curl http://localhost:8000/health
```

Response mong đợi:
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

### Test API chat

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Điểm chuẩn Học viện Kỹ thuật Quân sự năm 2024 là bao nhiêu?"}'
```

---

## 🔧 Troubleshooting (Xử lý lỗi thường gặp)

### 1. Lỗi "Ollama not running"
```bash
# Kiểm tra Ollama service
ps aux | grep ollama

# Khởi động lại
ollama serve
```

### 2. Lỗi "Cannot connect to PostgreSQL"
```bash
# Kiểm tra container
docker ps | grep postgres

# Xem logs
docker logs tsbot-postgres

# Khởi động lại
cd docker && docker-compose restart postgres
```

### 3. Lỗi "Qdrant connection failed"
```bash
# Kiểm tra container
docker ps | grep qdrant

# Xem logs
docker logs tsbot-qdrant

# Khởi động lại
cd docker && docker-compose restart qdrant
```

### 4. Lỗi khi cài đặt Python packages
```bash
# Cài build essentials
sudo apt update
sudo apt install build-essential python3-dev libpq-dev

# Thử lại
pip install -e .
```

### 5. Model không load được
```bash
# Kiểm tra models đã tải
ollama list

# Tải lại model
ollama pull qwen2.5:7b-instruct
```

---

## 📝 Cấu hình nâng cao

### Chỉnh sửa file .env

File `.env` chứa các cấu hình quan trọng:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=tsbot
POSTGRES_PASSWORD=tsbot_secret_password

# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MAIN_MODEL=qwen2.5:7b-instruct

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

---

## 🛑 Tắt hệ thống

```bash
# 1. Tắt FastAPI server: Nhấn Ctrl+C trong terminal

# 2. Tắt Docker containers
cd docker
docker-compose down

# 3. Tắt Ollama: Nhấn Ctrl+C hoặc
pkill ollama

# 4. Deactivate virtual environment
deactivate
```

---

## 📊 Tóm tắt Commands

```bash
# === KHỞI ĐỘNG HỆ THỐNG ===

# 1. Khởi động Ollama (terminal 1)
ollama serve

# 2. Khởi động Databases (terminal 2)
cd docker && docker-compose up -d postgres qdrant

# 3. Khởi động Backend (terminal 3)
cd /home/admin123/Downloads/NHDanDz/TSBot
source venv/bin/activate
uvicorn src.api.main:app --reload

# === KIỂM TRA ===
curl http://localhost:8000/health
```

---

## 🎯 Kết nối với Frontend

Sau khi Backend chạy thành công:
- Backend API: http://localhost:8000
- Frontend đã chạy sẽ tự động kết nối đến backend này
- Kiểm tra CORS_ORIGINS trong .env có chứa địa chỉ frontend

---

## 📚 Tài liệu thêm

- **API Documentation**: http://localhost:8000/docs
- **Ollama Docs**: https://ollama.com/docs
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **FastAPI**: https://fastapi.tiangolo.com

---

**Chúc bạn setup thành công! 🎉**
