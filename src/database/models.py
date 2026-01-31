"""SQLAlchemy models for TSBot database."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Truong(Base):
    """Military schools/academies table."""

    __tablename__ = "truong"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ma_truong: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    ten_truong: Mapped[str] = mapped_column(String(255), nullable=False)
    ten_khong_dau: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    loai_truong: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'quan_doi', 'cong_an', 'khac'
    dia_chi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    nganh_list: Mapped[list["Nganh"]] = relationship("Nganh", back_populates="truong")


class Nganh(Base):
    """Academic programs/majors table."""

    __tablename__ = "nganh"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    truong_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("truong.id", ondelete="CASCADE"), nullable=False
    )
    ma_nganh: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ten_nganh: Mapped[str] = mapped_column(String(255), nullable=False)
    ten_khong_dau: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("truong_id", "ma_nganh", name="uq_truong_nganh"),)

    # Relationships
    truong: Mapped["Truong"] = relationship("Truong", back_populates="nganh_list")
    diem_chuan_list: Mapped[list["DiemChuan"]] = relationship(
        "DiemChuan", back_populates="nganh"
    )


class KhoiThi(Base):
    """Exam subject groups table."""

    __tablename__ = "khoi_thi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ma_khoi: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    ten_khoi: Mapped[str] = mapped_column(String(100), nullable=False)
    mon_hoc: Mapped[str] = mapped_column(String(255), nullable=False)  # Comma-separated subjects
    mo_ta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    diem_chuan_list: Mapped[list["DiemChuan"]] = relationship(
        "DiemChuan", back_populates="khoi_thi"
    )


class DiemChuan(Base):
    """Admission scores table - main data table updated yearly."""

    __tablename__ = "diem_chuan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nganh_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("nganh.id", ondelete="CASCADE"), nullable=False
    )
    khoi_thi_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("khoi_thi.id", ondelete="CASCADE"), nullable=False
    )
    nam: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    diem_chuan: Mapped[float] = mapped_column(Float, nullable=False)
    chi_tieu: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gioi_tinh: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )  # 'nam', 'nu', null (both)
    khu_vuc: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'KV1', 'KV2', 'KV2-NT', 'KV3'
    doi_tuong: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Priority groups
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "nganh_id", "khoi_thi_id", "nam", "gioi_tinh", "khu_vuc", name="uq_diem_chuan"
        ),
    )

    # Relationships
    nganh: Mapped["Nganh"] = relationship("Nganh", back_populates="diem_chuan_list")
    khoi_thi: Mapped["KhoiThi"] = relationship("KhoiThi", back_populates="diem_chuan_list")
    creator: Mapped[Optional["User"]] = relationship("User", back_populates="diem_chuan_created")


class User(Base):
    """Admin users table."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    diem_chuan_created: Mapped[list["DiemChuan"]] = relationship(
        "DiemChuan", back_populates="creator"
    )


class ChatHistory(Base):
    """Chat history for context and analytics."""

    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user', 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chat_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Feedback(Base):
    """User feedback for continuous improvement."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    chat_history_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("chat_history.id"), nullable=True
    )
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars
    feedback_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'helpful', 'not_helpful', 'incorrect', 'incomplete'
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
