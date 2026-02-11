"""API request and response schemas."""

from typing import Optional

from pydantic import BaseModel, Field

from .slide import Presentation


class GenerateRequest(BaseModel):
    """Request body for the /api/generate endpoint."""

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=5000,
        description="User's description of the desired presentation.",
    )
    num_slides: Optional[int] = Field(
        None,
        ge=1,
        le=30,
        description="Number of slides to generate. If omitted, the LLM decides.",
    )


class GenerateResponse(BaseModel):
    """Response body from the /api/generate endpoint."""

    presentation_id: str = Field(
        ..., description="Unique ID for downloading the generated file."
    )
    presentation: Presentation = Field(
        ..., description="The structured presentation data."
    )
    download_url: str = Field(..., description="URL to download the .pptx file.")
    preview_urls: list[str] = Field(
        default_factory=list,
        description="URLs for slide preview images.",
    )
