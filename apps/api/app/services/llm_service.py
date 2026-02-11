"""
LLM Service — multi-provider support for converting user prompts
into structured Presentation JSON conforming to the IR schema.

Supported providers: Gemini, OpenAI, Claude.
Configured via the LLM_PROVIDER environment variable.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from app.core.config import get_settings
from app.models.slide import DesignTokens, Presentation

logger = logging.getLogger(__name__)

# ── System prompt (shared across all providers) ─────────────────────────────

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

REFINE_SYSTEM_PROMPT = """\
You are SlideDeck AI, an expert presentation editor.

You will receive the current presentation JSON and a user instruction describing
what to change. Apply the requested changes and return the COMPLETE updated
presentation JSON.

## Rules
1. Return **only** valid JSON — no markdown fences, no commentary.
2. Preserve the same schema structure as the input.
3. Only modify what the user requested — keep everything else unchanged.
4. If the user asks to add slides, insert them in logical order.
5. If the user asks to change colors/fonts, apply changes consistently.
6. Always maintain valid positioning (canvas is 13.333 x 7.5 inches).
"""


def _build_user_prompt(
    prompt: str,
    num_slides: int | None,
    design_tokens: DesignTokens | None = None,
) -> str:
    """Build the user message for the LLM."""
    parts = [f"Create a presentation about:\n\n{prompt}"]

    if num_slides:
        parts.append(f"\nGenerate exactly {num_slides} slides.")

    if design_tokens:
        parts.append(
            f"\n\n## Design Constraints (from uploaded template/reference)\n"
            f"You MUST use these design tokens:\n"
            f"- Primary color: {design_tokens.primary_color}\n"
            f"- Secondary color: {design_tokens.secondary_color}\n"
            f"- Background color: {design_tokens.background_color}\n"
            f"- Heading font: {design_tokens.font_heading}\n"
            f"- Body font: {design_tokens.font_body}\n"
        )
        if design_tokens.extracted_colors:
            parts.append(
                f"- Available palette: {', '.join(design_tokens.extracted_colors[:10])}\n"
            )

    return "".join(parts)


def _build_refine_prompt(current_ir: Presentation, instruction: str) -> str:
    """Build the user message for a refinement request."""
    ir_json = current_ir.model_dump_json(indent=2)
    return (
        f"## Current Presentation JSON\n\n```json\n{ir_json}\n```\n\n"
        f"## User Instruction\n\n{instruction}\n\n"
        f"Apply the changes and return the complete updated JSON."
    )


def _parse_response(raw_text: str) -> Presentation:
    """Parse raw LLM text into a validated Presentation model."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM JSON: %s\nRaw: %s", e, text[:500])
        raise ValueError(f"LLM returned invalid JSON: {e}") from e

    presentation = Presentation.model_validate(data)
    logger.info(
        "Generated presentation '%s' with %d slides.",
        presentation.title,
        len(presentation.slides),
    )
    return presentation


# ── Provider implementations ────────────────────────────────────────────────


async def _generate_gemini(user_message: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    """Generate using Google Gemini."""
    import google.generativeai as genai

    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Please configure it in your .env file.")

    genai.configure(api_key=settings.GEMINI_API_KEY)

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    response = model.generate_content(user_message)
    return response.text


async def _generate_openai(user_message: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    """Generate using OpenAI GPT-4o."""
    from openai import AsyncOpenAI

    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set. Please configure it in your .env file.")

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content or ""


async def _generate_claude(user_message: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    """Generate using Anthropic Claude."""
    from anthropic import AsyncAnthropic

    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not set. Please configure it in your .env file.")

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        temperature=0.7,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message},
        ],
    )

    return response.content[0].text


# ── Provider dispatch ───────────────────────────────────────────────────────

_PROVIDERS: dict[str, callable] = {
    "gemini": _generate_gemini,
    "openai": _generate_openai,
    "claude": _generate_claude,
}


async def _call_provider(user_message: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    """Call the configured LLM provider."""
    settings = get_settings()
    provider_name = settings.LLM_PROVIDER.lower()

    provider_fn = _PROVIDERS.get(provider_name)
    if not provider_fn:
        raise ValueError(
            f"Unknown LLM provider: '{provider_name}'. "
            f"Supported: {', '.join(_PROVIDERS.keys())}"
        )

    logger.info("Calling %s with message (%d chars)...", provider_name, len(user_message))
    raw_text = await provider_fn(user_message, system_prompt)
    logger.debug("Raw %s response (first 500 chars): %s", provider_name, raw_text[:500])
    return raw_text


# ── Public API ──────────────────────────────────────────────────────────────


async def generate_presentation(
    prompt: str,
    num_slides: int | None = None,
    design_tokens: DesignTokens | None = None,
) -> Presentation:
    """
    Call the configured LLM provider to generate a Presentation from a prompt.

    Args:
        prompt: User's description of the desired presentation.
        num_slides: Optional — requested number of slides.
        design_tokens: Optional — extracted from template/reference .pptx.

    Returns:
        A validated Presentation model.
    """
    user_message = _build_user_prompt(prompt, num_slides, design_tokens)
    raw_text = await _call_provider(user_message, SYSTEM_PROMPT)
    return _parse_response(raw_text)


async def refine_presentation(
    current: Presentation,
    instruction: str,
) -> Presentation:
    """
    Refine an existing presentation based on user feedback.

    Args:
        current: The current presentation IR.
        instruction: What the user wants to change.

    Returns:
        A validated, updated Presentation model.
    """
    user_message = _build_refine_prompt(current, instruction)
    raw_text = await _call_provider(user_message, REFINE_SYSTEM_PROMPT)
    return _parse_response(raw_text)
