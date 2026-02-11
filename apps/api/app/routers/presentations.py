"""
Presentations Router — endpoints for generating, downloading, and previewing
presentations.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.engine.builder import PresentationBuilder
from app.engine.renderer import render_to_images
from app.models.requests import GenerateRequest, GenerateResponse
from app.services.llm_service import generate_presentation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["presentations"])

# In-memory store for generated files (would be a DB/cache in production)
_presentations: dict[str, dict] = {}


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate a presentation from a user prompt.

    1. Calls the LLM to produce a Presentation IR.
    2. Builds the .pptx file.
    3. Optionally renders preview images.
    4. Returns the structured response.
    """
    settings = get_settings()
    presentation_id = str(uuid.uuid4())

    try:
        # Step 1: LLM → Presentation IR
        presentation = await generate_presentation(
            prompt=request.prompt,
            num_slides=request.num_slides,
        )

        # Step 2: Build PPTX
        output_dir = settings.OUTPUT_DIR / presentation_id
        pptx_path = output_dir / f"{presentation_id}.pptx"

        builder = PresentationBuilder()
        builder.build(presentation, pptx_path)

        # Step 3: Render previews (best-effort)
        preview_paths: list[Path] = []
        try:
            preview_dir = output_dir / "previews"
            preview_paths = render_to_images(pptx_path, preview_dir)
        except Exception as e:
            logger.warning("Preview rendering failed (non-fatal): %s", e)

        # Step 4: Build preview URLs
        preview_urls = [
            f"/api/preview/{presentation_id}/{i}"
            for i in range(len(preview_paths))
        ]

        # Store metadata
        _presentations[presentation_id] = {
            "pptx_path": str(pptx_path),
            "preview_paths": [str(p) for p in preview_paths],
            "presentation": presentation,
        }

        return GenerateResponse(
            presentation_id=presentation_id,
            presentation=presentation,
            download_url=f"/api/download/{presentation_id}",
            preview_urls=preview_urls,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Generation failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@router.get("/download/{presentation_id}")
async def download(presentation_id: str):
    """Download the generated .pptx file."""
    entry = _presentations.get(presentation_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Presentation not found.")

    pptx_path = Path(entry["pptx_path"])
    if not pptx_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")

    return FileResponse(
        path=str(pptx_path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"presentation-{presentation_id[:8]}.pptx",
    )


@router.get("/preview/{presentation_id}/{slide_index}")
async def preview(presentation_id: str, slide_index: int):
    """Get a PNG preview for a specific slide."""
    entry = _presentations.get(presentation_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Presentation not found.")

    preview_paths = entry.get("preview_paths", [])
    if slide_index < 0 or slide_index >= len(preview_paths):
        raise HTTPException(status_code=404, detail="Slide preview not found.")

    img_path = Path(preview_paths[slide_index])
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Preview image not found on disk.")

    return FileResponse(path=str(img_path), media_type="image/png")
