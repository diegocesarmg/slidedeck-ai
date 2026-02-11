"""SlideDeck AI — FastAPI Application Entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifecycle ────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    settings = get_settings()
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(
        "SlideDeck AI API started. Provider: %s | Output: %s",
        settings.LLM_PROVIDER,
        settings.OUTPUT_DIR,
    )
    yield
    logger.info("SlideDeck AI API shutting down.")


# ── App ──────────────────────────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title=settings.APP_TITLE,
    version="0.1.0",
    description="Enterprise-grade Presentation Generator — converts prompts to .pptx",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────

from app.routers.presentations import router as presentations_router  # noqa: E402

app.include_router(presentations_router)


@app.get("/")
async def root():
    return {"message": "Welcome to SlideDeck AI API"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "provider": get_settings().LLM_PROVIDER,
    }
