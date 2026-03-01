"""Database setup script - creates PostgreSQL schema and Qdrant collections."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.database.models import Base, DiemChuan, KhoiThi, Nganh, Truong, User
from src.database.postgres import get_postgres_db
from src.database.qdrant import get_qdrant_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# SQL for creating views and functions
ADDITIONAL_SQL = """
-- =============================================================================
-- Vietnamese text search function using unaccent
-- =============================================================================
CREATE OR REPLACE FUNCTION vi_unaccent(text)
RETURNS text AS $$
    SELECT unaccent('unaccent', $1)
$$ LANGUAGE SQL IMMUTABLE;

-- =============================================================================
-- Trigger function to auto-populate ten_khong_dau
-- =============================================================================
CREATE OR REPLACE FUNCTION update_ten_khong_dau()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'truong' THEN
        NEW.ten_khong_dau := lower(vi_unaccent(NEW.ten_truong));
    ELSIF TG_TABLE_NAME = 'nganh' THEN
        NEW.ten_khong_dau := lower(vi_unaccent(NEW.ten_nganh));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS trg_truong_ten_khong_dau ON truong;
DROP TRIGGER IF EXISTS trg_nganh_ten_khong_dau ON nganh;

-- Create triggers
CREATE TRIGGER trg_truong_ten_khong_dau
    BEFORE INSERT OR UPDATE ON truong
    FOR EACH ROW EXECUTE FUNCTION update_ten_khong_dau();

CREATE TRIGGER trg_nganh_ten_khong_dau
    BEFORE INSERT OR UPDATE ON nganh
    FOR EACH ROW EXECUTE FUNCTION update_ten_khong_dau();

-- =============================================================================
-- View for easy score lookup
-- =============================================================================
CREATE OR REPLACE VIEW view_tra_cuu_diem AS
SELECT
    dc.id AS diem_chuan_id,
    t.ma_truong,
    t.ten_truong,
    t.ten_khong_dau,
    t.loai_truong,
    n.ma_nganh,
    n.ten_nganh,
    n.ten_khong_dau AS ten_nganh_khong_dau,
    kt.ma_khoi,
    kt.ten_khoi,
    kt.mon_hoc,
    dc.nam,
    dc.diem_chuan,
    dc.chi_tieu,
    dc.gioi_tinh,
    dc.khu_vuc,
    dc.doi_tuong,
    dc.ghi_chu
FROM diem_chuan dc
JOIN nganh n ON dc.nganh_id = n.id
JOIN truong t ON n.truong_id = t.id
JOIN khoi_thi kt ON dc.khoi_thi_id = kt.id
WHERE t.active = true AND n.active = true AND kt.active = true;

-- =============================================================================
-- Indexes for Vietnamese text search
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_truong_ten_khong_dau_trgm
    ON truong USING gin (ten_khong_dau gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_nganh_ten_khong_dau_trgm
    ON nganh USING gin (ten_khong_dau gin_trgm_ops);

-- Index for year queries
CREATE INDEX IF NOT EXISTS idx_diem_chuan_nam ON diem_chuan(nam DESC);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_diem_chuan_nganh_nam
    ON diem_chuan(nganh_id, nam DESC);
"""


async def setup_postgres():
    """Create PostgreSQL tables, views, and indexes."""
    logger.info("Setting up PostgreSQL database...")

    db = get_postgres_db()

    # Create tables
    await db.create_tables()
    logger.info("Tables created successfully")

    # Execute additional SQL (views, triggers, indexes)
    try:
        async with db.get_session() as session:
            # Split and execute each statement
            from sqlalchemy import text

            statements = ADDITIONAL_SQL.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--'):
                    try:
                        await session.execute(text(stmt))
                    except Exception as e:
                        # Some statements might fail if objects already exist
                        logger.warning(f"Statement warning: {e}")
            await session.commit()
        logger.info("Views, triggers, and indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create additional objects: {e}")
        raise

    await db.close()


async def setup_qdrant():
    """Create Qdrant collections."""
    logger.info("Setting up Qdrant collections...")

    qdrant = get_qdrant_db()
    vector_size = settings.embedding_dimension

    collections = [
        (settings.qdrant_legal_collection, "Legal documents collection"),
        (settings.qdrant_sql_examples_collection, "SQL few-shot examples"),
        (settings.qdrant_intents_collection, "Intent vectors for routing"),
    ]

    for collection_name, description in collections:
        try:
            created = await qdrant.create_collection(
                collection_name=collection_name,
                vector_size=vector_size,
                distance="Cosine",
            )
            if created:
                logger.info(f"Created collection: {collection_name} - {description}")
            else:
                logger.info(f"Collection already exists: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise

    await qdrant.close()


async def seed_khoi_thi():
    """Seed initial khoi_thi (exam subject groups) data."""
    logger.info("Seeding khoi_thi data...")

    db = get_postgres_db()

    khoi_thi_data = [
        ("A00", "Khối A00", "Toán, Vật lý, Hóa học"),
        ("A01", "Khối A01", "Toán, Vật lý, Tiếng Anh"),
        ("B00", "Khối B00", "Toán, Hóa học, Sinh học"),
        ("C00", "Khối C00", "Ngữ văn, Lịch sử, Địa lý"),
        ("D01", "Khối D01", "Toán, Ngữ văn, Tiếng Anh"),
        ("D07", "Khối D07", "Toán, Hóa học, Tiếng Anh"),
    ]

    async with db.get_session() as session:
        from sqlalchemy import select

        for ma_khoi, ten_khoi, mon_hoc in khoi_thi_data:
            # Check if exists
            result = await session.execute(
                select(KhoiThi).where(KhoiThi.ma_khoi == ma_khoi)
            )
            existing = result.scalar_one_or_none()

            if not existing:
                khoi = KhoiThi(
                    ma_khoi=ma_khoi,
                    ten_khoi=ten_khoi,
                    mon_hoc=mon_hoc,
                )
                session.add(khoi)
                logger.info(f"Added khoi_thi: {ma_khoi}")
            else:
                logger.info(f"Khoi_thi already exists: {ma_khoi}")

        await session.commit()

    await db.close()


async def create_admin_user():
    """Create default admin user."""
    logger.info("Creating default admin user...")

    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    db = get_postgres_db()

    async with db.get_session() as session:
        from sqlalchemy import select

        # Check if admin exists
        result = await session.execute(
            select(User).where(User.username == settings.admin_username)
        )
        existing = result.scalar_one_or_none()

        if not existing:
            admin = User(
                username=settings.admin_username,
                hashed_password=pwd_context.hash(settings.admin_password),
                full_name="Administrator",
                is_active=True,
                is_superuser=True,
            )
            session.add(admin)
            await session.commit()
            logger.info(f"Admin user created: {settings.admin_username}")
        else:
            logger.info("Admin user already exists")

    await db.close()


async def main():
    """Run all setup tasks."""
    logger.info("=" * 60)
    logger.info("TSBot Database Setup")
    logger.info("=" * 60)

    try:
        # Setup PostgreSQL
        await setup_postgres()

        # Seed initial data
        await seed_khoi_thi()

        # Create admin user
        await create_admin_user()

        # Setup Qdrant
        await setup_qdrant()

        logger.info("=" * 60)
        logger.info("Database setup completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
