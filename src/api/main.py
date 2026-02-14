"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.admin import router as admin_router
from src.api.chat import router as chat_router
from src.core.config import settings
from src.database.postgres import get_postgres_db
from src.database.qdrant import get_qdrant_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer() if settings.is_production else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting TSBot application", env=settings.app_env)

    # Initialize database connections
    db = get_postgres_db()
    qdrant = get_qdrant_db()

    # Check database connections and create tables
    if await db.health_check():
        logger.info("PostgreSQL connection established")
        await db.create_tables()
    else:
        logger.error("PostgreSQL connection failed")

    if await qdrant.health_check():
        logger.info("Qdrant connection established")
        # Create required collections if they don't exist
        collections_to_create = [
            settings.qdrant_legal_collection,
            settings.qdrant_sql_examples_collection,
        ]
        for col_name in collections_to_create:
            try:
                await qdrant.create_collection(
                    collection_name=col_name,
                    vector_size=settings.embedding_dimension,
                )
            except Exception as e:
                logger.warning(f"Failed to create collection '{col_name}'", error=str(e))
    else:
        logger.warning("Qdrant connection failed - vector search will be unavailable")

    # Initialize semantic router
    from src.routers.semantic_router import get_semantic_router
    router = get_semantic_router()
    try:
        await router.initialize()
        logger.info("Semantic router initialized")
    except Exception as e:
        logger.warning("Semantic router initialization failed", error=str(e))

    # Auto-load chunks from JSON for advanced RAG pipeline
    from src.agents.components.vector_store import auto_load_chunks
    try:
        await auto_load_chunks()
    except Exception as e:
        logger.warning("Auto-load chunks failed", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down TSBot application")
    await db.close()
    await qdrant.close()


# Create FastAPI app
app = FastAPI(
    title="TSBot API",
    description="Chatbot AI Tư Vấn Tuyển Sinh Quân Sự Việt Nam",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Check application health status."""
    db = get_postgres_db()
    qdrant = get_qdrant_db()

    postgres_ok = await db.health_check()
    qdrant_ok = await qdrant.health_check()

    # Check LLM
    from src.core.llm import get_llm_service
    llm = get_llm_service()
    llm_status = await llm.health_check()

    status = "healthy" if postgres_ok and qdrant_ok else "degraded"

    return {
        "status": status,
        "services": {
            "postgres": "up" if postgres_ok else "down",
            "qdrant": "up" if qdrant_ok else "down",
            "ollama": "up" if llm_status.get("ollama_server") else "down",
            "main_model": "ready" if llm_status.get("main_model") else "not_loaded",
            "grader_model": "ready" if llm_status.get("grader_model") else "not_loaded",
        },
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "description": "Chatbot AI Tư Vấn Tuyển Sinh Quân Sự Việt Nam",
        "docs": "/docs" if settings.debug else "disabled",
    }


# Include routers
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])


def run():
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
