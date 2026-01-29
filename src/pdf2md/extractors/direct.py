"""
Direct text extraction from PDFs with text layers.

Uses PyMuPDF to extract text directly and convert to Markdown format.
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Optional, List, Dict

from pdf2md.core.document import Segment
from pdf2md.core.config import ConversionConfig
from pdf2md.extractors.base import BaseExtractor


class DirectExtractor(BaseExtractor):
    """
    Extractor for PDFs with extractable text layers.

    Uses PyMuPDF's text extraction capabilities to convert PDF to Markdown.
    Best for standard PDFs with good text layers.
    """

    def __init__(self, config: ConversionConfig):
        """
        Initialize the direct extractor.

        Args:
            config: Conversion configuration
        """
        super().__init__(config)

    def can_handle(self, pdf_path: Path) -> bool:
        """
        Check if PDF has extractable text.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if text can be extracted, False otherwise
        """
        return self.is_text_extractable(pdf_path)

    def extract(self, pdf_path: Path, segment: Optional[Segment] = None) -> str:
        """
        Extract text from PDF and convert to Markdown.

        Args:
            pdf_path: Path to the PDF file
            segment: Optional segment info for page range

        Returns:
            Markdown formatted text
        """
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

        # Extract text from each page
        for page_num in range(start_page, end_page + 1):
            page = doc[page_num]
            page_markdown = self._extract_page_as_markdown(page, page_num + 1)
            if page_markdown:
                markdown_parts.append(page_markdown)
                markdown_parts.append("\n\n")

        doc.close()

        return "".join(markdown_parts)

    def _extract_page_as_markdown(self, page: fitz.Page, page_num: int) -> str:
        """
        Extract text from a single page and format as Markdown.

        Args:
            page: PyMuPDF page object
            page_num: Page number (1-indexed, for reference)

        Returns:
            Markdown formatted text for the page
        """
        # Get text blocks with position information
        blocks = page.get_text("dict")["blocks"]

        markdown_parts = []

        for block in blocks:
            if block["type"] == 0:  # Text block
                block_markdown = self._process_text_block(block)
                if block_markdown:
                    markdown_parts.append(block_markdown)

        return "\n\n".join(markdown_parts)

    def _process_text_block(self, block: Dict) -> str:
        """
        Process a text block and convert to Markdown.

        Args:
            block: Text block dictionary from PyMuPDF

        Returns:
            Markdown formatted text
        """
        lines = []

        for line in block.get("lines", []):
            line_text = ""
            line_spans = line.get("spans", [])

            for span in line_spans:
                text = span.get("text", "").strip()
                if not text:
                    continue

                # Get font information
                font_size = span.get("size", 12)
                font_flags = span.get("flags", 0)

                # Check if bold (flag & 16)
                is_bold = (font_flags & 16) != 0
                # Check if italic (flag & 2)
                is_italic = (font_flags & 2) != 0

                # Apply formatting
                if is_bold and is_italic:
                    text = f"***{text}***"
                elif is_bold:
                    text = f"**{text}**"
                elif is_italic:
                    text = f"*{text}*"

                line_text += text + " "

            line_text = line_text.strip()
            if line_text:
                # Detect if line is a heading based on font size or content
                if self._is_likely_heading(line_text, block):
                    # Try to determine heading level
                    level = self._determine_heading_level(block)
                    line_text = f"{'#' * level} {line_text}"

                lines.append(line_text)

        # Join lines with appropriate spacing
        text = "\n".join(lines)

        # Detect and format lists
        text = self._format_lists(text)

        return text

    def _is_likely_heading(self, text: str, block: Dict) -> bool:
        """
        Determine if a text block is likely a heading.

        Args:
            text: Text content
            block: Block dictionary

        Returns:
            True if likely a heading
        """
        # Check for common heading patterns
        heading_patterns = [
            r"^Chapter \d+",
            r"^\d+\.?\s+[A-Z]",  # "1. Introduction" or "1 Introduction"
            r"^[A-Z][A-Z\s]{3,}$",  # ALL CAPS short text
        ]

        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True

        # Check if text is short and starts with capital
        if len(text) < 100 and text and text[0].isupper() and not text.endswith("."):
            # Check if font size is larger than average
            avg_size = 12
            if block.get("lines"):
                first_span = block["lines"][0].get("spans", [{}])[0]
                font_size = first_span.get("size", 12)
                if font_size > avg_size * 1.2:
                    return True

        return False

    def _determine_heading_level(self, block: Dict) -> int:
        """
        Determine heading level (1-6) based on block properties.

        Args:
            block: Block dictionary

        Returns:
            Heading level (1-6)
        """
        # Use font size to determine level
        if block.get("lines"):
            first_span = block["lines"][0].get("spans", [{}])[0]
            font_size = first_span.get("size", 12)

            # Map font sizes to heading levels
            if font_size >= 24:
                return 1
            elif font_size >= 20:
                return 2
            elif font_size >= 16:
                return 3
            elif font_size >= 14:
                return 4
            else:
                return 5

        return 2  # Default to h2

    def _format_lists(self, text: str) -> str:
        """
        Detect and format lists in text.

        Args:
            text: Input text

        Returns:
            Text with formatted lists
        """
        lines = text.split("\n")
        formatted_lines = []

        for line in lines:
            # Detect numbered lists: "1. Item", "1) Item", "(1) Item"
            if re.match(r"^\s*\d+[\.)]\s+", line):
                line = re.sub(r"^\s*(\d+)[\.)]\s+", r"\1. ", line)
            # Detect bullet lists: "• Item", "- Item", "* Item"
            elif re.match(r"^\s*[•\-\*]\s+", line):
                line = re.sub(r"^\s*[•\-\*]\s+", r"- ", line)

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def extract_with_images(
        self, pdf_path: Path, segment: Optional[Segment] = None
    ) -> tuple[str, List[Path]]:
        """
        Extract text and images from PDF.

        Args:
            pdf_path: Path to the PDF file
            segment: Optional segment info

        Returns:
            Tuple of (markdown text, list of image paths)
        """
        doc = fitz.open(pdf_path)

        # Determine page range
        if segment:
            start_page = segment.start_page - 1
            end_page = segment.end_page - 1
        else:
            start_page = 0
            end_page = len(doc) - 1

        markdown_parts = []
        image_paths = []

        # Create images directory
        output_dir = self.config.output_dir / "images"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Add title if segment has one
        if segment and segment.title:
            markdown_parts.append(f"# {segment.title}\n\n")

        # Extract text and images from each page
        for page_num in range(start_page, end_page + 1):
            page = doc[page_num]

            # Extract text
            page_markdown = self._extract_page_as_markdown(page, page_num + 1)
            if page_markdown:
                markdown_parts.append(page_markdown)

            # Extract images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Save image
                image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                image_path = output_dir / image_filename

                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)

                image_paths.append(image_path)

                # Add image reference to markdown
                markdown_parts.append(
                    f"\n\n![Image]({image_path.relative_to(self.config.output_dir)})\n\n"
                )

        doc.close()

        return "".join(markdown_parts), image_paths
