"""
Presentations Router — endpoints for generating, downloading, previewing,
and refining presentations.
"""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.engine.builder import PresentationBuilder
from app.engine.renderer import render_to_images
from app.engine.scanner import scan_pptx
from app.models.slide import DesignTokens, GenerationMode, Presentation
from app.models.requests import GenerateResponse, RefineRequest, RefineResponse
from app.services.llm_service import generate_presentation, refine_presentation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["presentations"])

# In-memory store for generated presentations (would be a DB/cache in production)
_presentations: dict[str, dict] = {}


async def _save_upload(file: UploadFile, dest: Path) -> Path:
    """Save an uploaded file to disk."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest


async def _build_and_render(
    presentation: Presentation,
    presentation_id: str,
    template_path: Path | None = None,
) -> tuple[Path, list[Path]]:
    """Build PPTX and render previews."""
    settings = get_settings()
    output_dir = settings.OUTPUT_DIR / presentation_id
    pptx_path = output_dir / f"{presentation_id}.pptx"

    builder = PresentationBuilder()
    builder.build(presentation, pptx_path, template_path=template_path)

    # Render previews (best-effort)
    preview_paths: list[Path] = []
    try:
        preview_dir = output_dir / "previews"
        preview_paths = render_to_images(pptx_path, preview_dir)
    except Exception as e:
        logger.warning("Preview rendering failed (non-fatal): %s", e)

    return pptx_path, preview_paths


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    prompt: str = Form(..., min_length=3, max_length=5000),
    num_slides: Optional[int] = Form(None, ge=1, le=30),
    generation_mode: GenerationMode = Form(GenerationMode.FROM_SCRATCH),
    file: Optional[UploadFile] = File(None),
):
    """
    Generate a presentation from a user prompt.

    Accepts multipart/form-data to support optional file uploads.

    Modes:
    - from_scratch: Generate from prompt only
    - template: Use uploaded .pptx as template (preserves slide masters)
    - reference: Analyze uploaded .pptx style and replicate it
    """
    settings = get_settings()
    presentation_id = str(uuid.uuid4())

    try:
        design_tokens: DesignTokens | None = None
        template_path: Path | None = None
        uploaded_path: Path | None = None

        # Handle file upload for template/reference modes
        if file and generation_mode in (GenerationMode.TEMPLATE, GenerationMode.REFERENCE):
            upload_dir = settings.OUTPUT_DIR / presentation_id
            uploaded_path = await _save_upload(
                file, upload_dir / f"uploaded_{file.filename}"
            )

            if generation_mode == GenerationMode.TEMPLATE:
                template_path = uploaded_path
                # Also scan for design tokens to inject into LLM
                design_tokens = scan_pptx(uploaded_path)
            elif generation_mode == GenerationMode.REFERENCE:
                design_tokens = scan_pptx(uploaded_path)

        elif generation_mode != GenerationMode.FROM_SCRATCH and not file:
            raise ValueError(
                f"Mode '{generation_mode.value}' requires a .pptx file upload."
            )

        # Step 1: LLM → Presentation IR
        presentation = await generate_presentation(
            prompt=prompt,
            num_slides=num_slides,
            design_tokens=design_tokens,
        )

        # Step 2: Build PPTX + render previews
        pptx_path, preview_paths = await _build_and_render(
            presentation, presentation_id, template_path
        )

        # Step 3: Build response URLs
        preview_urls = [
            f"/api/preview/{presentation_id}/{i}"
            for i in range(len(preview_paths))
        ]

        # Store metadata
        _presentations[presentation_id] = {
            "pptx_path": str(pptx_path),
            "preview_paths": [str(p) for p in preview_paths],
            "presentation": presentation,
            "template_path": str(template_path) if template_path else None,
            "design_tokens": design_tokens,
            "prompt_history": [prompt],
        }

        return GenerateResponse(
            presentation_id=presentation_id,
            presentation=presentation,
            download_url=f"/api/download/{presentation_id}",
            preview_urls=preview_urls,
            generation_mode=generation_mode,
            design_tokens=design_tokens,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Generation failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@router.post("/refine/{presentation_id}", response_model=RefineResponse)
async def refine(presentation_id: str, request: RefineRequest):
    """
    Refine an existing presentation based on user feedback.

    Sends the current IR + user instruction to the LLM for modification,
    rebuilds the PPTX, and re-renders previews.
    """
    entry = _presentations.get(presentation_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Presentation not found.")

    try:
        current = entry["presentation"]

        # Call LLM to refine
        updated = await refine_presentation(
            current=current,
            instruction=request.instruction,
        )

        # Rebuild PPTX + previews
        template_path = Path(entry["template_path"]) if entry.get("template_path") else None
        pptx_path, preview_paths = await _build_and_render(
            updated, presentation_id, template_path
        )

        preview_urls = [
            f"/api/preview/{presentation_id}/{i}"
            for i in range(len(preview_paths))
        ]

        # Update stored metadata
        entry["presentation"] = updated
        entry["pptx_path"] = str(pptx_path)
        entry["preview_paths"] = [str(p) for p in preview_paths]
        entry["prompt_history"].append(request.instruction)

        return RefineResponse(
            presentation_id=presentation_id,
            presentation=updated,
            download_url=f"/api/download/{presentation_id}",
            preview_urls=preview_urls,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Refinement failed")
        raise HTTPException(status_code=500, detail=f"Refinement failed: {e}")


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
