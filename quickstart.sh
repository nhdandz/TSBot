#!/bin/bash

# TSBot Backend Quick Start Script
# Tự động hóa việc thiết lập và chạy backend

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 TSBOT BACKEND QUICK START${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for user
wait_for_user() {
    echo -e "${YELLOW}Nhấn Enter để tiếp tục...${NC}"
    read
}

# Step 1: Check prerequisites
echo -e "${GREEN}[1/7]${NC} Kiểm tra môi trường..."

if ! command_exists python3; then
    echo -e "${RED}✗ Python3 chưa cài đặt${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED}✗ Docker chưa cài đặt${NC}"
    exit 1
fi

if ! command_exists ollama; then
    echo -e "${RED}✗ Ollama chưa cài đặt${NC}"
    echo -e "${YELLOW}Cài đặt: curl -fsSL https://ollama.com/install.sh | sh${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tất cả prerequisites đã sẵn sàng${NC}"
echo ""

# Step 2: Check and pull Ollama models
echo -e "${GREEN}[2/7]${NC} Kiểm tra Ollama models..."

MODELS=$(ollama list 2>/dev/null || echo "")

if ! echo "$MODELS" | grep -q "qwen2.5:7b-instruct"; then
    echo -e "${YELLOW}⚠ Đang tải model qwen2.5:7b-instruct (~7GB)...${NC}"
    echo -e "${YELLOW}Quá trình này có thể mất 10-30 phút tùy tốc độ mạng${NC}"
    ollama pull qwen2.5:7b-instruct
    echo -e "${GREEN}✓ Đã tải xong qwen2.5:7b-instruct${NC}"
else
    echo -e "${GREEN}✓ Model qwen2.5:7b-instruct đã có${NC}"
fi

if ! echo "$MODELS" | grep -q "qwen2.5:1.5b"; then
    echo -e "${YELLOW}⚠ Đang tải model qwen2.5:1.5b (~1GB)...${NC}"
    ollama pull qwen2.5:1.5b
    echo -e "${GREEN}✓ Đã tải xong qwen2.5:1.5b${NC}"
else
    echo -e "${GREEN}✓ Model qwen2.5:1.5b đã có${NC}"
fi

if ! echo "$MODELS" | grep -q "nomic-embed-text"; then
    echo -e "${YELLOW}⚠ Đang tải model nomic-embed-text (~500MB)...${NC}"
    ollama pull nomic-embed-text
    echo -e "${GREEN}✓ Đã tải xong nomic-embed-text${NC}"
else
    echo -e "${GREEN}✓ Model nomic-embed-text đã có${NC}"
fi

echo ""

# Step 3: Start Docker containers
echo -e "${GREEN}[3/7]${NC} Khởi động Docker containers..."

cd docker

if ! docker ps | grep -q "tsbot-postgres"; then
    echo -e "${YELLOW}⚠ Khởi động PostgreSQL...${NC}"
    docker-compose up -d postgres
    echo -e "${YELLOW}Đợi PostgreSQL khởi động hoàn toàn...${NC}"
    sleep 10
else
    echo -e "${GREEN}✓ PostgreSQL đang chạy${NC}"
fi

if ! docker ps | grep -q "tsbot-qdrant"; then
    echo -e "${YELLOW}⚠ Khởi động Qdrant...${NC}"
    docker-compose up -d qdrant
    echo -e "${YELLOW}Đợi Qdrant khởi động hoàn toàn...${NC}"
    sleep 5
else
    echo -e "${GREEN}✓ Qdrant đang chạy${NC}"
fi

cd ..
echo ""

# Step 4: Create virtual environment
echo -e "${GREEN}[4/7]${NC} Thiết lập Python virtual environment..."

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Tạo virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Đã tạo venv${NC}"
else
    echo -e "${GREEN}✓ Virtual environment đã tồn tại${NC}"
fi

# Activate venv
source venv/bin/activate
echo ""

# Step 5: Install dependencies
echo -e "${GREEN}[5/7]${NC} Cài đặt Python dependencies..."

if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Đang cài đặt dependencies (có thể mất 5-15 phút)...${NC}"
    pip install --upgrade pip -q
    pip install -e . -q
    echo -e "${GREEN}✓ Đã cài đặt dependencies${NC}"
else
    echo -e "${GREEN}✓ Dependencies đã được cài đặt${NC}"
fi

echo ""

# Step 6: Setup database
echo -e "${GREEN}[6/7]${NC} Thiết lập database..."

# Check if tables exist
if python -c "from src.database.postgres import get_postgres_db; import asyncio; asyncio.run(get_postgres_db().health_check())" 2>/dev/null; then
    echo -e "${YELLOW}Bạn có muốn chạy lại setup database không? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${YELLOW}⚠ Đang setup database...${NC}"
        python scripts/setup_database.py
        echo -e "${GREEN}✓ Database đã được setup${NC}"

        echo -e "${YELLOW}⚠ Đang import dữ liệu mẫu...${NC}"
        python scripts/seed_data.py
        echo -e "${GREEN}✓ Dữ liệu đã được import${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Đang setup database...${NC}"
    python scripts/setup_database.py
    echo -e "${GREEN}✓ Database đã được setup${NC}"

    echo -e "${YELLOW}⚠ Đang import dữ liệu mẫu...${NC}"
    python scripts/seed_data.py
    echo -e "${GREEN}✓ Dữ liệu đã được import${NC}"
fi

echo ""

# Step 7: Optional - Index documents
echo -e "${GREEN}[7/7]${NC} Index documents (tùy chọn)..."
echo -e "${YELLOW}Bạn có muốn index documents để sử dụng RAG không? (y/N)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    if [ -d "data/documents" ] && [ "$(ls -A data/documents 2>/dev/null)" ]; then
        echo -e "${YELLOW}⚠ Đang xử lý và index documents...${NC}"
        python scripts/process_legal_docs.py
        python scripts/index_documents.py
        echo -e "${GREEN}✓ Documents đã được index${NC}"
    else
        echo -e "${RED}✗ Không tìm thấy documents trong data/documents/${NC}"
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ THIẾT LẬP HOÀN TẤT!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${BLUE}📝 Để chạy backend, sử dụng:${NC}"
echo ""
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload${NC}"
echo ""

echo -e "${BLUE}🌐 Sau khi chạy, truy cập:${NC}"
echo -e "  • API Docs: ${YELLOW}http://localhost:8000/docs${NC}"
echo -e "  • Health Check: ${YELLOW}http://localhost:8000/health${NC}"
echo ""

echo -e "${YELLOW}Bạn có muốn chạy backend server ngay bây giờ? (y/N)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo -e "${GREEN}🚀 Đang khởi động backend server...${NC}"
    echo -e "${YELLOW}Nhấn Ctrl+C để dừng server${NC}"
    echo ""
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo ""
    echo -e "${GREEN}Tuyệt vời! Bạn có thể chạy backend bất cứ lúc nào bằng lệnh trên.${NC}"
    echo ""
fi
