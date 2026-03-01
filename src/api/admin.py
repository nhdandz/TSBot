"""Admin API endpoints for data management."""

import io
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.database.models import DiemChuan, KhoiThi, Nganh, Truong, User
from src.database.postgres import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()

# Security
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
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
    khu_vuc: Optional[str] = Field(None, pattern="^(mien_bac|mien_nam)$")
    doi_tuong: Optional[str] = None
    ghi_chu: Optional[str] = None


class DiemChuanUpdate(BaseModel):
    diem_chuan: Optional[float] = Field(None, ge=0, le=30)
    chi_tieu: Optional[int] = Field(None, ge=0)
    gioi_tinh: Optional[str] = Field(None, pattern="^(nam|nu)$")
    khu_vuc: Optional[str] = Field(None, pattern="^(mien_bac|mien_nam)$")
    doi_tuong: Optional[str] = None
    ghi_chu: Optional[str] = None


class TruongCreate(BaseModel):
    school_id: str = Field(..., max_length=20)
    school_name: str = Field(..., max_length=255)
    alias: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class NganhCreate(BaseModel):
    truong_id: int
    major_code: str = Field(..., max_length=20)
    major_name: str = Field(..., max_length=255)
    description: Optional[str] = None


class NganhUpdate(BaseModel):
    truong_id: Optional[int] = None
    major_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


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

    if not user or not verify_password(credentials.password, user.hashed_password):
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
            "description": t.mo_ta,
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
    truong = Truong(
        ma_truong=data.school_id,
        ten_truong=data.school_name,
        loai_truong=data.alias or "quan_doi",
        dia_chi=data.location,
        website=data.website,
        mo_ta=data.description,
    )
    session.add(truong)
    await session.commit()
    await session.refresh(truong)

    return {"id": truong.id, "message": "Thêm trường thành công"}


@router.put("/truong/{truong_id}")
async def update_truong(
    truong_id: str,
    data: TruongCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update a school."""
    result = await session.execute(
        select(Truong).where(Truong.ma_truong == truong_id)
    )
    truong = result.scalar_one_or_none()

    if not truong:
        raise HTTPException(status_code=404, detail="Không tìm thấy trường")

    truong.ten_truong = data.school_name
    truong.loai_truong = data.alias or truong.loai_truong
    truong.dia_chi = data.location
    truong.website = data.website
    truong.mo_ta = data.description

    await session.commit()

    return {"message": "Cập nhật trường thành công"}


@router.delete("/truong/{truong_id}")
async def delete_truong(
    truong_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete (deactivate) a school."""
    result = await session.execute(
        select(Truong).where(Truong.ma_truong == truong_id)
    )
    truong = result.scalar_one_or_none()

    if not truong:
        raise HTTPException(status_code=404, detail="Không tìm thấy trường")

    truong.active = False
    await session.commit()

    return {"message": "Xóa trường thành công"}


# KhoiThi (Exam blocks) endpoints
@router.get("/khoi-thi")
async def list_khoi_thi(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """List all exam blocks."""
    result = await session.execute(
        select(KhoiThi).where(KhoiThi.active == True).order_by(KhoiThi.ma_khoi)
    )
    khoi_list = result.scalars().all()

    return [
        {
            "id": k.id,
            "ma_khoi": k.ma_khoi,
            "ten_khoi": k.ten_khoi,
            "mon_hoc": k.mon_hoc,
        }
        for k in khoi_list
    ]


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
    nganh = Nganh(
        truong_id=data.truong_id,
        ma_nganh=data.major_code,
        ten_nganh=data.major_name,
        mo_ta=data.description,
    )
    session.add(nganh)
    await session.commit()
    await session.refresh(nganh)

    return {"id": nganh.id, "message": "Thêm ngành thành công"}


@router.put("/nganh/{major_code}")
async def update_nganh(
    major_code: str,
    data: NganhUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update a program by its major code."""
    result = await session.execute(
        select(Nganh).where(Nganh.ma_nganh == major_code)
    )
    nganh = result.scalar_one_or_none()

    if not nganh:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngành")

    update_data = data.model_dump(exclude_unset=True)
    if "truong_id" in update_data:
        nganh.truong_id = update_data["truong_id"]
    if "major_name" in update_data:
        nganh.ten_nganh = update_data["major_name"]
    if "description" in update_data:
        nganh.mo_ta = update_data["description"]

    await session.commit()

    return {"message": "Cập nhật ngành thành công"}


@router.delete("/nganh/{major_code}")
async def delete_nganh(
    major_code: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Deactivate a program by its major code."""
    result = await session.execute(
        select(Nganh).where(Nganh.ma_nganh == major_code)
    )
    nganh = result.scalar_one_or_none()

    if not nganh:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngành")

    nganh.active = False
    await session.commit()

    return {"message": "Xóa ngành thành công"}


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


# Document Management Endpoints
@router.post("/documents/load-json")
async def load_from_json(
    json_file_path: str = settings.chunks_json_path,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Load chunks from JSON file into vector store and Qdrant.

    This builds the in-memory chunk_map for hierarchy navigation
    and upserts embeddings to Qdrant for dense search.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có thể load dữ liệu",
        )

    try:
        from src.agents.components.vector_store import async_load_from_json
        stats = await async_load_from_json(json_file_path)
        logger.info(f"Loaded chunks from JSON: {stats}")
        return {
            "success": True,
            "message": f"Đã load {stats['total_chunks']} chunks từ {json_file_path}",
            **stats,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error loading JSON: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Upload and index a legal document.

    Accepts PDF, DOCX, or TXT files. The document will be:
    1. Text extracted
    2. Chunked using LegalDocumentChunker
    3. Embedded
    4. Indexed into Qdrant
    """
    logger.info(f"=== UPLOAD DOCUMENT START ===")
    logger.info(f"User: {current_user.username} (is_superuser: {current_user.is_superuser})")
    logger.info(f"File: {file.filename if file.filename else 'NO FILENAME'}")
    logger.info(f"Content-Type: {file.content_type if hasattr(file, 'content_type') else 'UNKNOWN'}")

    if not current_user.is_superuser:
        logger.warning(f"Non-superuser {current_user.username} attempted to upload document")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có thể upload tài liệu",
        )

    if not file.filename:
        logger.error("No filename provided in upload request")
        raise HTTPException(status_code=400, detail="Vui lòng chọn file")

    logger.info(f"Upload request from {current_user.username}: {file.filename}")
    
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".txt"}
    
    # Safe extension extraction
    if "." not in file.filename:
        raise HTTPException(status_code=400, detail="File không có phần mở rộng")
    
    file_ext = file.filename[file.filename.rfind("."):].lower()
    logger.debug(f"Detected file extension: {file_ext}")
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Chỉ hỗ trợ file PDF, DOCX, TXT. File của bạn: {file_ext}"
        )


    try:
        # Read file content
        logger.info(f"Reading file content...")
        content_bytes = await file.read()
        logger.info(f"Read {len(content_bytes)} bytes from file")

        if len(content_bytes) == 0:
            logger.error("File is empty (0 bytes)")
            raise HTTPException(status_code=400, detail="File rỗng")

        # Extract text based on file type
        logger.info(f"Extracting text from {file_ext} file...")
        if file_ext == ".txt":
            text = content_bytes.decode("utf-8")
        elif file_ext == ".docx":
            from docx import Document
            doc = Document(io.BytesIO(content_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif file_ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            text_parts = [page.extract_text() for page in reader.pages]
            text = "\n".join(text_parts)
        else:
            logger.error(f"Unsupported file extension: {file_ext}")
            raise HTTPException(status_code=400, detail="Định dạng file không hỗ trợ")

        logger.info(f"Extracted {len(text)} characters of text")

        if not text.strip():
            logger.error("Extracted text is empty")
            raise HTTPException(status_code=400, detail="File rỗng hoặc không đọc được")
        
        # Import services
        from src.core.embeddings import get_embedding_service
        from src.database.qdrant import get_qdrant_db
        from src.utils.chunking import LegalDocumentChunker
        
        embedding_service = get_embedding_service()
        qdrant = get_qdrant_db()
        
        # Chunk document
        chunker = LegalDocumentChunker(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            respect_structure=True,
        )
        
        doc_metadata = {
            "source": file.filename,
            "uploaded_by": current_user.username,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        
        chunks = chunker.chunk_document(text, doc_metadata)
        logger.info(f"Created {len(chunks)} chunks from {file.filename}")
        
        # Embed chunks
        chunk_texts = [c.content for c in chunks]
        embeddings = embedding_service.encode_documents(chunk_texts, show_progress=False)
        
        # Prepare payloads
        payloads = []
        vectors = []
        for i, chunk in enumerate(chunks):
            payload = {
                "content": chunk.content,
                **chunk.metadata,
            }
            payloads.append(payload)
            vectors.append(embeddings[i].tolist())
        
        # Index to Qdrant
        await qdrant.upsert_vectors(
            collection_name=settings.qdrant_legal_collection,
            vectors=vectors,
            payloads=payloads,
        )

        logger.info(
            f"✅ Successfully indexed {len(chunks)} chunks from {file.filename} by {current_user.username}"
        )
        logger.info(f"=== UPLOAD DOCUMENT END ===")

        return {
            "success": True,
            "message": f"Đã index {len(chunks)} chunks từ {file.filename}",
            "filename": file.filename,
            "chunks": len(chunks),
            "collection": settings.qdrant_legal_collection,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý file: {str(e)}"
        )


@router.get("/documents")
async def list_documents(
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all documents in the vector database."""
    try:
        from src.database.qdrant import get_qdrant_db
        qdrant = get_qdrant_db()
        
        # Get all documents (scroll through collection)
        # Group by source filename
        points = await qdrant.scroll(
            collection_name=settings.qdrant_legal_collection,
            limit=1000,  # Adjust if needed
        )
        
        # Group by source
        docs_map = {}
        for point in points:
            payload = point.get("payload", {})
            source = payload.get("source", "Unknown")
            
            if source not in docs_map:
                docs_map[source] = {
                    "filename": source,
                    "chunks": 0,
                    "uploaded_by": payload.get("uploaded_by", "Unknown"),
                    "uploaded_at": payload.get("uploaded_at", "Unknown"),
                }
            docs_map[source]["chunks"] += 1
        
        documents = list(docs_map.values())
        
        return {
            "total": len(documents),
            "documents": documents,
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.delete("/documents/{filename}")
async def delete_document(
    filename: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete all chunks of a document from the vector database."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có thể xóa tài liệu",
        )
    
    try:
        from src.database.qdrant import get_qdrant_db
        qdrant = get_qdrant_db()
        
        # Delete points by metadata filter
        deleted_count = await qdrant.delete_by_filter(
            collection_name=settings.qdrant_legal_collection,
            filter_condition={
                "key": "source",
                "match": {"value": filename}
            }
        )
        
        logger.info(f"Deleted {deleted_count} chunks of {filename} by {current_user.username}")
        
        return {
            "success": True,
            "message": f"Đã xóa {deleted_count} chunks của {filename}",
            "deleted_chunks": deleted_count,
        }
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


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
    
    # Document count from Qdrant
    try:
        from src.database.qdrant import get_qdrant_db
        qdrant = get_qdrant_db()
        doc_count = await qdrant.count_points(settings.qdrant_legal_collection)
    except:
        doc_count = 0

    return {
        "total_schools": truong_count or 0,
        "total_majors": nganh_count or 0,
        "total_scores": diem_chuan_count or 0,
        "total_documents": doc_count or 0,
        "total_chats": 0,
        "recent_chats": 0,
        "latest_year": latest_year,
    }

