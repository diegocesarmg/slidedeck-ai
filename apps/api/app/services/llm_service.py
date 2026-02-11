"""
LLM Service — uses Google Gemini to convert a user prompt into
a structured Presentation JSON that matches our IR schema.
"""

from __future__ import annotations

import json
import logging

import google.generativeai as genai

from app.core.config import get_settings
from app.models.slide import Presentation

logger = logging.getLogger(__name__)

# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are SlideDeck AI, an expert presentation designer.

Your job is to convert a user's description into a structured JSON object
that represents a professional PowerPoint presentation.

## Output Rules
1. Return **only** valid JSON — no markdown fences, no commentary.
2. The JSON must conform exactly to this schema:

```
{
  "title": "string",
  "subtitle": "string (optional)",
  "author": "SlideDeck AI",
  "theme": {
    "primary_color": "#hex",
    "secondary_color": "#hex",
    "background_color": "#hex",
    "font_heading": "string",
    "font_body": "string"
  },
  "slides": [
    {
      "layout": "title | title_content | two_column | blank | section_header | image_full",
      "background_color": "#hex",
      "elements": [
        {
          "type": "text",
          "content": "string",
          "is_title": true/false,
          "x": float, "y": float, "width": float, "height": float,
          "font_name": "string",
          "font_size": int,
          "font_bold": bool,
          "font_italic": bool,
          "font_color": "#hex",
          "alignment": "left | center | right",
          "vertical_alignment": "top | middle | bottom"
        }
      ],
      "speaker_notes": "string (optional)"
    }
  ]
}
```

3. Use only "text" type elements for now (images/charts will be added later).
4. Make the presentation visually appealing with proper spacing, font sizes, and colors.
5. Use the first slide as a title slide with large title text and optional subtitle.
6. Use section headers between major topics.
7. Keep bullet points concise (max ~8 words per bullet).
8. For slide positioning, the canvas is 13.333 x 7.5 inches.
9. Vary background colors per slide for visual interest (keep text readable).
10. Always include speaker notes with key talking points.
"""


def _build_user_prompt(prompt: str, num_slides: int | None) -> str:
    """Build the user message for the LLM."""
    slide_instruction = ""
    if num_slides:
        slide_instruction = f"\n\nGenerate exactly {num_slides} slides."
    return f"Create a presentation about:\n\n{prompt}{slide_instruction}"


async def generate_presentation(
    prompt: str,
    num_slides: int | None = None,
) -> Presentation:
    """
    Call the Gemini API to generate a Presentation from a user prompt.

    Args:
        prompt: User's description of the desired presentation.
        num_slides: Optional — requested number of slides.

    Returns:
        A validated Presentation model.
    """
    settings = get_settings()

    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. Please configure it in your .env file."
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    user_message = _build_user_prompt(prompt, num_slides)
    logger.info("Sending prompt to Gemini: %s...", user_message[:100])

    response = model.generate_content(user_message)

    # Parse JSON from the response
    raw_text = response.text
    logger.debug("Raw LLM response (first 500 chars): %s", raw_text[:500])

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM JSON: %s", e)
        raise ValueError(f"LLM returned invalid JSON: {e}") from e

    # Validate against our Pydantic model
    presentation = Presentation.model_validate(data)
    logger.info(
        "Generated presentation '%s' with %d slides.",
        presentation.title,
        len(presentation.slides),
    )
    return presentation
