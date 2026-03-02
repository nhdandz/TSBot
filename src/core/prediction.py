"""Linear regression prediction for admission scores."""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class PredictionResult:
    """Result of a score prediction."""

    nam_toi: int
    diem_du_doan: float
    confidence: float  # 0.0 – 1.0
    disclaimer: Optional[str]
    slope: float
    intercept: float
    r_squared: float
    n_points: int


def predict_next_year(data_points: list[dict]) -> Optional[PredictionResult]:
    """Predict the admission score for next year using linear regression.

    Args:
        data_points: List of dicts with keys ``nam`` (int) and ``diem_chuan`` (float).
                     Must have at least 2 distinct year values.

    Returns:
        PredictionResult or None if there are not enough data points.
    """
    if len(data_points) < 2:
        return None

    years = np.array([p["nam"] for p in data_points], dtype=float)
    scores = np.array([p["diem_chuan"] for p in data_points], dtype=float)

    # Fit degree-1 polynomial (linear regression)
    coeffs = np.polyfit(years, scores, deg=1)
    slope, intercept = float(coeffs[0]), float(coeffs[1])

    # Predicted values for R²
    predicted = np.polyval(coeffs, years)
    ss_res = float(np.sum((scores - predicted) ** 2))
    ss_tot = float(np.sum((scores - scores.mean()) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    next_year = int(years.max()) + 1
    diem_du_doan = round(float(np.polyval(coeffs, next_year)), 2)

    # Confidence: with only 2 points, R² is always 1 but CI is wide
    n = len(data_points)
    if n == 2:
        confidence = 0.40
        disclaimer = (
            "Dự đoán dựa trên 2 năm dữ liệu (2023–2024), mang tính tham khảo. "
            "Độ chính xác sẽ tăng khi có thêm dữ liệu."
        )
    elif n == 3:
        confidence = min(0.65, r_squared)
        disclaimer = "Dự đoán dựa trên 3 năm dữ liệu, mang tính tham khảo."
    else:
        confidence = min(0.90, r_squared)
        disclaimer = None

    # Clamp to reasonable score range
    diem_du_doan = max(10.0, min(30.0, diem_du_doan))

    return PredictionResult(
        nam_toi=next_year,
        diem_du_doan=diem_du_doan,
        confidence=round(confidence, 2),
        disclaimer=disclaimer,
        slope=round(slope, 4),
        intercept=round(intercept, 4),
        r_squared=round(r_squared, 4),
        n_points=n,
    )
