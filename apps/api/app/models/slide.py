"""
Core data models for the SlideDeck AI Intermediate Representation (IR).

These Pydantic models are the **Source of Truth** for the entire system.
TypeScript interfaces are auto-generated from these definitions.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class HorizontalAlignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class VerticalAlignment(str, Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"


class LayoutType(str, Enum):
    TITLE = "title"
    TITLE_CONTENT = "title_content"
    TWO_COLUMN = "two_column"
    BLANK = "blank"
    SECTION_HEADER = "section_header"
    IMAGE_FULL = "image_full"


class GenerationMode(str, Enum):
    FROM_SCRATCH = "from_scratch"
    TEMPLATE = "template"
    REFERENCE = "reference"


# ── Design Tokens (extracted from template/reference) ────────────────────────


class DesignTokens(BaseModel):
    """Design tokens extracted from a template or reference .pptx."""

    primary_color: str = Field("#1a73e8", description="Primary brand color.")
    secondary_color: str = Field("#e8710a", description="Secondary accent color.")
    background_color: str = Field("#FFFFFF", description="Default background.")
    font_heading: str = Field("Calibri", description="Font for headings.")
    font_body: str = Field("Calibri", description="Font for body text.")
    layout_names: list[str] = Field(default_factory=list, description="Available layout names.")
    extracted_colors: list[str] = Field(default_factory=list, description="All colors found.")
    extracted_fonts: list[str] = Field(default_factory=list, description="All fonts found.")


# ── Element Models ───────────────────────────────────────────────────────────


class TextBox(BaseModel):
    """A text box element on a slide."""

    type: Literal["text"] = "text"

    # Content
    content: str = Field(..., description="The text content of the box.")
    is_title: bool = Field(False, description="Whether this is the slide title.")

    # Position & Size (inches from top-left)
    x: float = Field(0.5, ge=0, description="X position in inches.")
    y: float = Field(0.5, ge=0, description="Y position in inches.")
    width: float = Field(9.0, gt=0, description="Width in inches.")
    height: float = Field(1.0, gt=0, description="Height in inches.")

    # Typography
    font_name: str = Field("Calibri", description="Font family name.")
    font_size: int = Field(18, ge=6, le=96, description="Font size in points.")
    font_bold: bool = False
    font_italic: bool = False
    font_color: str = Field("#333333", description="Hex color code for the text.")

    # Alignment
    alignment: HorizontalAlignment = HorizontalAlignment.LEFT
    vertical_alignment: VerticalAlignment = VerticalAlignment.TOP


class ImageElement(BaseModel):
    """An image element on a slide."""

    type: Literal["image"] = "image"

    # Source
    url: Optional[str] = Field(None, description="URL to download the image from.")
    path: Optional[str] = Field(None, description="Local path to the image file.")
    alt_text: str = Field("", description="Accessibility alt text.")

    # Position & Size (inches)
    x: float = Field(1.0, ge=0, description="X position in inches.")
    y: float = Field(1.5, ge=0, description="Y position in inches.")
    width: float = Field(8.0, gt=0, description="Width in inches.")
    height: float = Field(5.0, gt=0, description="Height in inches.")


class ChartElement(BaseModel):
    """A chart element on a slide (placeholder — renders as a styled table)."""

    type: Literal["chart"] = "chart"

    chart_type: ChartType = ChartType.BAR
    title: str = Field("", description="Chart title.")

    # Data
    categories: list[str] = Field(default_factory=list, description="X-axis labels.")
    series: list[dict] = Field(
        default_factory=list,
        description='Data series, each dict has "name" and "values" keys.',
    )

    # Position & Size (inches)
    x: float = Field(1.0, ge=0)
    y: float = Field(1.5, ge=0)
    width: float = Field(8.0, gt=0)
    height: float = Field(5.0, gt=0)


# ── Discriminated Union ──────────────────────────────────────────────────────

SlideElement = TextBox | ImageElement | ChartElement


# ── Slide & Presentation ─────────────────────────────────────────────────────


class Slide(BaseModel):
    """A single slide in the presentation."""

    layout: LayoutType = Field(
        LayoutType.TITLE_CONTENT, description="Layout template for this slide."
    )
    background_color: str = Field(
        "#FFFFFF", description="Hex color code for the slide background."
    )
    elements: list[SlideElement] = Field(
        default_factory=list, description="Ordered list of elements on the slide."
    )
    speaker_notes: str = Field("", description="Speaker notes for this slide.")


class ThemeSettings(BaseModel):
    """Global theme settings for the presentation."""

    primary_color: str = Field("#1a73e8", description="Primary brand color.")
    secondary_color: str = Field("#e8710a", description="Secondary accent color.")
    background_color: str = Field("#FFFFFF", description="Default background.")
    font_heading: str = Field("Calibri", description="Font for headings.")
    font_body: str = Field("Calibri", description="Font for body text.")


class Presentation(BaseModel):
    """Root model — the complete presentation definition."""

    title: str = Field(..., description="Presentation title.")
    subtitle: str = Field("", description="Presentation subtitle.")
    author: str = Field("SlideDeck AI", description="Author name.")
    theme: ThemeSettings = Field(default_factory=ThemeSettings)
    slides: list[Slide] = Field(
        default_factory=list, description="Ordered list of slides."
    )
