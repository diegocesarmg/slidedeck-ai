"""API request and response schemas."""

from typing import Optional

from pydantic import BaseModel, Field

from .slide import DesignTokens, GenerationMode, Presentation


class GenerateRequest(BaseModel):
    """
    Request body for the /api/generate endpoint.

    Note: When files are uploaded, the endpoint uses Form fields instead
    of a JSON body. This model is still used for validation and documentation.
    """

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
    generation_mode: GenerationMode = Field(
        GenerationMode.FROM_SCRATCH,
        description="Generation mode: from_scratch, template, or reference.",
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
    generation_mode: GenerationMode = Field(
        GenerationMode.FROM_SCRATCH,
        description="The mode used for generation.",
    )
    design_tokens: Optional[DesignTokens] = Field(
        None,
        description="Design tokens extracted from template/reference (if applicable).",
    )


class RefineRequest(BaseModel):
    """Request body for the /api/refine endpoint."""

    instruction: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="What the user wants to change about the presentation.",
    )


class RefineResponse(BaseModel):
    """Response body from the /api/refine endpoint."""

    presentation_id: str = Field(
        ..., description="Same presentation ID."
    )
    presentation: Presentation = Field(
        ..., description="The updated presentation data."
    )
    download_url: str = Field(..., description="URL to download the updated .pptx.")
    preview_urls: list[str] = Field(
        default_factory=list,
        description="URLs for updated slide preview images.",
    )
