"""Script to seed initial data (schools, programs, sample scores)."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.embeddings import get_embedding_service
from src.database.models import DiemChuan, KhoiThi, Nganh, Truong
from src.database.postgres import get_postgres_db
from src.database.qdrant import get_qdrant_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample data for military schools
TRUONG_DATA = [
    {
        "ma_truong": "HVKTQS",
        "ten_truong": "Học viện Kỹ thuật Quân sự",
        "loai_truong": "quan_doi",
        "dia_chi": "236 Hoàng Quốc Việt, Cầu Giấy, Hà Nội",
        "website": "https://mta.edu.vn",
    },
    {
        "ma_truong": "HVQY",
        "ten_truong": "Học viện Quân y",
        "loai_truong": "quan_doi",
        "dia_chi": "160 Phùng Hưng, Hà Đông, Hà Nội",
        "website": "https://vmmu.edu.vn",
    },
    {
        "ma_truong": "SQLQ1",
        "ten_truong": "Trường Sĩ quan Lục quân 1",
        "loai_truong": "quan_doi",
        "dia_chi": "Sơn Tây, Hà Nội",
    },
    {
        "ma_truong": "SQCT",
        "ten_truong": "Trường Sĩ quan Chính trị",
        "loai_truong": "quan_doi",
        "dia_chi": "Bắc Ninh",
    },
    {
        "ma_truong": "HVPKKQ",
        "ten_truong": "Học viện Phòng không - Không quân",
        "loai_truong": "quan_doi",
        "dia_chi": "Sơn Tây, Hà Nội",
    },
    {
        "ma_truong": "HVHQ",
        "ten_truong": "Học viện Hải quân",
        "loai_truong": "quan_doi",
        "dia_chi": "Nha Trang, Khánh Hòa",
    },
    {
        "ma_truong": "SQTT",
        "ten_truong": "Trường Sĩ quan Thông tin",
        "loai_truong": "quan_doi",
        "dia_chi": "Nha Trang, Khánh Hòa",
    },
    {
        "ma_truong": "HVBP",
        "ten_truong": "Học viện Biên phòng",
        "loai_truong": "quan_doi",
        "dia_chi": "Sơn Tây, Hà Nội",
    },
]

# Sample programs
NGANH_DATA = [
    # HVKTQS
    {"truong": "HVKTQS", "ma_nganh": "CNTT", "ten_nganh": "Công nghệ thông tin"},
    {"truong": "HVKTQS", "ma_nganh": "DTTT", "ten_nganh": "Điện tử - Viễn thông"},
    {"truong": "HVKTQS", "ma_nganh": "CNCK", "ten_nganh": "Công nghệ cơ khí"},
    {"truong": "HVKTQS", "ma_nganh": "CKOT", "ten_nganh": "Cơ khí ô tô"},
    {"truong": "HVKTQS", "ma_nganh": "XDCT", "ten_nganh": "Xây dựng công trình"},
    # HVQY
    {"truong": "HVQY", "ma_nganh": "YDK", "ten_nganh": "Y đa khoa"},
    {"truong": "HVQY", "ma_nganh": "RHM", "ten_nganh": "Răng hàm mặt"},
    {"truong": "HVQY", "ma_nganh": "DUOC", "ten_nganh": "Dược học"},
    # HVPKKQ
    {"truong": "HVPKKQ", "ma_nganh": "CTQS", "ten_nganh": "Chỉ huy tham mưu"},
    {"truong": "HVPKKQ", "ma_nganh": "KTQS", "ten_nganh": "Kỹ thuật quân sự"},
    # Other schools
    {"truong": "SQLQ1", "ma_nganh": "CTQS", "ten_nganh": "Chỉ huy tham mưu lục quân"},
    {"truong": "SQCT", "ma_nganh": "CTQS", "ten_nganh": "Chính trị quân sự"},
    {"truong": "HVHQ", "ma_nganh": "CTQS", "ten_nganh": "Chỉ huy tham mưu hải quân"},
    {"truong": "SQTT", "ma_nganh": "KTTT", "ten_nganh": "Kỹ thuật thông tin"},
    {"truong": "HVBP", "ma_nganh": "BPQS", "ten_nganh": "Biên phòng quân sự"},
]

# Sample admission scores (2024)
DIEM_CHUAN_DATA = [
    # HVKTQS 2024
    {"truong": "HVKTQS", "nganh": "CNTT", "khoi": "A00", "nam": 2024, "diem": 27.5, "chi_tieu": 50},
    {"truong": "HVKTQS", "nganh": "CNTT", "khoi": "A01", "nam": 2024, "diem": 27.0, "chi_tieu": 30},
    {"truong": "HVKTQS", "nganh": "DTTT", "khoi": "A00", "nam": 2024, "diem": 26.5, "chi_tieu": 40},
    {"truong": "HVKTQS", "nganh": "CNCK", "khoi": "A00", "nam": 2024, "diem": 25.5, "chi_tieu": 35},
    {"truong": "HVKTQS", "nganh": "CKOT", "khoi": "A00", "nam": 2024, "diem": 25.0, "chi_tieu": 30},
    # HVQY 2024
    {"truong": "HVQY", "nganh": "YDK", "khoi": "B00", "nam": 2024, "diem": 28.0, "chi_tieu": 100},
    {"truong": "HVQY", "nganh": "RHM", "khoi": "B00", "nam": 2024, "diem": 27.5, "chi_tieu": 30},
    {"truong": "HVQY", "nganh": "DUOC", "khoi": "B00", "nam": 2024, "diem": 26.0, "chi_tieu": 40},
    # HVKTQS 2023
    {"truong": "HVKTQS", "nganh": "CNTT", "khoi": "A00", "nam": 2023, "diem": 27.0, "chi_tieu": 45},
    {"truong": "HVKTQS", "nganh": "DTTT", "khoi": "A00", "nam": 2023, "diem": 26.0, "chi_tieu": 40},
    # HVQY 2023
    {"truong": "HVQY", "nganh": "YDK", "khoi": "B00", "nam": 2023, "diem": 27.5, "chi_tieu": 100},
    # Other schools 2024
    {"truong": "HVPKKQ", "nganh": "CTQS", "khoi": "A00", "nam": 2024, "diem": 24.0, "chi_tieu": 60},
    {"truong": "SQLQ1", "nganh": "CTQS", "khoi": "A00", "nam": 2024, "diem": 23.5, "chi_tieu": 200},
    {"truong": "SQCT", "nganh": "CTQS", "khoi": "C00", "nam": 2024, "diem": 24.5, "chi_tieu": 150},
    {"truong": "HVHQ", "nganh": "CTQS", "khoi": "A00", "nam": 2024, "diem": 24.0, "chi_tieu": 80},
]

def load_sql_examples() -> list[dict]:
    """Load SQL examples from JSON file."""
    sql_file = settings.sql_examples_dir / "examples.json"
    if sql_file.exists():
        data = json.loads(sql_file.read_text(encoding="utf-8"))
        return data.get("examples", [])
    logger.warning(f"SQL examples file not found: {sql_file}")
    return []


def load_intents() -> list[dict]:
    """Load intent data from JSON file."""
    intent_file = settings.intents_dir / "intents.json"
    if intent_file.exists():
        data = json.loads(intent_file.read_text(encoding="utf-8"))
        return data.get("intents", [])
    logger.warning(f"Intents file not found: {intent_file}")
    return []


async def seed_schools(db):
    """Seed schools data."""
    logger.info("Seeding schools...")

    async with db.get_session() as session:
        from sqlalchemy import select

        for truong_data in TRUONG_DATA:
            # Check if exists
            result = await session.execute(
                select(Truong).where(Truong.ma_truong == truong_data["ma_truong"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                truong = Truong(**truong_data)
                session.add(truong)
                logger.info(f"  Added: {truong_data['ten_truong']}")

        await session.commit()


async def seed_programs(db):
    """Seed programs data."""
    logger.info("Seeding programs...")

    async with db.get_session() as session:
        from sqlalchemy import select

        # Get school mapping
        result = await session.execute(select(Truong))
        truong_map = {t.ma_truong: t.id for t in result.scalars().all()}

        for nganh_data in NGANH_DATA:
            truong_id = truong_map.get(nganh_data["truong"])
            if not truong_id:
                logger.warning(f"  School not found: {nganh_data['truong']}")
                continue

            # Check if exists
            result = await session.execute(
                select(Nganh).where(
                    Nganh.truong_id == truong_id,
                    Nganh.ma_nganh == nganh_data["ma_nganh"],
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                nganh = Nganh(
                    truong_id=truong_id,
                    ma_nganh=nganh_data["ma_nganh"],
                    ten_nganh=nganh_data["ten_nganh"],
                )
                session.add(nganh)
                logger.info(f"  Added: {nganh_data['ten_nganh']}")

        await session.commit()


async def seed_scores(db):
    """Seed admission scores data."""
    logger.info("Seeding admission scores...")

    async with db.get_session() as session:
        from sqlalchemy import select

        # Get mappings
        result = await session.execute(select(Truong))
        truong_map = {t.ma_truong: t.id for t in result.scalars().all()}

        result = await session.execute(select(Nganh))
        nganh_map = {(n.truong_id, n.ma_nganh): n.id for n in result.scalars().all()}

        result = await session.execute(select(KhoiThi))
        khoi_map = {k.ma_khoi: k.id for k in result.scalars().all()}

        for score_data in DIEM_CHUAN_DATA:
            truong_id = truong_map.get(score_data["truong"])
            nganh_id = nganh_map.get((truong_id, score_data["nganh"]))
            khoi_id = khoi_map.get(score_data["khoi"])

            if not all([truong_id, nganh_id, khoi_id]):
                logger.warning(f"  Missing reference for: {score_data}")
                continue

            # Check if exists
            result = await session.execute(
                select(DiemChuan).where(
                    DiemChuan.nganh_id == nganh_id,
                    DiemChuan.khoi_thi_id == khoi_id,
                    DiemChuan.nam == score_data["nam"],
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                diem_chuan = DiemChuan(
                    nganh_id=nganh_id,
                    khoi_thi_id=khoi_id,
                    nam=score_data["nam"],
                    diem_chuan=score_data["diem"],
                    chi_tieu=score_data.get("chi_tieu"),
                )
                session.add(diem_chuan)
                logger.info(
                    f"  Added: {score_data['truong']} - {score_data['nganh']} "
                    f"- {score_data['khoi']} - {score_data['nam']}"
                )

        await session.commit()


async def seed_sql_examples():
    """Seed SQL few-shot examples into Qdrant."""
    logger.info("Seeding SQL examples from JSON...")

    sql_examples = load_sql_examples()
    if not sql_examples:
        logger.warning("  No SQL examples found, skipping")
        return

    embedding_service = get_embedding_service()
    qdrant = get_qdrant_db()

    # Create collection
    await qdrant.create_collection(
        collection_name=settings.qdrant_sql_examples_collection,
        vector_size=embedding_service.dimension,
    )

    # Check if already seeded
    count = await qdrant.count_points(settings.qdrant_sql_examples_collection)
    if count > 0:
        logger.info(f"  SQL examples already seeded ({count} examples)")
        return

    # Embed and store examples
    vectors = []
    payloads = []

    for example in sql_examples:
        embedding = embedding_service.encode(example["question"])[0]
        vectors.append(embedding.tolist())
        payloads.append({
            "question": example["question"],
            "sql": example["sql"],
            "category": example.get("category", ""),
        })

    await qdrant.upsert_vectors(
        collection_name=settings.qdrant_sql_examples_collection,
        vectors=vectors,
        payloads=payloads,
    )

    logger.info(f"  Added {len(sql_examples)} SQL examples")

    await qdrant.close()


async def seed_intents():
    """Seed intent examples into Qdrant for Semantic Router."""
    logger.info("Seeding intent examples from JSON...")

    intents = load_intents()
    if not intents:
        logger.warning("  No intents found, skipping")
        return

    embedding_service = get_embedding_service()
    qdrant = get_qdrant_db()

    # Create collection
    await qdrant.create_collection(
        collection_name=settings.qdrant_intents_collection,
        vector_size=embedding_service.dimension,
    )

    # Check if already seeded
    count = await qdrant.count_points(settings.qdrant_intents_collection)
    if count > 0:
        logger.info(f"  Intents already seeded ({count} examples)")
        return

    # Embed and store all intent examples
    vectors = []
    payloads = []
    total_examples = 0

    for intent in intents:
        intent_name = intent["name"]
        description = intent.get("description", "")
        examples = intent.get("examples", [])

        for example in examples:
            embedding = embedding_service.encode(example)[0]
            vectors.append(embedding.tolist())
            payloads.append({
                "intent": intent_name,
                "example": example,
                "description": description,
            })
            total_examples += 1

    await qdrant.upsert_vectors(
        collection_name=settings.qdrant_intents_collection,
        vectors=vectors,
        payloads=payloads,
    )

    logger.info(f"  Added {total_examples} intent examples from {len(intents)} intents")

    await qdrant.close()


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Seeding TSBot Database")
    logger.info("=" * 60)

    db = get_postgres_db()

    try:
        await seed_schools(db)
        await seed_programs(db)
        await seed_scores(db)
        await seed_sql_examples()
        await seed_intents()

        logger.info("=" * 60)
        logger.info("Seeding completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        raise

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
