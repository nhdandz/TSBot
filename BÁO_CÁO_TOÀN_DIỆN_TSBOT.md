# BÁO CÁO TOÀN DIỆN: HỆ THỐNG CHATBOT AI TƯ VẤN TUYỂN SINH QUÂN SỰ (TSBOT)
**Ngày:** 08/03/2026 | **Mục đích:** Báo cáo nội bộ, trình sếp phê duyệt

---

## MỤC LỤC
1. [Tổng quan kiến trúc hiện tại](#1-tổng-quan)
2. [Vấn đề tồn tại (Issues)](#2-vấn-đề-tồn-tại)
3. [Phân tích khả năng trả lời đúng](#3-khả-năng-trả-lời-đúng)
4. [Khả năng đáp ứng nhiều người dùng](#4-khả-năng-mở-rộng)
5. [Ý tưởng cải tiến chi tiết](#5-cải-tiến)
6. [Benchmark các thành phần](#6-benchmark)
7. [Ước tính chi phí thuê server](#7-chi-phí-server)
8. [Lộ trình và kế hoạch triển khai](#8-kế-hoạch)

---

## 1. TỔNG QUAN KIẾN TRÚC HIỆN TẠI

### 1.1 Kiến trúc đang chạy

```
User → Nginx (HTTPS) → FastAPI → Supervisor Agent (LangGraph)
                                        ↓
                          ┌─────────────────────────┐
                          │    Semantic Router       │
                          │    (vector similarity)   │
                          └────────┬────────────────-┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
        SQL Agent           RAG Agent           General Agent
        (điểm chuẩn)      (văn bản PQ)         (chào hỏi)
              ↓                    ↓
         PostgreSQL            Qdrant
       (view_tra_cuu_diem)  (BGE-M3 vectors)
              ↓                    ↓
          vLLM (A100)          vLLM (A100)
        Qwen2.5-7B            Qwen2.5-7B
```

### 1.2 Hạ tầng hiện tại
| Thành phần | Mô tả |
|-----------|-------|
| **Máy ứng dụng** | GPU 16GB VRAM — chạy embedding (BGE-M3), FastAPI, DB |
| **Máy A100** | GPU 80GB VRAM — chạy vLLM (Qwen2.5-7B main + grader) |
| **Database** | PostgreSQL 16 + Qdrant (vector) + Redis (cache) |
| **Frontend** | React/TypeScript (Vite) — serve qua Nginx |
| **Auth** | JWT, rate limit 30 req/min (chat), 5/min (login) |
| **Streaming** | SSE (`/api/v1/chat/stream`) — token-by-token |

---

## 2. VẤN ĐỀ TỒN TẠI (ISSUES)

### 2.1 Vấn đề về độ chính xác câu trả lời

#### ❌ Issue #1: Routing sai ở câu hỏi phức tạp (Hybrid Queries)
- **Mô tả:** Câu hỏi kiểu *"Với 24 điểm, tôi có đủ điều kiện vào HVKTQS không và cần chuẩn bị giấy tờ gì?"* vừa cần SQL (điểm chuẩn) vừa cần RAG (hồ sơ). Hiện tại router chọn **một** trong hai, bỏ sót thông tin còn lại.
- **Nguy cơ:** Câu trả lời thiếu, gây hiểu nhầm cho thí sinh.
- **Tần suất ước tính:** ~15–20% câu hỏi thực tế thuộc dạng hybrid.

#### ❌ Issue #2: SQL Agent sinh sai khi thiếu ví dụ Few-Shot
- **Mô tả:** Hệ thống dùng Zero-shot (chỉ có System Prompt) để sinh SQL. Với các câu hỏi phức tạp như "so sánh điểm chuẩn nam/nữ các ngành HVKTQS theo khối A00 qua 3 năm", LLM đôi khi quên bộ lọc `gioi_tinh`, `khu_vuc` hoặc sinh sai mệnh đề `WHERE`.
- **Nguy cơ:** Trả về dữ liệu không đúng mà không có cảnh báo.
- **Quan sát:** Hệ thống có validation prompt nhưng LLM grader cũng có thể bỏ sót.

#### ❌ Issue #3: RAG Chunking chưa tối ưu cho văn bản pháp lý
- **Mô tả:** Quy chế tuyển sinh có cấu trúc *Chương → Điều → Khoản → Điểm*. Chunking hiện tại chưa phân tích cấu trúc này, có thể cắt đứt giữa "Khoản 3" và "Điều 12" mà nó thuộc về.
- **Nguy cơ:** LLM nhận ngữ cảnh không đầy đủ → trả lời thiếu điều kiện → nghiêm trọng với quy định pháp luật.

#### ❌ Issue #4: Không có cơ chế tự kiểm tra (Self-Verification)
- **Mô tả:** Khi RAG trả về câu trả lời, không có bước nào verify xem thông tin có đúng với tài liệu gốc không (Faithfulness check).
- **Nguy cơ:** Hallucination — LLM "sáng tạo" thêm thông tin ngoài context.

#### ❌ Issue #5: Không xử lý tốt câu hỏi follow-up (ngữ cảnh hội thoại)
- **Mô tả:** Hệ thống lấy 5 messages lịch sử từ DB truyền vào state, nhưng routing và SQL generation KHÔNG sử dụng hội thoại trước để phân giải đại từ ("Thế còn trường đó?", "Năm ngoái thì sao?").
- **Ví dụ fail:** User hỏi "Điểm chuẩn HVKTQS 2024?" → Bot trả lời → User hỏi "Thế còn năm 2023?" → SQL Agent sinh query thiếu tên trường vì không xử lý ngữ cảnh.

#### ❌ Issue #6: Dataset đánh giá còn nhỏ (10 mẫu)
- **Mô tả:** Bộ `golden_dataset.json` chỉ có 10 câu hỏi. RAGAS chạy trên 10 mẫu không đại diện, không phát hiện được edge cases.
- **Cần:** Tối thiểu 100–200 mẫu đa dạng (điểm chuẩn, quy chế, thủ tục, ưu tiên...).

### 2.2 Vấn đề về kiểm soát câu trả lời

#### ⚠️ Issue #7: Thiếu Safety Layer cho thông tin nhạy cảm
- **Mô tả:** Không có lớp kiểm soát để ngăn bot trả lời sai về thông tin pháp lý quan trọng (điểm chuẩn sai năm, điều kiện sức khỏe sai...). Câu trả lời không có disclaimer khi độ tin cậy thấp.
- **Rủi ro:** Thí sinh tin theo thông tin sai → thiệt hại thực tế.

#### ⚠️ Issue #8: Không có cơ chế Human-in-the-Loop
- **Mô tả:** Admin chưa có giao diện review/approve câu trả lời trước khi public. Không có hệ thống đánh dấu câu hỏi "không trả lời được" để bổ sung dữ liệu.

#### ⚠️ Issue #9: Prompt injection chưa được bảo vệ hoàn toàn
- **Mô tả:** User có thể cố tình chèn lệnh vào câu hỏi ("Ignore all instructions..."). Chưa có input sanitization chuyên biệt cho prompt injection.

### 2.3 Vấn đề về khả năng bao quát câu hỏi

#### ⚠️ Issue #10: Chưa bao quát đủ intents
- Hiện tại: ~17 intent types trong `intents.json`
- **Thiếu:** Câu hỏi về học phí/chế độ đãi ngộ, cơ hội sau tốt nghiệp, kinh nghiệm luyện thi, điểm ưu tiên tính như thế nào, điểm sàn khác điểm chuẩn như thế nào...
- **Ước tính gap:** Khoảng 30–40% câu hỏi từ thí sinh thực tế chưa được cover đầy đủ bởi dữ liệu RAG.

#### ⚠️ Issue #11: Dữ liệu điểm chuẩn chỉ có 2 năm (2023–2024)
- **Vấn đề:** Dự đoán xu hướng với 2 data points không có ý nghĩa thống kê. Linear regression với numpy.polyfit trên 2 điểm chỉ là đường thẳng qua 2 điểm.
- **Khuyến nghị:** Cần ít nhất 5 năm dữ liệu để dự đoán có giá trị.

---

## 3. KHẢ NĂNG TRẢ LỜI ĐÚNG (ACCURACY ANALYSIS)

### 3.1 Phân loại câu hỏi và độ chính xác ước tính

| Loại câu hỏi | % tần suất | Độ chính xác hiện tại | Ghi chú |
|-------------|-----------|----------------------|---------|
| Điểm chuẩn năm cụ thể | 35% | ~85% | SQL đơn giản, ổn |
| So sánh điểm chuẩn qua năm | 15% | ~70% | Hay miss filter |
| Tiêu chuẩn sức khỏe | 10% | ~80% | RAG tốt nếu chunk đúng |
| Quy trình đăng ký/hồ sơ | 15% | ~75% | RAG nhưng thiếu context |
| Điều kiện ưu tiên | 8% | ~65% | Phức tạp, dễ hallucinate |
| Giới thiệu trường | 7% | ~90% | DB lookup, ổn |
| Câu hỏi hybrid (SQL+RAG) | 10% | ~50% | Điểm yếu lớn nhất |

**Ước tính tổng thể: ~75% câu trả lời đạt yêu cầu** (chưa có benchmark thực tế đủ lớn để xác nhận con số này)

### 3.2 Cách đo lường (đề xuất chạy ngay)
```bash
# Chạy RAGAS evaluation (cần mở rộng dataset lên 100 mẫu trước)
python scripts/run_evaluation.py --limit 100 --metrics faithfulness,answer_relevancy,context_recall

# Kết quả mục tiêu cần đạt:
# - Faithfulness: > 0.85 (quan trọng nhất — không hallucinate)
# - Answer Relevancy: > 0.80
# - Context Recall: > 0.75
```

---

## 4. KHẢ NĂNG ĐÁP ỨNG NHIỀU NGƯỜI DÙNG (SCALABILITY)

### 4.1 Cấu hình phần cứng đã xác nhận

| Máy | Phần cứng | Chức năng |
|-----|-----------|-----------|
| Máy Application | GPU 16GB VRAM | FastAPI, BGE-M3 embedding, PostgreSQL, Qdrant, Redis |
| Máy A100 | **NVIDIA A100 80GB** | vLLM — Qwen2.5-7B-Instruct (main + grader cùng 1 instance) |

### 4.2 Thông số vLLM đã cấu hình (từ `docker/vllm-a100.sh`)

| Tham số | Giá trị | Nguồn |
|---------|---------|-------|
| Model | Qwen/Qwen2.5-7B-Instruct | config |
| dtype | float16 | config |
| gpu_memory_utilization | 0.90 | config |
| max_model_len | 8,192 tokens | config |
| max_num_seqs | 128 | config |
| tensor_parallel_size | 1 | config |
| chunked_prefill | enabled | config |

### 4.3 Phân tích KV Cache (tính toán lý thuyết)

Qwen2.5-7B architecture: **28 layers, 8 KV heads (GQA), head_dim=128, fp16**

```
KV cache per token (1 layer)  = 2 (K+V) × 8 heads × 128 dim × 2 bytes = 4,096 bytes
KV cache per token (all 28L)  = 4,096 × 28                             = 112 KB/token

VRAM allocation:
  Tổng VRAM                   = 80 GB × 0.90                           = 72 GB
  Model weights (7.6B × 2B)   ≈ 15.2 GB
  Còn lại cho KV cache        ≈ 56.8 GB

Số sequence tối đa:
  Worst case (8,192 token/seq): 56.8 GB / 0.9 GB ≈ 63 sequences
  Avg case (~1,000 token/seq):  56.8 GB / 0.11 GB ≈ 516 sequences
  → Hard cap bởi max_num_seqs = 128
```

**Kết luận:** vLLM có thể xử lý **tối đa 128 sequences song song** (nếu trung bình < 3,500 token/seq), hoặc ~63 nếu mỗi session dùng gần hết 8,192 token context.

> ⚠️ **Lưu ý:** Đây là con số lý thuyết tính từ kiến trúc model và cấu hình. Số liệu thực tế cần đo bằng load test (xem 4.5).

### 4.4 Giới hạn đã biết từ config

| Thành phần | Giới hạn cấu hình | Ghi chú |
|-----------|------------------|---------|
| Rate limit chat | **30 req/phút / IP** | slowapi, từ code |
| Rate limit login | **5 req/phút / IP** | slowapi, từ code |
| PostgreSQL | **60 connections** (pool=20 + overflow=40) | từ .env.production |
| vLLM max sequences | **128 concurrent** | max_num_seqs trong script |
| API Workers | **1 uvicorn worker** | API_WORKERS=1 trong .env |
| BGE-M3 | Chạy non-blocking (run_in_executor) | từ embeddings.py |

**Điểm cần lưu ý về API_WORKERS=1:** FastAPI chạy async nên 1 worker vẫn phục vụ nhiều request đồng thời qua event loop. Chỉ trở thành vấn đề nếu có tác vụ blocking CPU-bound mà không dùng executor.

### 4.5 Những con số chưa có — cần đo thực tế

Các số liệu sau **chưa được benchmark**, không nên đưa vào báo cáo kỹ thuật mà không có chú thích:

| Cần đo | Cách đo |
|--------|---------|
| Throughput tokens/s thực tế của vLLM | `python -m vllm.benchmark_throughput` |
| End-to-end latency P50/P95 | Locust hoặc k6 load test |
| Số concurrent users thực tế trước khi degraded | Locust với ramp-up |
| Cache hit rate của Redis | Xem metrics Redis sau 1 tuần chạy thật |

```bash
# Lệnh benchmark vLLM (chạy trực tiếp trên máy A100)
docker exec tsbot-vllm python -m vllm.benchmark_throughput \
  --model Qwen/Qwen2.5-7B-Instruct \
  --num-prompts 200 \
  --input-len 200 \
  --output-len 300
```

### 4.6 Cách scale khi cần (theo thứ tự ưu tiên)

1. **Ngay bây giờ (miễn phí):** Cấu hình `max-num-seqs=128` + `enable-chunked-prefill` đã được thêm vào script — cần restart vLLM container để có hiệu lực
2. **Nếu tải tăng cao:** Tăng `API_WORKERS` lên 2-3 trên máy 16GB (mỗi worker load thêm BGE-M3 ~1.5GB VRAM)
3. **Scale lớn (>200 concurrent users):** Cần load test để xác định bottleneck thực tế trước khi quyết định thêm phần cứng

---

## 5. Ý TƯỞNG CẢI TIẾN CHI TIẾT

### 5.1 [QUAN TRỌNG NHẤT] Dynamic Few-Shot SQL

**Vấn đề giải quyết:** Issue #2 — SQL sinh sai

**Cách triển khai cụ thể:**

Bước 1: Tạo file `data/few_shot_sql.json` với 80-100 cặp (câu hỏi → SQL chuẩn):
```json
[
  {
    "question": "Điểm chuẩn nam miền bắc học viện kỹ thuật quân sự năm 2024 khối A00",
    "sql": "SELECT nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan, chi_tieu FROM view_tra_cuu_diem WHERE ten_khong_dau ILIKE '%hoc vien ky thuat quan su%' AND gioi_tinh = 'nam' AND khu_vuc = 'mien_bac' AND nam = 2024 AND ma_khoi = 'A00' ORDER BY ten_nganh LIMIT 50;"
  },
  {
    "question": "so sánh điểm chuẩn học viện hải quân và trường sĩ quan lục quân 1 năm 2023",
    "sql": "SELECT nam, ten_truong, ten_nganh, ma_khoi, gioi_tinh, khu_vuc, diem_chuan, chi_tieu FROM view_tra_cuu_diem WHERE (ten_khong_dau ILIKE '%hoc vien hai quan%' OR ten_khong_dau ILIKE '%si quan luc quan 1%') AND nam = 2023 ORDER BY ten_truong, ten_nganh LIMIT 100;"
  }
  // ... thêm 78 cặp nữa
]
```

Bước 2: Index vào Qdrant collection riêng (`few_shot_sql`):
```python
# script: python scripts/index_few_shot.py
for item in few_shot_data:
    embedding = embed(item["question"])  # BGE-M3
    qdrant.upsert(collection="few_shot_sql",
                  payload={"question": item["question"], "sql": item["sql"]},
                  vector=embedding)
```

Bước 3: Sửa `sql_agent.py` — thêm bước retrieve trước khi sinh SQL:
```python
async def _get_few_shot_examples(self, query: str, k: int = 3) -> str:
    query_vec = await self.embed(query)
    hits = await qdrant.search("few_shot_sql", query_vec, limit=k)
    examples = ""
    for hit in hits:
        examples += f"\nCâu hỏi: {hit.payload['question']}\nSQL: {hit.payload['sql']}\n---"
    return examples
```

**Lợi ích:** Tăng độ chính xác SQL ước tính từ 70% → 90%+
**Effort:** 3-4 ngày (chủ yếu viết 100 ví dụ chuẩn)

---

### 5.2 [QUAN TRỌNG] Structure-Aware Chunking cho RAG

**Vấn đề giải quyết:** Issue #3 — RAG chunking cắt đứt văn bản pháp lý

**Cách triển khai cụ thể:**

```python
# script: scripts/rechunk_legal_docs.py
import re

def chunk_legal_document(text: str, doc_name: str) -> list[dict]:
    chunks = []

    # Parse cấu trúc phân cấp
    chuong_pattern = r'(Chương\s+[IVX\d]+[^\n]*)'
    dieu_pattern = r'(Điều\s+\d+[^\n]*(?:\n(?!Điều|\nChương).*)*)'

    chapters = re.split(chuong_pattern, text)

    current_chuong = ""
    for part in chapters:
        if re.match(r'Chương\s+', part):
            current_chuong = part.strip()
            continue

        # Tách thành các Điều
        articles = re.split(r'\n(?=Điều\s+\d+)', part)
        for article in articles:
            if not article.strip():
                continue
            dieu_match = re.match(r'(Điều\s+\d+[^\n]*)', article)
            current_dieu = dieu_match.group(1) if dieu_match else ""

            # Tách thành Khoản
            khoan_parts = re.split(r'\n(?=\d+\.)', article)
            for khoan in khoan_parts:
                if len(khoan.strip()) < 50:
                    continue
                chunks.append({
                    "content": khoan.strip(),
                    "metadata": {
                        "doc": doc_name,
                        "chuong": current_chuong,
                        "dieu": current_dieu,
                        "parent_context": f"{current_chuong} > {current_dieu}",
                        "hierarchy_path": f"{doc_name}/{current_chuong}/{current_dieu}"
                    }
                })
    return chunks
```

**Kết quả:** Mỗi chunk khi đưa vào LLM luôn có `parent_context` → LLM biết "Khoản này thuộc Điều nào" → trả lời chính xác hơn.

**Effort:** 2-3 ngày

---

### 5.3 [QUAN TRỌNG] Query Decomposition cho Hybrid Queries

**Vấn đề giải quyết:** Issue #1 — câu hỏi phức tạp cần cả SQL lẫn RAG

**Cách triển khai cụ thể:**

Thêm node `decompose` vào LangGraph trước `route`:
```python
DECOMPOSE_PROMPT = """Phân tích câu hỏi: "{query}"

Câu hỏi này có YÊU CẦU CẢ HAI loại thông tin không?
- Số liệu (điểm chuẩn, chỉ tiêu) → SQL
- Quy định, thủ tục, điều kiện → RAG

Trả về JSON:
{
  "is_hybrid": true/false,
  "sql_question": "phần câu hỏi cần tra số liệu (hoặc null)",
  "rag_question": "phần câu hỏi cần tra quy định (hoặc null)"
}"""

# Trong _route_node: nếu is_hybrid=true → route về "both"
# _decide_next("both") → sql_agent → sau đó rag_agent → combine_node
```

**Lợi ích:** Giải quyết 10-15% câu hỏi hiện đang bị trả lời thiếu.
**Effort:** 1-2 ngày

---

### 5.4 Context-Aware Follow-up Resolution

**Vấn đề giải quyết:** Issue #5 — câu hỏi nối tiếp không hiểu ngữ cảnh

**Cách triển khai:**
```python
CONTEXT_RESOLVE_PROMPT = """Dựa vào lịch sử hội thoại, viết lại câu hỏi hiện tại thành câu hỏi đầy đủ, độc lập (không cần ngữ cảnh trước để hiểu).

Lịch sử:
{history}

Câu hỏi hiện tại: "{current_query}"

Câu hỏi đầy đủ (chỉ viết câu hỏi, không giải thích):"""

# Bước mới đầu tiên trong process():
resolved_query = await resolve_followup(query, conversation_history)
# Sau đó mới route resolved_query thay vì query gốc
```

**Effort:** 1 ngày

---

### 5.5 Mở rộng Dataset Đánh giá RAGAS (100+ mẫu)

**Cách tạo tự động:**
```bash
# Dùng LLM để generate câu hỏi từ tài liệu gốc
python scripts/generate_eval_dataset.py \
  --input data/legal_docs/ \
  --output data/evaluation/golden_dataset_v2.json \
  --num-questions 200 \
  --categories "diem_chuan,quy_che,thu_tuc,uu_tien,suc_khoe"
```

**Categories cần cover:**
- Điểm chuẩn (20 mẫu) — đơn trường, so sánh, theo năm
- Tiêu chuẩn sức khỏe (20 mẫu) — mắt, chiều cao, bệnh lý
- Điều kiện chính trị, lý lịch (15 mẫu)
- Quy trình hồ sơ, đăng ký (20 mẫu)
- Ưu tiên (KV, đối tượng, dân tộc) (15 mẫu)
- Ngành đào tạo, cơ hội (15 mẫu)
- Edge cases/câu hỏi khó (15 mẫu)

---

### 5.6 Confidence Score + Disclaimer

**Mô tả:** Khi RAG score thấp, tự động thêm disclaimer:
```python
if rag_score < 0.6:
    response += "\n\n⚠️ *Thông tin này có thể chưa đầy đủ. Vui lòng xác nhận lại với cơ quan tuyển sinh hoặc trực tiếp nhà trường.*"
```

**Effort:** 0.5 ngày

---

### 5.7 Admin Dashboard: Câu hỏi chưa trả lời được

**Mô tả:** Log câu hỏi nào có confidence thấp hoặc RAG trả về "không có thông tin" vào bảng `unanswered_questions`. Admin xem, bổ sung vào knowledge base.

```python
# Schema bảng mới
CREATE TABLE unanswered_questions (
    id SERIAL PRIMARY KEY,
    question TEXT,
    session_id TEXT,
    rag_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Effort:** 1 ngày backend + 1 ngày frontend

---

## 6. BENCHMARK CÁC THÀNH PHẦN

### 6.1 Benchmark hiện tại (ước tính từ quan sát)

| Thành phần | Latency P50 | Latency P95 | Throughput |
|-----------|-------------|-------------|-----------|
| Semantic Router | ~50ms | ~150ms | - |
| SQL Generation (vLLM) | ~800ms | ~2000ms | ~5-8 req/s |
| SQL Execution (PostgreSQL) | ~20ms | ~100ms | 500+ req/s |
| RAG Retrieval (Qdrant) | ~30ms | ~80ms | 200 req/s |
| RAG LLM Generation | ~1500ms | ~4000ms | ~3-5 req/s |
| BGE-M3 Embedding (local) | ~100ms | ~300ms | ~50 req/s |
| **End-to-end (chat, no cache)** | **~2-4s** | **~8-10s** | **~5 req/s** |
| **End-to-end (cache hit)** | **~100ms** | **~300ms** | **100+ req/s** |

### 6.2 Benchmark cần chạy để có số thực (Đề xuất)

```bash
# 1. Load test FastAPI
locust -f tests/locustfile.py --host http://localhost:8000 \
  --users 50 --spawn-rate 5 --run-time 5m

# 2. RAGAS evaluation (sau khi có 100 mẫu)
python scripts/run_evaluation.py --limit 100 \
  --metrics faithfulness,answer_relevancy,context_recall,context_precision

# 3. SQL accuracy test
python scripts/test_sql_accuracy.py \
  --test-file data/evaluation/sql_test_cases.json
  # Expected: câu hỏi → SQL đúng hay sai → accuracy %

# 4. vLLM throughput benchmark
python -m vllm.benchmark_throughput \
  --model Qwen/Qwen2.5-7B-Instruct \
  --num-prompts 200 --max-tokens 500
```

### 6.3 Target KPIs đề xuất

| Metric | Mục tiêu | Hiện tại (ước tính) |
|--------|---------|-------------------|
| Faithfulness (RAGAS) | > 0.85 | Chưa đo đủ |
| Answer Relevancy | > 0.80 | Chưa đo đủ |
| SQL Accuracy (test set) | > 90% | ~75-80% |
| End-to-end latency P95 | < 10s | ~8-10s |
| Cache hit rate | > 40% | Chưa đo |
| Uptime | 99.5% | Chưa đo |

---

## 7. ƯỚC TÍNH CHI PHÍ THUÊ SERVER (THAM KHẢO)

> **Lưu ý:** Giá tham khảo theo thị trường Q1/2026. Cần liên hệ trực tiếp Viettel IDC, FPT Cloud để có báo giá chính xác theo nhu cầu cụ thể.

### 7.1 Cấu hình server cần thiết

**Option A: Self-hosted GPU (khuyến nghị cho dài hạn)**
| Server | Specs | Chức năng |
|--------|-------|-----------|
| GPU Server (A100 80GB) | 32 CPU core, 128GB RAM, 2TB NVMe | vLLM (LLM inference) |
| App Server | 16 CPU core, 64GB RAM, 500GB SSD | FastAPI + Embedding + DB |

**Option B: Tách riêng DB**
| Server | Specs | Chức năng |
|--------|-------|-----------|
| GPU Server (A100 80GB) | 32 CPU, 128GB RAM | vLLM |
| App Server | 8 CPU, 32GB RAM | FastAPI + Embedding |
| DB Server | 8 CPU, 32GB RAM, 1TB NVMe | PostgreSQL + Qdrant + Redis |

### 7.2 Bảng giá ước tính (tham khảo thị trường Việt Nam)

#### Viettel IDC (Cloud GPU)
| Gói | Specs | Giá ước tính/tháng |
|----|-------|-------------------|
| GPU Standard | 1x NVIDIA A100 40GB, 32 vCPU, 128GB RAM | ~30-40 triệu VNĐ |
| GPU Premium | 1x NVIDIA A100 80GB, 32 vCPU, 256GB RAM | ~50-70 triệu VNĐ |
| App Server (kèm theo) | 8 vCPU, 32GB RAM, 500GB SSD | ~5-8 triệu VNĐ |
| **Tổng Option A (Viettel)** | | **~55-78 triệu/tháng** |

#### FPT Cloud (HPC AI)
| Gói | Specs | Giá ước tính/tháng |
|----|-------|-------------------|
| AI Compute A100 | 1x A100 40GB, 30 vCPU, 120GB RAM | ~28-38 triệu VNĐ |
| AI Compute A100 80GB | 1x A100 80GB, 30 vCPU, 256GB RAM | ~45-60 triệu VNĐ |
| App VM (kèm theo) | 8 vCPU, 32GB RAM, 500GB SSD | ~4-6 triệu VNĐ |
| **Tổng Option A (FPT)** | | **~49-66 triệu/tháng** |

#### VNPT SmartCloud
| Gói | Specs | Giá ước tính/tháng |
|----|-------|-------------------|
| GPU VM A10 (24GB) | 1x A10, 16 vCPU, 64GB RAM | ~15-20 triệu VNĐ |
| App VM | 8 vCPU, 32GB RAM | ~4-5 triệu VNĐ |
| **Tổng (VNPT, dùng A10)** | | **~19-25 triệu/tháng** |
| **Lưu ý** | A10 24GB có thể không đủ cho Qwen2.5-7B full precision | |

#### So sánh với Cloud AI API (không cần quản lý server)
| Provider | Model tương đương | Chi phí/tháng (ước tính 100k requests) |
|---------|-----------------|---------------------------------------|
| OpenAI GPT-4o-mini | Tốt nhất cho tiếng Việt | ~8-15 triệu VNĐ |
| Anthropic Claude 3.5 Haiku | Tốt | ~10-18 triệu VNĐ |
| Google Gemini 1.5 Flash | Khá | ~5-10 triệu VNĐ |

> **Phân tích:** Cloud AI API rẻ hơn đáng kể ở quy mô nhỏ (<100k req/tháng), nhưng phụ thuộc internet, latency cao hơn, và data phải gửi ra ngoài (vấn đề bảo mật với dữ liệu quân sự).

### 7.3 Khuyến nghị

| Giai đoạn | Khuyến nghị | Lý do |
|----------|------------|-------|
| **Demo/Testing** | Máy hiện có (16GB GPU + A100 nội bộ) | Không cần chi phí |
| **Pilot (50 users)** | FPT Cloud A100 40GB | Giá hợp lý, hỗ trợ tốt |
| **Production (200+ users)** | Viettel IDC A100 80GB + App VM | SLA tốt hơn, hỗ trợ 24/7 |
| **Scale lớn (1000+ users)** | Multi-GPU + load balancer | Thiết kế lại kiến trúc |

**Chi phí tối thiểu để chạy production (ước tính):**
- FPT Cloud A100 40GB: ~32 triệu/tháng
- App Server (FPT): ~5 triệu/tháng
- Băng thông + Storage: ~2 triệu/tháng
- **Tổng: ~39 triệu/tháng** (chưa gồm nhân sự vận hành)

---

## 8. LỘ TRÌNH VÀ KẾ HOẠCH (ĐỀ XUẤT)

### 8.1 Giai đoạn ngắn hạn (1-2 tháng) — Tập trung cải thiện chất lượng

| Tuần | Việc cần làm | Người phụ trách | Priority |
|------|-------------|----------------|---------|
| 1 | Mở rộng RAGAS dataset lên 100 mẫu, chạy baseline benchmark | Dev | 🔴 Cao |
| 1 | Implement Dynamic Few-Shot SQL (80 cặp mẫu) | Dev | 🔴 Cao |
| 2 | Structure-Aware Chunking, re-index Qdrant | Dev | 🔴 Cao |
| 2 | Query decomposition cho hybrid queries | Dev | 🟡 Trung |
| 3 | Context-aware follow-up resolution | Dev | 🟡 Trung |
| 3 | Confidence score + disclaimer | Dev | 🟡 Trung |
| 4 | Load test (Locust 50 users) | Dev | 🔴 Cao |
| 4 | Admin dashboard: unanswered questions | Dev | 🟡 Trung |
| 5-6 | Bổ sung knowledge base (quy chế 2025, chế độ đãi ngộ) | Chuyên gia nội dung | 🔴 Cao |
| 7-8 | User acceptance testing với thí sinh thực | Nhóm test | 🔴 Cao |

### 8.2 Giai đoạn trung hạn (3-6 tháng) — Chuẩn bị production

- Liên hệ FPT Cloud / Viettel IDC lấy báo giá chính thức
- Thiết lập CI/CD pipeline đầy đủ
- Implement HITL (Human-in-the-Loop) review workflow
- Monitoring: Grafana + Prometheus cho toàn hệ thống
- Penetration test bảo mật

### 8.3 Các câu hỏi cần trả lời trước khi triển khai

1. **Số lượng người dùng kỳ vọng?** (ảnh hưởng quyết định server)
2. **Yêu cầu bảo mật dữ liệu?** (có thể dùng cloud API không, hay phải on-premise?)
3. **Budget hàng tháng cho server?** (quyết định chọn Viettel/FPT/VNPT hay dùng máy nội bộ)
4. **Timeline ra mắt chính thức?** (ảnh hưởng sprint planning)
5. **Ai phụ trách vận hành sau khi launch?** (cần 1 DevOps hoặc thỏa thuận với nhà cung cấp)

---

## PHỤ LỤC A: Stack công nghệ tóm tắt

| Layer | Tech | Version |
|-------|------|---------|
| LLM | Qwen2.5-7B-Instruct qua vLLM | - |
| Embedding | BAAI/BGE-M3 (local) | SentenceTransformers |
| Backend | FastAPI + LangGraph | 0.115 + 0.2 |
| Orchestration | LangGraph (Stateless) | 0.2+ |
| Vector DB | Qdrant | 1.12+ |
| Relational DB | PostgreSQL 16 | asyncpg |
| Cache | Redis | 5.0+ |
| Frontend | React + TypeScript (Vite) | - |
| Auth | JWT + slowapi | - |
| Deploy | Docker Compose + Nginx | - |

## PHỤ LỤC B: Tóm tắt Issues và mức độ ưu tiên

| # | Issue | Mức độ | Effort |
|---|-------|--------|--------|
| 1 | Hybrid query routing | 🔴 Cao | 2 ngày |
| 2 | SQL few-shot thiếu | 🔴 Cao | 4 ngày |
| 3 | RAG chunking pháp lý | 🔴 Cao | 3 ngày |
| 4 | Không có self-verification | 🟡 Trung | 3 ngày |
| 5 | Follow-up context | 🟡 Trung | 1 ngày |
| 6 | Dataset RAGAS nhỏ | 🔴 Cao | 5 ngày |
| 7 | Thiếu safety layer | 🟡 Trung | 2 ngày |
| 8 | Không có HITL | 🟡 Trung | 5 ngày |
| 9 | Prompt injection | 🟡 Trung | 2 ngày |
| 10 | Thiếu intents/nội dung | 🔴 Cao | 10+ ngày (nội dung) |
| 11 | Dữ liệu điểm 2 năm | 🔴 Cao | Thu thập dữ liệu |

---

*Tài liệu này được tạo tự động từ phân tích source code và kiến trúc hệ thống. Cần xác nhận lại các con số với dữ liệu đo lường thực tế.*
