#!/usr/bin/env python3
"""Index few-shot SQL examples into Qdrant for dynamic retrieval."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.embeddings import get_embedding_service
from src.database.qdrant import get_qdrant_db


async def main():
    data_file = Path(__file__).parent.parent / "data" / "few_shot_sql.json"
    if not data_file.exists():
        print(f"ERROR: {data_file} not found")
        sys.exit(1)

    with open(data_file) as f:
        examples = json.load(f)

    print(f"Loaded {len(examples)} few-shot examples")

    embedding_service = get_embedding_service()
    qdrant = get_qdrant_db()

    collection_name = settings.qdrant_sql_examples_collection
    vector_size = 1024  # BGE-M3 dimension

    # Recreate collection
    try:
        await qdrant.delete_collection(collection_name)
        print(f"Deleted existing collection '{collection_name}'")
    except Exception:
        pass

    await qdrant.create_collection(collection_name, vector_size=vector_size)
    print(f"Created collection '{collection_name}' (dim={vector_size})")

    # Index each example
    points = []
    for i, example in enumerate(examples):
        question = example["question"]
        sql = example["sql"]

        embedding = embedding_service.encode_query(question)

        points.append({
            "id": i + 1,
            "vector": embedding.tolist(),
            "payload": {"question": question, "sql": sql},
        })

    await qdrant.upsert_batch(collection_name, points)
    print(f"Indexed {len(points)} examples into '{collection_name}'")
    print("Done! Few-shot SQL examples ready for retrieval.")


if __name__ == "__main__":
    asyncio.run(main())
