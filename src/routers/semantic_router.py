"""Semantic Router for fast intent classification."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np

from src.core.config import settings
from src.core.embeddings import get_embedding_service
from src.database.qdrant import get_qdrant_db

logger = logging.getLogger(__name__)


def load_routes_from_json() -> list["Route"]:
    """Load routes from intents.json file."""
    intent_file = settings.intents_dir / "intents.json"
    if not intent_file.exists():
        logger.warning(f"Intent file not found: {intent_file}, using defaults")
        return []

    try:
        data = json.loads(intent_file.read_text(encoding="utf-8"))
        routes = []
        for intent in data.get("intents", []):
            routes.append(Route(
                name=intent["name"],
                description=intent.get("description", ""),
                examples=intent.get("examples", []),
            ))
        return routes
    except Exception as e:
        logger.error(f"Failed to load intents: {e}")
        return []


@dataclass
class Route:
    """A route definition for the semantic router."""

    name: str
    description: str
    examples: list[str]
    response_template: Optional[str] = None


# Default routes for the admission chatbot
DEFAULT_ROUTES = [
    Route(
        name="score_lookup",
        description="Tra cứu điểm chuẩn, chỉ tiêu tuyển sinh",
        examples=[
            "Điểm chuẩn Học viện Kỹ thuật Quân sự năm 2024",
            "Điểm chuẩn năm nay là bao nhiêu",
            "Với 25 điểm khối A có vào được không",
            "Trường nào điểm thấp nhất",
            "So sánh điểm chuẩn 2023 và 2024",
            "Chỉ tiêu tuyển sinh năm nay",
            "Điểm sàn các trường quân đội",
            "Học viện Quân y lấy bao nhiêu điểm",
            "Điểm chuẩn ngành công nghệ thông tin",
            "25 điểm vào được trường nào",
        ],
    ),
    Route(
        name="regulation",
        description="Hỏi về quy định, tiêu chuẩn, điều kiện, thủ tục tuyển sinh",
        examples=[
            "Tiêu chuẩn sức khỏe để thi vào quân đội",
            "Điều kiện đăng ký xét tuyển",
            "Yêu cầu về chính trị như thế nào",
            "Quy trình đăng ký xét tuyển",
            "Hồ sơ cần những gì",
            "Độ tuổi được đăng ký là bao nhiêu",
            "Chiều cao tối thiểu là bao nhiêu",
            "Có cần khám sức khỏe không",
            "Tiêu chuẩn về mắt như thế nào",
            "Quy định về đối tượng ưu tiên",
            "Thí sinh đã đăng ký sơ tuyển có phải đăng ký dự thi tốt nghiệp THPT không",
            "Quy trình sơ tuyển như thế nào",
            "Thủ tục nhập học ra sao",
            "Đối tượng nào được ưu tiên xét tuyển",
            "Khu vực tuyển sinh được quy định thế nào",
            "Thí sinh nữ có được đăng ký không",
            "Có cần xác nhận lý lịch không",
            "Điều kiện về học lực thế nào",
            "Quy định về cộng điểm ưu tiên",
            "Khám sức khỏe sơ tuyển gồm những gì",
            "Các trường quân đội sử dụng tổ hợp xét tuyển nào",
            "Tổ hợp môn thi vào trường quân đội",
            "Xét tuyển theo khối nào",
            "Nguyên tắc tuyển sinh quân sự",
        ],
    ),
    Route(
        name="faq",
        description="Câu hỏi thường gặp về đời sống, chế độ, chính sách trong quân đội",
        examples=[
            "Học quân đội có được miễn học phí không",
            "Ra trường được phân công ở đâu",
            "Có được về thăm nhà không",
            "Lương học viên là bao nhiêu",
            "Học bao lâu thì ra trường",
            "Có được dùng điện thoại không",
            "Ngành nào dễ xin việc nhất",
            "Nữ có được thi vào không",
            "Cận thị có được thi không",
            "Có hình xăm có được thi không",
        ],
    ),
    Route(
        name="greeting",
        description="Chào hỏi, cảm ơn, tạm biệt",
        examples=[
            "Xin chào",
            "Chào bạn",
            "Hello",
            "Hi",
            "Cảm ơn bạn",
            "Thanks",
            "Tạm biệt",
            "Bye",
            "Bạn là ai",
            "Bạn có thể giúp gì",
        ],
    ),
    Route(
        name="comparison",
        description="So sánh các trường, ngành học",
        examples=[
            "So sánh Học viện KTQS và Học viện Quân y",
            "Trường nào tốt nhất",
            "Ngành nào có tương lai",
            "Nên chọn trường nào",
            "So sánh điểm các trường",
            "Trường nào khó vào nhất",
        ],
    ),
    Route(
        name="school_info",
        description="Giới thiệu, thông tin tổng quan về trường",
        examples=[
            "Giới thiệu về Học viện Kỹ thuật Quân sự",
            "Học viện Hải quân có những ngành gì",
            "Thông tin về Trường Sĩ quan Lục quân",
            "Cho tôi biết về Học viện Quân y",
            "Trường Sĩ quan Chính trị đào tạo gì",
            "Học viện Biên phòng ở đâu",
            "Mô tả về Học viện Phòng không Không quân",
            "Trường Sĩ quan Công binh là trường gì",
            "Giới thiệu trường quân đội",
            "Học viện Hậu cần có gì đặc biệt",
        ],
    ),
]


class SemanticRouter:
    """Fast semantic router for intent classification."""

    def __init__(
        self,
        routes: Optional[list[Route]] = None,
        similarity_threshold: float = 0.85,
        use_cache: bool = True,
    ):
        """Initialize semantic router.

        Args:
            routes: List of route definitions.
            similarity_threshold: Minimum similarity for routing.
            use_cache: Whether to use vector cache.
        """
        # Try loading from JSON first, fall back to defaults
        if routes:
            self.routes = routes
        else:
            self.routes = load_routes_from_json() or DEFAULT_ROUTES
        self.similarity_threshold = similarity_threshold
        self.use_cache = use_cache

        self.embedding_service = get_embedding_service()
        self.qdrant = get_qdrant_db()

        self._route_embeddings: Optional[dict[str, np.ndarray]] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize router with route embeddings."""
        if self._initialized:
            return

        logger.info("Initializing semantic router...")

        # Compute embeddings for all route examples
        self._route_embeddings = {}

        for route in self.routes:
            embeddings = self.embedding_service.encode_documents(
                route.examples,
                batch_size=32,
            )
            self._route_embeddings[route.name] = embeddings

        # Optionally index in Qdrant for persistence
        if self.use_cache:
            await self._index_routes()

        self._initialized = True
        logger.info(f"Semantic router initialized with {len(self.routes)} routes")

    async def _index_routes(self) -> None:
        """Index route examples in Qdrant."""
        try:
            # Create collection if not exists
            await self.qdrant.create_collection(
                collection_name=settings.qdrant_intents_collection,
                vector_size=self.embedding_service.dimension,
            )

            # Count expected examples
            expected_count = sum(len(route.examples) for route in self.routes)

            # Check if already indexed with correct count
            count = await self.qdrant.count_points(settings.qdrant_intents_collection)
            if count == expected_count:
                logger.info("Routes already indexed in Qdrant")
                return

            # Re-index if count mismatch (routes changed)
            if count > 0:
                logger.info(f"Route count mismatch (cached={count}, expected={expected_count}), re-indexing...")
                await self.qdrant.delete_collection(settings.qdrant_intents_collection)
                await self.qdrant.create_collection(
                    collection_name=settings.qdrant_intents_collection,
                    vector_size=self.embedding_service.dimension,
                )

            # Index all examples
            vectors = []
            payloads = []

            for route in self.routes:
                for example in route.examples:
                    embedding = self.embedding_service.encode(example)[0]
                    vectors.append(embedding.tolist())
                    payloads.append({
                        "route": route.name,
                        "example": example,
                        "description": route.description,
                    })

            await self.qdrant.upsert_vectors(
                collection_name=settings.qdrant_intents_collection,
                vectors=vectors,
                payloads=payloads,
            )

            logger.info(f"Indexed {len(vectors)} route examples in Qdrant")

        except Exception as e:
            logger.warning(f"Failed to index routes in Qdrant: {e}")

    async def route(self, query: str) -> dict[str, Any]:
        """Route a query to the best matching intent.

        Args:
            query: User query.

        Returns:
            Routing result with intent and confidence.
        """
        if not self._initialized:
            await self.initialize()

        # Embed the query
        query_embedding = self.embedding_service.encode_query(query)

        # Find best matching route
        best_route = None
        best_score = 0.0
        all_scores = {}

        for route_name, route_embeddings in self._route_embeddings.items():
            # Compute similarities with all examples
            similarities = self.embedding_service.similarity(
                query_embedding, route_embeddings
            )

            # Use max similarity
            max_sim = float(np.max(similarities))
            all_scores[route_name] = max_sim

            if max_sim > best_score:
                best_score = max_sim
                best_route = route_name

        # Check threshold
        if best_score < self.similarity_threshold:
            return {
                "intent": "unknown",
                "confidence": best_score,
                "all_scores": all_scores,
                "matched": False,
            }

        return {
            "intent": best_route,
            "confidence": best_score,
            "all_scores": all_scores,
            "matched": True,
        }

    async def route_with_qdrant(self, query: str) -> dict[str, Any]:
        """Route using Qdrant vector search (alternative method).

        Args:
            query: User query.

        Returns:
            Routing result.
        """
        query_embedding = self.embedding_service.encode_query(query)

        results = await self.qdrant.search(
            collection_name=settings.qdrant_intents_collection,
            query_vector=query_embedding.tolist(),
            limit=5,
        )

        if not results:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "matched": False,
            }

        # Aggregate scores by route
        route_scores = {}
        for result in results:
            route = result["payload"]["route"]
            score = result["score"]
            if route not in route_scores:
                route_scores[route] = []
            route_scores[route].append(score)

        # Use max score per route
        route_max_scores = {
            route: max(scores) for route, scores in route_scores.items()
        }

        best_route = max(route_max_scores, key=route_max_scores.get)
        best_score = route_max_scores[best_route]

        if best_score < self.similarity_threshold:
            return {
                "intent": "unknown",
                "confidence": best_score,
                "matched": False,
            }

        return {
            "intent": best_route,
            "confidence": best_score,
            "matched": True,
            "similar_examples": [
                r["payload"]["example"] for r in results[:3]
            ],
        }

    def add_route(self, route: Route) -> None:
        """Add a new route dynamically.

        Args:
            route: Route to add.
        """
        self.routes.append(route)
        self._initialized = False  # Force re-initialization

    def get_route_info(self, route_name: str) -> Optional[Route]:
        """Get information about a route.

        Args:
            route_name: Name of the route.

        Returns:
            Route object or None.
        """
        for route in self.routes:
            if route.name == route_name:
                return route
        return None

    async def get_faq_response(self, query: str) -> Optional[str]:
        """Get FAQ response if query matches a FAQ pattern.

        Args:
            query: User query.

        Returns:
            FAQ response or None.
        """
        result = await self.route(query)

        if result["intent"] == "faq" and result["matched"]:
            # Could return pre-defined response
            route = self.get_route_info("faq")
            if route and route.response_template:
                return route.response_template

        return None


# Factory function
_router_instance: Optional[SemanticRouter] = None


def get_semantic_router() -> SemanticRouter:
    """Get global semantic router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = SemanticRouter(
            similarity_threshold=settings.router_similarity_threshold,
        )
    return _router_instance
