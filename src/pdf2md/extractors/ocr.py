"""
OCR-based extraction for scanned PDFs.

Uses PaddleOCR for text recognition with support for multiple languages.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image
import io

from pdf2md.core.document import Segment
from pdf2md.core.config import ConversionConfig, OcrConfig
from pdf2md.extractors.base import BaseExtractor


class OcrExtractor(BaseExtractor):
    """
    Extractor for scanned PDFs using OCR.

    Uses PaddleOCR to recognize text from images and convert to Markdown.
    Best for scanned documents and image-based PDFs.
    """

    def __init__(self, config: ConversionConfig):
        """
        Initialize the OCR extractor.

        Args:
            config: Conversion configuration with OCR settings
        """
        super().__init__(config)
        self.ocr_config = config.ocr_config
        self._ocr_engine = None

    def _init_ocr_engine(self):
        """Lazy initialization of OCR engine."""
        if self._ocr_engine is None:
            try:
                from paddleocr import PaddleOCR

                self._ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.ocr_config.lang,
                    use_gpu=self.ocr_config.use_gpu,
                    det_db_thresh=self.ocr_config.det_db_thresh,
                    det_db_box_thresh=self.ocr_config.det_db_box_thresh,
                    show_log=False,
                )
            except ImportError:
                raise ImportError(
                    "PaddleOCR is not installed. Install it with: pip install paddleocr"
                )

    def can_handle(self, pdf_path: Path) -> bool:
        """
        Check if PDF is image-based (needs OCR).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if PDF is image-based, False if text-extractable
        """
        # If text is not extractable, we need OCR
        return not self.is_text_extractable(pdf_path)

    def extract(
        self, pdf_path: Path, segment: Optional[Segment] = None
    ) -> str:
        """
        Extract text from PDF using OCR and convert to Markdown.

        Args:
            pdf_path: Path to the PDF file
            segment: Optional segment info for page range

        Returns:
            Markdown formatted text
        """
        self._init_ocr_engine()

        doc = fitz.open(pdf_path)

        # Determine page range
        if segment:
            start_page = segment.start_page - 1  # 0-indexed
            end_page = segment.end_page - 1
        else:
            start_page = 0
            end_page = len(doc) - 1

        markdown_parts = []

        # Add title if segment has one
        if segment and segment.title:
            markdown_parts.append(f"# {segment.title}\n\n")

        # Process each page
        for page_num in range(start_page, end_page + 1):
            page = doc[page_num]
            page_markdown = self._extract_page_with_ocr(page, page_num + 1)
            if page_markdown:
                markdown_parts.append(page_markdown)
                markdown_parts.append("\n\n")

        doc.close()

        return "".join(markdown_parts)

    def _extract_page_with_ocr(self, page: fitz.Page, page_num: int) -> str:
        """
        Extract text from a single page using OCR.

        Args:
            page: PyMuPDF page object
            page_num: Page number (1-indexed)

        Returns:
            Markdown formatted text for the page
        """
        # Render page to image at higher DPI for better OCR
        zoom = 2  # 2x zoom for better quality
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        # Run OCR
        result = self._ocr_engine.ocr(img_data, cls=True)

        if not result or not result[0]:
            return ""

        # Process OCR results
        markdown = self._process_ocr_result(result[0])

        return markdown

    def _process_ocr_result(self, ocr_result: List[Any]) -> str:
        """
        Process OCR result and convert to Markdown.

        Args:
            ocr_result: OCR result from PaddleOCR

        Returns:
            Markdown formatted text
        """
        if not ocr_result:
            return ""

        # Group text by vertical position (lines)
        lines = []
        current_line = []
        last_y = None
        line_threshold = 20  # pixels difference to consider same line

        for item in ocr_result:
            if not item or len(item) < 2:
                continue

            box = item[0]  # Bounding box
            text_info = item[1]  # (text, confidence)
            text = text_info[0] if isinstance(text_info, tuple) else text_info

            if not text.strip():
                continue

            # Get vertical position (average y of top-left and bottom-left)
            y_pos = (box[0][1] + box[3][1]) / 2

            if last_y is None or abs(y_pos - last_y) < line_threshold:
                # Same line
                current_line.append((box[0][0], text))  # (x_position, text)
                last_y = y_pos
            else:
                # New line
                if current_line:
                    # Sort by x position and join
                    current_line.sort(key=lambda x: x[0])
                    line_text = " ".join(t[1] for t in current_line)
                    lines.append(line_text)
                current_line = [(box[0][0], text)]
                last_y = y_pos

        # Add last line
        if current_line:
            current_line.sort(key=lambda x: x[0])
            line_text = " ".join(t[1] for t in current_line)
            lines.append(line_text)

        # Format as markdown
        markdown_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect headings (heuristic: short lines with capitals)
            if self._is_likely_heading_ocr(line):
                # Determine heading level
                level = 2  # Default to h2
                if len(line) < 30 and line.isupper():
                    level = 1
                elif len(line) < 50:
                    level = 2
                else:
                    level = 3

                markdown_lines.append(f"{'#' * level} {line}")
            else:
                markdown_lines.append(line)

        return "\n\n".join(markdown_lines)

    def _is_likely_heading_ocr(self, text: str) -> bool:
        """
        Determine if text is likely a heading based on OCR output.

        Args:
            text: Text content

        Returns:
            True if likely a heading
        """
        import re

        # Check for common heading patterns
        heading_patterns = [
            r"^Chapter \d+",
            r"^\d+\.?\s+[A-Z]",
            r"^[A-Z][A-Z\s]{3,}$",  # ALL CAPS
        ]

        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True

        # Short text starting with capital and no ending period
        if (
            len(text) < 80
            and text
            and text[0].isupper()
            and not text.endswith(".")
        ):
            return True

        return False

    def extract_with_layout(
        self, pdf_path: Path, segment: Optional[Segment] = None
    ) -> str:
        """
        Extract text with layout analysis for better structure detection.

        Args:
            pdf_path: Path to the PDF file
            segment: Optional segment info

        Returns:
            Markdown formatted text with better layout
        """
        if not self.ocr_config.enable_layout_analysis:
            return self.extract(pdf_path, segment)

        try:
            from paddleocr import PPStructure

            # Initialize layout analysis
            table_engine = PPStructure(
                show_log=False,
                use_gpu=self.ocr_config.use_gpu,
                lang=self.ocr_config.lang,
            )

            doc = fitz.open(pdf_path)

            # Determine page range
            if segment:
                start_page = segment.start_page - 1
                end_page = segment.end_page - 1
            else:
                start_page = 0
                end_page = len(doc) - 1

            markdown_parts = []

            # Add title if segment has one
            if segment and segment.title:
                markdown_parts.append(f"# {segment.title}\n\n")

            # Process each page with layout analysis
            for page_num in range(start_page, end_page + 1):
                page = doc[page_num]

                # Render page to image
                zoom = 2
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")

                # Run layout analysis
                result = table_engine(img_data)

                # Process structured result
                for item in result:
                    item_type = item.get("type", "text")

                    if item_type == "text":
                        text = item.get("res", {}).get("text", "")
                        if text:
                            markdown_parts.append(text)
                            markdown_parts.append("\n\n")

                    elif item_type == "table":
                        # Format table as markdown
                        table_html = item.get("res", {}).get("html", "")
                        if table_html:
                            markdown_parts.append(
                                self._html_table_to_markdown(table_html)
                            )
                            markdown_parts.append("\n\n")

                    elif item_type == "figure":
                        markdown_parts.append("*[Figure]*\n\n")

            doc.close()

            return "".join(markdown_parts)

        except ImportError:
            # Fallback to basic OCR if layout analysis not available
            return self.extract(pdf_path, segment)

    def _html_table_to_markdown(self, html_table: str) -> str:
        """
        Convert HTML table to Markdown table.

        Args:
            html_table: HTML table string

        Returns:
            Markdown table
        """
        # Simple conversion (can be enhanced with html parser)
        # For now, just wrap in code block
        return f"```\n{html_table}\n```"
