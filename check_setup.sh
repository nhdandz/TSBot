#!/bin/bash

# Script kiểm tra môi trường setup cho TSBot Backend
# Chạy: bash check_setup.sh

echo "🔍 KIỂM TRA MÔI TRƯỜNG TSBOT BACKEND"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES=0

# Check Python
echo "1️⃣  Kiểm tra Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    echo -e "   ${GREEN}✓${NC} Python đã cài: $PYTHON_VERSION"

    # Check version >= 3.11
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
        echo -e "   ${GREEN}✓${NC} Version đạt yêu cầu (>= 3.11)"
    else
        echo -e "   ${RED}✗${NC} Cần Python >= 3.11 (hiện tại: $PYTHON_VERSION)"
        ISSUES=$((ISSUES+1))
    fi
else
    echo -e "   ${RED}✗${NC} Python3 chưa được cài đặt"
    echo -e "   ${YELLOW}→${NC} Cài đặt: sudo apt install python3 python3-pip python3-venv"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check Docker
echo "2️⃣  Kiểm tra Docker..."
if command -v docker &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Docker đã cài"
    if command -v docker-compose &> /dev/null; then
        echo -e "   ${GREEN}✓${NC} Docker Compose đã cài"
    else
        echo -e "   ${RED}✗${NC} Docker Compose chưa cài"
        echo -e "   ${YELLOW}→${NC} Cài đặt: sudo apt install docker-compose"
        ISSUES=$((ISSUES+1))
    fi
else
    echo -e "   ${RED}✗${NC} Docker chưa được cài đặt"
    echo -e "   ${YELLOW}→${NC} Xem hướng dẫn: https://docs.docker.com/engine/install/"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check Ollama
echo "3️⃣  Kiểm tra Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "   ${GREEN}✓${NC} Ollama đã cài"

    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "   ${GREEN}✓${NC} Ollama server đang chạy"

        # Check models
        MODELS=$(ollama list 2>/dev/null)
        if echo "$MODELS" | grep -q "qwen2.5:7b-instruct"; then
            echo -e "   ${GREEN}✓${NC} Model qwen2.5:7b-instruct đã tải"
        else
            echo -e "   ${YELLOW}⚠${NC} Model qwen2.5:7b-instruct chưa tải"
            echo -e "   ${YELLOW}→${NC} Chạy: ollama pull qwen2.5:7b-instruct"
        fi

        if echo "$MODELS" | grep -q "qwen2.5:1.5b"; then
            echo -e "   ${GREEN}✓${NC} Model qwen2.5:1.5b đã tải"
        else
            echo -e "   ${YELLOW}⚠${NC} Model qwen2.5:1.5b chưa tải"
            echo -e "   ${YELLOW}→${NC} Chạy: ollama pull qwen2.5:1.5b"
        fi

        if echo "$MODELS" | grep -q "nomic-embed-text"; then
            echo -e "   ${GREEN}✓${NC} Model nomic-embed-text đã tải"
        else
            echo -e "   ${YELLOW}⚠${NC} Model nomic-embed-text chưa tải"
            echo -e "   ${YELLOW}→${NC} Chạy: ollama pull nomic-embed-text"
        fi
    else
        echo -e "   ${YELLOW}⚠${NC} Ollama server chưa chạy"
        echo -e "   ${YELLOW}→${NC} Khởi động: ollama serve"
    fi
else
    echo -e "   ${RED}✗${NC} Ollama chưa được cài đặt"
    echo -e "   ${YELLOW}→${NC} Cài đặt: curl -fsSL https://ollama.com/install.sh | sh"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check Docker containers
echo "4️⃣  Kiểm tra Docker containers..."
if command -v docker &> /dev/null; then
    if docker ps | grep -q "tsbot-postgres"; then
        echo -e "   ${GREEN}✓${NC} PostgreSQL container đang chạy"
    else
        echo -e "   ${YELLOW}⚠${NC} PostgreSQL container chưa chạy"
        echo -e "   ${YELLOW}→${NC} Khởi động: cd docker && docker-compose up -d postgres"
    fi

    if docker ps | grep -q "tsbot-qdrant"; then
        echo -e "   ${GREEN}✓${NC} Qdrant container đang chạy"
    else
        echo -e "   ${YELLOW}⚠${NC} Qdrant container chưa chạy"
        echo -e "   ${YELLOW}→${NC} Khởi động: cd docker && docker-compose up -d qdrant"
    fi
fi
echo ""

# Check .env file
echo "5️⃣  Kiểm tra file cấu hình..."
if [ -f ".env" ]; then
    echo -e "   ${GREEN}✓${NC} File .env đã tồn tại"
else
    echo -e "   ${YELLOW}⚠${NC} File .env chưa tồn tại"
    echo -e "   ${YELLOW}→${NC} Tạo từ mẫu: cp .env.example .env"
fi
echo ""

# Check virtual environment
echo "6️⃣  Kiểm tra Python virtual environment..."
if [ -d "venv" ]; then
    echo -e "   ${GREEN}✓${NC} Virtual environment đã tạo"

    if [ -f "venv/bin/python" ]; then
        # Check if packages are installed
        if ./venv/bin/python -c "import fastapi" 2>/dev/null; then
            echo -e "   ${GREEN}✓${NC} Dependencies đã được cài đặt"
        else
            echo -e "   ${YELLOW}⚠${NC} Dependencies chưa được cài đặt"
            echo -e "   ${YELLOW}→${NC} Cài đặt: source venv/bin/activate && pip install -e ."
        fi
    fi
else
    echo -e "   ${YELLOW}⚠${NC} Virtual environment chưa được tạo"
    echo -e "   ${YELLOW}→${NC} Tạo mới: python3 -m venv venv"
fi
echo ""

# Check data directory
echo "7️⃣  Kiểm tra thư mục dữ liệu..."
if [ -d "data" ]; then
    echo -e "   ${GREEN}✓${NC} Thư mục data đã tồn tại"

    if [ -d "data/documents" ] && [ "$(ls -A data/documents 2>/dev/null)" ]; then
        echo -e "   ${GREEN}✓${NC} Có văn bản trong data/documents"
    else
        echo -e "   ${YELLOW}⚠${NC} Chưa có văn bản pháp luật trong data/documents"
        echo -e "   ${YELLOW}→${NC} Thêm file .txt, .pdf, .docx vào data/documents/"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} Thư mục data chưa tồn tại"
fi
echo ""

# Summary
echo "=========================================="
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ Môi trường đã sẵn sàng!${NC}"
    echo ""
    echo "📝 Các bước tiếp theo:"
    echo "   1. Khởi động Docker: cd docker && docker-compose up -d postgres qdrant"
    echo "   2. Khởi động Ollama (nếu chưa): ollama serve"
    echo "   3. Setup database: python scripts/setup_database.py"
    echo "   4. Import dữ liệu: python scripts/seed_data.py"
    echo "   5. Chạy backend: uvicorn src.api.main:app --reload"
else
    echo -e "${RED}✗ Phát hiện $ISSUES vấn đề cần khắc phục${NC}"
    echo ""
    echo "📖 Xem hướng dẫn chi tiết tại: BACKEND_SETUP.md"
fi
echo ""
