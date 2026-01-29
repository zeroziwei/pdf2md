"""
PDF splitting based on Table of Contents (TOC).

Refactored from pdf_split_by_toc.py to fit the new modular architecture.
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Optional, List

from pdf2md.core.document import Document, Segment, SegmentStatus


def sanitize_filename(filename: str) -> str:
    """
    Clean filename by removing illegal characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace illegal characters
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, "_", filename)
    # Remove leading/trailing spaces
    filename = filename.strip()
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    return filename


class TocSplitter:
    """
    Splits PDF documents based on their table of contents.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the TOC splitter.

        Args:
            output_dir: Output directory for split PDFs (optional)
        """
        self.output_dir = Path(output_dir) if output_dir else None

    def has_toc(self, pdf_path: Path) -> bool:
        """
        Check if PDF has a table of contents.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if TOC exists, False otherwise
        """
        try:
            doc = fitz.open(pdf_path)
            toc = doc.get_toc()
            has_toc = len(toc) > 0
            doc.close()
            return has_toc
        except Exception:
            return False

    def get_toc(self, pdf_path: Path) -> List[tuple]:
        """
        Get the table of contents from a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of (level, title, page) tuples

        Raises:
            ValueError: If PDF has no TOC
        """
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()
        doc.close()

        if not toc:
            raise ValueError("PDF has no table of contents")

        return toc

    def create_document_from_toc(
        self, pdf_path: Path, split_level: int = 1
    ) -> Document:
        """
        Create a Document with segments based on TOC.

        Args:
            pdf_path: Path to the PDF file
            split_level: TOC level to split on (1 = chapters, 2 = sections, etc.)

        Returns:
            Document object with segments

        Raises:
            ValueError: If PDF has no TOC
        """
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()

        if not toc:
            doc.close()
            raise ValueError("PDF has no table of contents")

        # Create Document object
        document = Document(
            original_filename=pdf_path.name,
            file_path=pdf_path,
            title=pdf_path.stem,
            total_pages=doc.page_count,
            has_toc=True,
        )

        # Parse TOC and create segments
        segments = []
        for i, (level, title, start_page) in enumerate(toc):
            if level == split_level:
                # Find end page
                end_page = doc.page_count
                for j in range(i + 1, len(toc)):
                    next_level, _, next_page = toc[j]
                    if next_level <= split_level:
                        end_page = next_page - 1
                        break

                segment = Segment(
                    title=title,
                    start_page=start_page,
                    end_page=end_page,
                    level=level,
                    status=SegmentStatus.READY,
                )
                segments.append(segment)

        doc.close()

        # Add all segments to document
        for segment in segments:
            document.add_segment(segment)

        return document

    def split_and_save(
        self,
        pdf_path: Path,
        output_dir: Optional[Path] = None,
        split_level: int = 1,
    ) -> Document:
        """
        Split PDF by TOC and save segment files.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory (overrides instance output_dir)
            split_level: TOC level to split on

        Returns:
            Document object with segments and saved files

        Raises:
            ValueError: If PDF has no TOC
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir) if output_dir else self.output_dir

        if output_dir is None:
            output_dir = pdf_path.parent / f"{pdf_path.stem}_chapters"

        output_dir.mkdir(parents=True, exist_ok=True)

        # Create document with segments
        document = self.create_document_from_toc(pdf_path, split_level)

        # Open PDF for splitting
        doc = fitz.open(pdf_path)

        # Save each segment as a separate PDF
        for idx, segment in enumerate(document.segments, 1):
            safe_title = sanitize_filename(segment.title)
            output_filename = f"{idx:02d}_{safe_title}.pdf"
            output_path = output_dir / output_filename

            # Create new PDF and copy pages
            new_doc = fitz.open()
            new_doc.insert_pdf(
                doc,
                from_page=segment.start_page - 1,  # 0-indexed
                to_page=segment.end_page - 1,
            )
            new_doc.save(output_path)
            new_doc.close()

            # Store file path in segment metadata
            segment.metadata["pdf_path"] = str(output_path)
            segment.metadata["output_filename"] = output_filename

        doc.close()

        # Store output directory in document metadata
        document.metadata["output_dir"] = str(output_dir)
        document.metadata["split_level"] = split_level

        return document


def split_pdf_by_toc(
    pdf_path: Path,
    output_dir: Optional[Path] = None,
    split_level: int = 1,
) -> Document:
    """
    Convenience function to split PDF by TOC.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory
        split_level: TOC level to split on (default: 1 for chapters)

    Returns:
        Document object with segments
    """
    splitter = TocSplitter(output_dir)
    return splitter.split_and_save(pdf_path, output_dir, split_level)
