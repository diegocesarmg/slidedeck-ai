"""SlideDeck AI — FastAPI Application Entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.presentations import router as presentations_router

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────────────────

settings = get_settings()

app = FastAPI(
    title=settings.APP_TITLE,
    version="0.1.0",
    description="Enterprise-grade Presentation Generator — converts prompts to .pptx",
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

app.include_router(presentations_router)


@app.get("/")
async def root():
    return {"message": "Welcome to SlideDeck AI API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ── Lifecycle ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Ensure output directories exist on startup."""
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("SlideDeck AI API started. Output dir: %s", settings.OUTPUT_DIR)
