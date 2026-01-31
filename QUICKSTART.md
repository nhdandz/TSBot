# ⚡ QUICK START - CHẠY BACKEND NGAY

Dựa trên kiểm tra môi trường, đây là các bước bạn cần làm:

## 🎯 TÓM TẮT TRẠNG THÁI

✅ **Đã có:**
- Python 3.12.2
- Ollama (đang chạy)
- File .env cấu hình
- Dữ liệu văn bản

⚠️ **Cần thiết lập:**
- Tải LLM models
- Khởi động Docker containers
- Tạo Python environment
- Setup database

---

## 📝 CÁC BƯỚC THỰC HIỆN

### Bước 1: Khởi động Docker Desktop
```bash
# Mở Docker Desktop từ menu Applications
# Hoặc từ command line:
systemctl --user start docker-desktop

# Đợi Docker Desktop khởi động hoàn toàn (biểu tượng Docker trên thanh taskbar)
```

### Bước 2: Tải LLM Models (mất 10-30 phút)
```bash
# Mở terminal mới, chạy lần lượt:
ollama pull qwen2.5:7b-instruct     # ~7GB
ollama pull qwen2.5:1.5b            # ~1GB

# Kiểm tra đã tải xong:
ollama list
```

### Bước 3: Khởi động Database Containers
```bash
cd docker
docker-compose up -d postgres qdrant

# Kiểm tra đã chạy:
docker-compose ps
```

### Bước 4: Tạo Python Virtual Environment
```bash
cd /home/admin123/Downloads/NHDanDz/TSBot

# Tạo venv
python3 -m venv venv

# Kích hoạt
source venv/bin/activate

# Cài đặt dependencies (mất 5-15 phút)
pip install --upgrade pip
pip install -e .
```

### Bước 5: Setup Database
```bash
# Đảm bảo venv đã kích hoạt (thấy (venv) ở đầu dòng)
python scripts/setup_database.py
python scripts/seed_data.py
```

### Bước 6: Index Documents (tùy chọn)
```bash
# Nếu muốn sử dụng tính năng RAG với văn bản pháp luật
python scripts/process_legal_docs.py
python scripts/index_documents.py
```

### Bước 7: Chạy Backend Server
```bash
# Vẫn trong venv
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ✅ KIỂM TRA

Mở trình duyệt, truy cập:
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

Nếu thấy status "healthy" và tất cả services "up" → Thành công! 🎉

---

## 🚀 SCRIPT TỰ ĐỘNG (Khuyên dùng)

Tôi đã tạo script để tự động hóa các bước:

```bash
# Kiểm tra môi trường
bash check_setup.sh

# Nếu đã sẵn sàng, chạy script này:
bash quickstart.sh
```

---

## 📊 CẤU TRÚC TERMINAL

Để chạy đầy đủ, bạn cần **3 terminals**:

**Terminal 1 - Ollama:**
```bash
ollama serve  # Giữ terminal này chạy
```

**Terminal 2 - Docker:**
```bash
cd docker
docker-compose up postgres qdrant  # Không dùng -d nếu muốn xem logs
```

**Terminal 3 - Backend:**
```bash
source venv/bin/activate
uvicorn src.api.main:app --reload
```

---

## ❓ GẶP VẤN ĐỀ?

Xem file **BACKEND_SETUP.md** để có hướng dẫn chi tiết và troubleshooting.

---

**Thời gian ước tính tổng:** 30-60 phút (phụ thuộc tốc độ mạng)
