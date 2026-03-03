"""Analytics API endpoints for trend analysis and score prediction."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.core.prediction import predict_next_year
from src.database.postgres import get_postgres_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# GET /trend
# ---------------------------------------------------------------------------
@router.get("/trend")
async def get_trend(
    truong: Optional[str] = Query(None, description="Tên trường (không dấu, tìm ILIKE)"),
    nganh: Optional[str] = Query(None, description="Tên ngành (không dấu, tìm ILIKE)"),
    ma_khoi: Optional[str] = Query(None, description="Mã khối thi, ví dụ A00"),
    gioi_tinh: Optional[str] = Query(None, description="nam hoặc nu"),
    khu_vuc: Optional[str] = Query(None, description="mien_bac hoặc mien_nam"),
) -> dict:
    """Xu hướng điểm chuẩn qua các năm kèm dự đoán năm tới."""
    if not truong and not nganh:
        raise HTTPException(
            status_code=400, detail="Cần cung cấp ít nhất truong hoặc nganh"
        )

    db = get_postgres_db()
    conditions = ["1=1"]
    params: dict = {}

    if truong:
        conditions.append("ten_khong_dau ILIKE :truong")
        params["truong"] = f"%{truong}%"
    if nganh:
        conditions.append("ten_nganh_khong_dau ILIKE :nganh")
        params["nganh"] = f"%{nganh}%"
    if ma_khoi:
        conditions.append("ma_khoi = :ma_khoi")
        params["ma_khoi"] = ma_khoi
    if gioi_tinh:
        conditions.append("gioi_tinh = :gioi_tinh")
        params["gioi_tinh"] = gioi_tinh
    if khu_vuc:
        conditions.append("khu_vuc = :khu_vuc")
        params["khu_vuc"] = khu_vuc

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT nam, AVG(diem_chuan) AS diem_chuan
        FROM view_tra_cuu_diem
        WHERE {where_clause}
        GROUP BY nam
        ORDER BY nam ASC
        LIMIT 20
    """

    try:
        rows = await db.fetch_all(sql, params)
    except Exception as e:
        logger.error(f"Trend query error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi truy vấn cơ sở dữ liệu")

    if not rows:
        return {"data_points": [], "prediction": None, "regression": None}

    data_points = [
        {"nam": int(r["nam"]), "diem_chuan": round(float(r["diem_chuan"]), 2)}
        for r in rows
    ]

    prediction_obj = predict_next_year(data_points)
    prediction = None
    regression = None

    if prediction_obj:
        prediction = {
            "nam_toi": prediction_obj.nam_toi,
            "diem_du_doan": prediction_obj.diem_du_doan,
            "confidence": prediction_obj.confidence,
            "disclaimer": prediction_obj.disclaimer,
        }
        regression = {
            "slope": prediction_obj.slope,
            "intercept": prediction_obj.intercept,
            "r_squared": prediction_obj.r_squared,
            "n_points": prediction_obj.n_points,
        }

    return {"data_points": data_points, "prediction": prediction, "regression": regression}


# ---------------------------------------------------------------------------
# GET /compare
# ---------------------------------------------------------------------------
@router.get("/compare")
async def compare_schools(
    nam: Optional[int] = Query(None, description="Năm tuyển sinh"),
    ma_khoi: Optional[str] = Query(None, description="Mã khối thi"),
    gioi_tinh: Optional[str] = Query(None, description="nam hoặc nu"),
    khu_vuc: Optional[str] = Query(None, description="mien_bac hoặc mien_nam"),
    limit: int = Query(20, ge=1, le=50),
) -> list[dict]:
    """So sánh điểm chuẩn trung bình giữa các trường."""
    db = get_postgres_db()
    conditions = ["1=1"]
    params: dict = {}

    if nam is not None:
        conditions.append("nam = :nam")
        params["nam"] = nam
    if ma_khoi:
        conditions.append("ma_khoi = :ma_khoi")
        params["ma_khoi"] = ma_khoi
    if gioi_tinh:
        conditions.append("gioi_tinh = :gioi_tinh")
        params["gioi_tinh"] = gioi_tinh
    if khu_vuc:
        conditions.append("khu_vuc = :khu_vuc")
        params["khu_vuc"] = khu_vuc

    where_clause = " AND ".join(conditions)
    # limit đã được FastAPI validate là int trong [1,50] → an toàn dùng trực tiếp
    sql = f"""
        SELECT
            ten_truong,
            ROUND(AVG(diem_chuan)::numeric, 2) AS diem_trung_binh,
            MAX(diem_chuan) AS diem_cao_nhat,
            MIN(diem_chuan) AS diem_thap_nhat,
            COUNT(*) AS so_nganh
        FROM view_tra_cuu_diem
        WHERE {where_clause}
        GROUP BY ten_truong
        ORDER BY diem_trung_binh DESC
        LIMIT {limit}
    """

    try:
        rows = await db.fetch_all(sql, params)
    except Exception as e:
        logger.error(f"Compare query error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi truy vấn cơ sở dữ liệu")

    return [
        {
            "ten_truong": r["ten_truong"],
            "diem_trung_binh": float(r["diem_trung_binh"]),
            "diem_cao_nhat": float(r["diem_cao_nhat"]),
            "diem_thap_nhat": float(r["diem_thap_nhat"]),
            "so_nganh": int(r["so_nganh"]),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /distribution
# ---------------------------------------------------------------------------
@router.get("/distribution")
async def get_distribution(
    nam: Optional[int] = Query(None, description="Năm tuyển sinh"),
    ma_khoi: Optional[str] = Query(None, description="Mã khối thi"),
) -> dict:
    """Phân phối điểm chuẩn (dạng histogram)."""
    db = get_postgres_db()
    conditions = ["1=1"]
    params: dict = {}

    if nam is not None:
        conditions.append("nam = :nam")
        params["nam"] = nam
    if ma_khoi:
        conditions.append("ma_khoi = :ma_khoi")
        params["ma_khoi"] = ma_khoi

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT diem_chuan FROM view_tra_cuu_diem
        WHERE {where_clause} AND diem_chuan IS NOT NULL
        LIMIT 2000
    """

    try:
        rows = await db.fetch_all(sql, params)
    except Exception as e:
        logger.error(f"Distribution query error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi truy vấn cơ sở dữ liệu")

    if not rows:
        return {"bins": [], "counts": []}

    scores = [float(r["diem_chuan"]) for r in rows]

    bin_edges = list(range(10, 32, 2))
    bins = [f"{b}–{b + 2}" for b in bin_edges[:-1]]
    counts = [0] * len(bins)

    for s in scores:
        for i, edge in enumerate(bin_edges[:-1]):
            if edge <= s < bin_edges[i + 1]:
                counts[i] += 1
                break
        else:
            if s == bin_edges[-1]:
                counts[-1] += 1

    return {"bins": bins, "counts": counts}


# ---------------------------------------------------------------------------
# GET /schools-summary
# ---------------------------------------------------------------------------
@router.get("/schools-summary")
async def get_schools_summary() -> dict:
    """Tổng quan tất cả trường: top điểm, khoảng điểm, năm có dữ liệu."""
    db = get_postgres_db()

    sql = """
        SELECT
            ten_truong,
            MIN(nam) AS nam_dau,
            MAX(nam) AS nam_cuoi,
            COUNT(DISTINCT nam) AS so_nam,
            ROUND(AVG(diem_chuan)::numeric, 2) AS diem_tb,
            MAX(diem_chuan) AS diem_max,
            MIN(diem_chuan) AS diem_min
        FROM view_tra_cuu_diem
        GROUP BY ten_truong
        ORDER BY diem_tb DESC
    """

    try:
        rows = await db.fetch_all(sql)
    except Exception as e:
        logger.error(f"Schools summary query error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi truy vấn cơ sở dữ liệu")

    schools = [
        {
            "ten_truong": r["ten_truong"],
            "nam_dau": int(r["nam_dau"]),
            "nam_cuoi": int(r["nam_cuoi"]),
            "so_nam": int(r["so_nam"]),
            "diem_tb": float(r["diem_tb"]),
            "diem_max": float(r["diem_max"]),
            "diem_min": float(r["diem_min"]),
        }
        for r in rows
    ]

    try:
        nam_rows = await db.fetch_all(
            "SELECT DISTINCT nam FROM view_tra_cuu_diem ORDER BY nam"
        )
        years = [int(r["nam"]) for r in nam_rows]
    except Exception:
        years = []

    return {
        "schools": schools,
        "years_available": years,
        "total_schools": len(schools),
    }
