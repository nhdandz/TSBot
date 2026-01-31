"""Admin API endpoints for data management."""

import io
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.database.models import DiemChuan, KhoiThi, Nganh, Truong, User
from src.database.postgres import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/login")


# Models
class Token(BaseModel):
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    username: str
    password: str


class DiemChuanCreate(BaseModel):
    nganh_id: int
    khoi_thi_id: int
    nam: int = Field(..., ge=2000, le=2100)
    diem_chuan: float = Field(..., ge=0, le=30)
    chi_tieu: Optional[int] = Field(None, ge=0)
    gioi_tinh: Optional[str] = Field(None, pattern="^(nam|nu)$")
    khu_vuc: Optional[str] = None
    doi_tuong: Optional[str] = None
    ghi_chu: Optional[str] = None


class DiemChuanUpdate(BaseModel):
    diem_chuan: Optional[float] = Field(None, ge=0, le=30)
    chi_tieu: Optional[int] = Field(None, ge=0)
    gioi_tinh: Optional[str] = Field(None, pattern="^(nam|nu)$")
    khu_vuc: Optional[str] = None
    doi_tuong: Optional[str] = None
    ghi_chu: Optional[str] = None


class TruongCreate(BaseModel):
    ma_truong: str = Field(..., max_length=20)
    ten_truong: str = Field(..., max_length=255)
    loai_truong: str = Field(..., pattern="^(quan_doi|cong_an|khac)$")
    dia_chi: Optional[str] = None
    website: Optional[str] = None
    mo_ta: Optional[str] = None


class NganhCreate(BaseModel):
    truong_id: int
    ma_nganh: str = Field(..., max_length=20)
    ten_nganh: str = Field(..., max_length=255)
    mo_ta: Optional[str] = None


class ImportResult(BaseModel):
    success: bool
    total_rows: int
    imported: int
    errors: list[str]


# Authentication
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )

    return user


# Login endpoint
@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_db_session),
) -> Token:
    """Login and get access token."""
    result = await session.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await session.commit()

    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


# Truong (School) endpoints
@router.get("/truong")
async def list_truong(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List all schools."""
    result = await session.execute(
        select(Truong).where(Truong.active == True).order_by(Truong.ten_truong)
    )
    truong_list = result.scalars().all()

    return [
        {
            "id": t.id,
            "school_id": t.ma_truong,
            "school_name": t.ten_truong,
            "alias": t.loai_truong,
            "location": t.dia_chi,
            "website": t.website,
        }
        for t in truong_list
    ]


@router.post("/truong")
async def create_truong(
    data: TruongCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a new school."""
    truong = Truong(**data.model_dump())
    session.add(truong)
    await session.commit()
    await session.refresh(truong)

    return {"id": truong.id, "message": "Thêm trường thành công"}


# Nganh (Program) endpoints
@router.get("/nganh")
async def list_nganh(
    truong_id: Optional[int] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List programs, optionally filtered by school."""
    query = select(Nganh).where(Nganh.active == True)
    if truong_id:
        query = query.where(Nganh.truong_id == truong_id)
    query = query.order_by(Nganh.ten_nganh)

    result = await session.execute(query)
    nganh_list = result.scalars().all()

    # Get school names
    truong_result = await session.execute(select(Truong))
    truong_map = {t.id: t.ten_truong for t in truong_result.scalars().all()}

    return [
        {
            "id": n.id,
            "truong_id": n.truong_id,
            "school_name": truong_map.get(n.truong_id, ""),
            "major_code": n.ma_nganh,
            "major_name": n.ten_nganh,
            "description": n.mo_ta,
        }
        for n in nganh_list
    ]


@router.post("/nganh")
async def create_nganh(
    data: NganhCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a new program."""
    nganh = Nganh(**data.model_dump())
    session.add(nganh)
    await session.commit()
    await session.refresh(nganh)

    return {"id": nganh.id, "message": "Thêm ngành thành công"}


# Diem Chuan (Admission Score) endpoints
@router.get("/diem-chuan")
async def list_diem_chuan(
    nam: Optional[int] = None,
    truong_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List admission scores with filtering."""
    query = (
        select(DiemChuan, Nganh, Truong, KhoiThi)
        .join(Nganh, DiemChuan.nganh_id == Nganh.id)
        .join(Truong, Nganh.truong_id == Truong.id)
        .join(KhoiThi, DiemChuan.khoi_thi_id == KhoiThi.id)
    )

    if nam:
        query = query.where(DiemChuan.nam == nam)
    if truong_id:
        query = query.where(Truong.id == truong_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)

    # Get paginated results
    query = query.order_by(Truong.ten_truong, Nganh.ten_nganh, DiemChuan.nam.desc())
    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    rows = result.all()

    items = [
        {
            "id": dc.id,
            "truong": {
                "id": truong.id,
                "ma_truong": truong.ma_truong,
                "ten_truong": truong.ten_truong,
            },
            "nganh": {
                "id": nganh.id,
                "ma_nganh": nganh.ma_nganh,
                "ten_nganh": nganh.ten_nganh,
            },
            "khoi_thi": {
                "id": kt.id,
                "ma_khoi": kt.ma_khoi,
                "ten_khoi": kt.ten_khoi,
            },
            "nam": dc.nam,
            "diem_chuan": dc.diem_chuan,
            "chi_tieu": dc.chi_tieu,
            "gioi_tinh": dc.gioi_tinh,
            "khu_vuc": dc.khu_vuc,
            "ghi_chu": dc.ghi_chu,
        }
        for dc, nganh, truong, kt in rows
    ]

    return {
        "total": total,
        "items": items,
        "limit": limit,
        "offset": offset,
    }


@router.post("/diem-chuan")
async def create_diem_chuan(
    data: DiemChuanCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a new admission score entry."""
    diem_chuan = DiemChuan(**data.model_dump(), created_by=current_user.id)
    session.add(diem_chuan)
    await session.commit()
    await session.refresh(diem_chuan)

    logger.info(f"Created diem_chuan {diem_chuan.id} by user {current_user.username}")

    return {"id": diem_chuan.id, "message": "Thêm điểm chuẩn thành công"}


@router.put("/diem-chuan/{diem_chuan_id}")
async def update_diem_chuan(
    diem_chuan_id: int,
    data: DiemChuanUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update an admission score entry."""
    result = await session.execute(
        select(DiemChuan).where(DiemChuan.id == diem_chuan_id)
    )
    diem_chuan = result.scalar_one_or_none()

    if not diem_chuan:
        raise HTTPException(status_code=404, detail="Không tìm thấy điểm chuẩn")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(diem_chuan, field, value)

    await session.commit()

    logger.info(f"Updated diem_chuan {diem_chuan_id} by user {current_user.username}")

    return {"message": "Cập nhật thành công"}


@router.delete("/diem-chuan/{diem_chuan_id}")
async def delete_diem_chuan(
    diem_chuan_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete an admission score entry."""
    result = await session.execute(
        select(DiemChuan).where(DiemChuan.id == diem_chuan_id)
    )
    diem_chuan = result.scalar_one_or_none()

    if not diem_chuan:
        raise HTTPException(status_code=404, detail="Không tìm thấy điểm chuẩn")

    await session.delete(diem_chuan)
    await session.commit()

    logger.info(f"Deleted diem_chuan {diem_chuan_id} by user {current_user.username}")

    return {"message": "Xóa thành công"}


@router.post("/diem-chuan/import", response_model=ImportResult)
async def import_diem_chuan(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ImportResult:
    """Import admission scores from Excel/CSV file.

    Expected columns:
    - ma_truong: School code
    - ma_nganh: Program code
    - ma_khoi: Exam group code (A00, B00, etc.)
    - nam: Year
    - diem_chuan: Admission score
    - chi_tieu (optional): Quota
    - gioi_tinh (optional): Gender (nam/nu)
    - khu_vuc (optional): Region
    - ghi_chu (optional): Notes
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Vui lòng chọn file")

    # Read file
    try:
        content = await file.read()

        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file CSV hoặc Excel")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi đọc file: {str(e)}")

    # Validate required columns
    required_cols = ["ma_truong", "ma_nganh", "ma_khoi", "nam", "diem_chuan"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Thiếu cột: {', '.join(missing)}",
        )

    # Process rows
    errors = []
    imported = 0

    # Pre-fetch lookups
    truong_result = await session.execute(select(Truong))
    truong_map = {t.ma_truong: t.id for t in truong_result.scalars().all()}

    nganh_result = await session.execute(select(Nganh))
    nganh_map = {(n.truong_id, n.ma_nganh): n.id for n in nganh_result.scalars().all()}

    khoi_result = await session.execute(select(KhoiThi))
    khoi_map = {k.ma_khoi: k.id for k in khoi_result.scalars().all()}

    for idx, row in df.iterrows():
        try:
            # Lookup IDs
            truong_id = truong_map.get(row["ma_truong"])
            if not truong_id:
                errors.append(f"Dòng {idx + 2}: Không tìm thấy trường {row['ma_truong']}")
                continue

            nganh_id = nganh_map.get((truong_id, row["ma_nganh"]))
            if not nganh_id:
                errors.append(f"Dòng {idx + 2}: Không tìm thấy ngành {row['ma_nganh']}")
                continue

            khoi_id = khoi_map.get(row["ma_khoi"])
            if not khoi_id:
                errors.append(f"Dòng {idx + 2}: Không tìm thấy khối {row['ma_khoi']}")
                continue

            # Create entry
            diem_chuan = DiemChuan(
                nganh_id=nganh_id,
                khoi_thi_id=khoi_id,
                nam=int(row["nam"]),
                diem_chuan=float(row["diem_chuan"]),
                chi_tieu=int(row["chi_tieu"]) if pd.notna(row.get("chi_tieu")) else None,
                gioi_tinh=row.get("gioi_tinh") if pd.notna(row.get("gioi_tinh")) else None,
                khu_vuc=row.get("khu_vuc") if pd.notna(row.get("khu_vuc")) else None,
                ghi_chu=row.get("ghi_chu") if pd.notna(row.get("ghi_chu")) else None,
                created_by=current_user.id,
            )
            session.add(diem_chuan)
            imported += 1

        except Exception as e:
            errors.append(f"Dòng {idx + 2}: {str(e)}")

    await session.commit()

    logger.info(
        f"Import completed by {current_user.username}: "
        f"{imported}/{len(df)} rows imported"
    )

    return ImportResult(
        success=len(errors) == 0,
        total_rows=len(df),
        imported=imported,
        errors=errors[:20],  # Limit errors returned
    )


# Document reindexing endpoint
@router.post("/documents/reindex")
async def reindex_documents(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Trigger re-indexing of legal documents.

    This will re-process all documents in the documents directory
    and update the vector database.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có thể thực hiện",
        )

    # TODO: Implement background task for reindexing
    logger.info(f"Document reindex triggered by {current_user.username}")

    return {
        "message": "Đã bắt đầu quá trình index lại văn bản",
        "status": "processing",
    }


# Statistics endpoint
@router.get("/stats")
async def get_stats(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get system statistics."""
    truong_count = await session.scalar(select(func.count(Truong.id)))
    nganh_count = await session.scalar(select(func.count(Nganh.id)))
    diem_chuan_count = await session.scalar(select(func.count(DiemChuan.id)))

    # Latest year
    latest_year = await session.scalar(select(func.max(DiemChuan.nam)))

    return {
        "total_schools": truong_count or 0,
        "total_majors": nganh_count or 0,
        "total_scores": diem_chuan_count or 0,
        "total_chats": 0,
        "recent_chats": 0,
        "latest_year": latest_year,
    }
