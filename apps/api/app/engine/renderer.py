"""
Renderer — converts .pptx → PNG using LibreOffice headless.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def render_to_images(pptx_path: Path, output_dir: Path | None = None) -> list[Path]:
    """
    Convert a .pptx file to a series of PNG images using LibreOffice.

    Args:
        pptx_path: Path to the .pptx file.
        output_dir: Directory to save the PNGs. Defaults to a temp directory.

    Returns:
        Sorted list of paths to the generated PNG files.
    """
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="slidedeck-preview-"))
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Convert PPTX → PDF
        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_dir),
                str(pptx_path),
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )

        pdf_path = output_dir / f"{pptx_path.stem}.pdf"

        if not pdf_path.exists():
            logger.error("LibreOffice did not produce a PDF file.")
            return []

        # Step 2: Convert PDF → PNG images (one per page)
        # Use LibreOffice to convert to individual PNGs
        # We first convert to individual PNG pages via pdftoppm if available,
        # otherwise fallback to a single PNG
        try:
            subprocess.run(
                [
                    "pdftoppm",
                    "-png",
                    "-r", "200",
                    str(pdf_path),
                    str(output_dir / "slide"),
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except FileNotFoundError:
            # pdftoppm not available — fallback: one PNG per PDF via libreoffice
            logger.info("pdftoppm not found, falling back to LibreOffice PNG export.")
            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "png",
                    "--outdir", str(output_dir),
                    str(pdf_path),
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )

        # Collect all generated PNGs
        png_files = sorted(output_dir.glob("*.png"))
        logger.info("Rendered %d slide images to %s", len(png_files), output_dir)
        return png_files

    except subprocess.CalledProcessError as e:
        logger.error(
            "Rendering failed: %s\nstdout: %s\nstderr: %s",
            e, e.stdout, e.stderr,
        )
        return []
    except Exception as e:
        logger.error("Unexpected rendering error: %s", e)
        return []
