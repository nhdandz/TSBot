#!/bin/bash
# =============================================================================
# Khởi động vLLM trên máy A100
# Chạy script này trên MÁY A100 (không phải máy application)
#
# Yêu cầu: Docker + NVIDIA Container Toolkit
# =============================================================================

set -e

# ── Cấu hình ─────────────────────────────────────────────────────────────────
MAIN_MODEL="${VLLM_MAIN_MODEL:-Qwen/Qwen2.5-7B-Instruct}"
GRADER_MODEL="${VLLM_GRADER_MODEL:-Qwen/Qwen2.5-1.5B-Instruct}"
PORT="${VLLM_PORT:-8001}"
GPU_MEMORY_UTIL="${GPU_MEMORY_UTIL:-0.90}"    # A100 80GB: dùng 90% (~72GB), model 14GB → ~58GB KV cache
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-128}"           # Số request xử lý song song tối đa (~50-100 concurrent users)
TENSOR_PARALLEL="${TENSOR_PARALLEL:-1}"        # 1 GPU, tăng nếu có multi-GPU

echo "Starting vLLM with model: $MAIN_MODEL on port $PORT"

# ── Chạy vLLM container ──────────────────────────────────────────────────────
# vLLM serve 1 model chính. Nếu cần cả grader_model riêng,
# chạy thêm 1 container khác trên port 8002.
docker run -d \
  --name tsbot-vllm \
  --restart unless-stopped \
  --gpus all \
  -p "${PORT}:8000" \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e HUGGING_FACE_HUB_TOKEN="${HF_TOKEN:-}" \
  vllm/vllm-openai:latest \
    --model "$MAIN_MODEL" \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
    --max-model-len "$MAX_MODEL_LEN" \
    --max-num-seqs "$MAX_NUM_SEQS" \
    --tensor-parallel-size "$TENSOR_PARALLEL" \
    --enable-chunked-prefill \
    --trust-remote-code \
    --served-model-name "$MAIN_MODEL" \
    --dtype float16

echo ""
echo "vLLM đang khởi động tại http://$(hostname -I | awk '{print $1}'):${PORT}"
echo "Kiểm tra: curl http://localhost:${PORT}/health"
echo "Models:   curl http://localhost:${PORT}/v1/models"
echo ""
echo "Logs: docker logs -f tsbot-vllm"
