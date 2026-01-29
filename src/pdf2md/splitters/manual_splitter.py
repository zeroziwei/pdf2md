"""
Manual PDF splitting by page ranges.

Allows users to specify custom page ranges for splitting PDFs.
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Optional, List, Tuple

from pdf2md.core.document import Document, Segment, SegmentStatus


class PageRange:
    """
    Represents a page range with start and end pages.
    """

    def __init__(self, start: int, end: int, title: Optional[str] = None):
        """
        Initialize a page range.

        Args:
            start: Starting page (1-indexed, inclusive)
            end: Ending page (1-indexed, inclusive)
            title: Optional title for the range
        """
        if start < 1:
            raise ValueError("Start page must be >= 1")
        if end < start:
            raise ValueError("End page must be >= start page")

        self.start = start
        self.end = end
        self.title = title or f"Pages {start}-{end}"

    @property
    def page_count(self) -> int:
        """Get the number of pages in this range."""
        return self.end - self.start + 1

    def __repr__(self) -> str:
        return f"PageRange({self.start}-{self.end}: {self.title})"


class ManualSplitter:
    """
    Splits PDF documents by manually specified page ranges.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the manual splitter.

        Args:
            output_dir: Output directory for split PDFs (optional)
        """
        self.output_dir = Path(output_dir) if output_dir else None

    @staticmethod
    def parse_page_ranges(range_str: str) -> List[PageRange]:
        """
        Parse page range string into PageRange objects.

        Supported formats:
        - "1-10" - single range
        - "1-10, 15-20" - multiple ranges
        - "1-10, 15-20, 25-30" - multiple ranges
        - "5" - single page (treated as 5-5)

        Args:
            range_str: Page range string

        Returns:
            List of PageRange objects

        Raises:
            ValueError: If format is invalid
        """
        ranges = []
        parts = [p.strip() for p in range_str.split(",")]

        for part in parts:
            if not part:
                continue

            # Match "start-end" or single page "N"
            match = re.match(r"^(\d+)(?:-(\d+))?$", part)
            if not match:
                raise ValueError(f"Invalid page range format: {part}")

            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else start

            ranges.append(PageRange(start, end))

        return ranges

    @staticmethod
    def validate_ranges(ranges: List[PageRange], total_pages: int) -> None:
        """
        Validate page ranges against total page count.

        Args:
            ranges: List of page ranges
            total_pages: Total pages in the PDF

        Raises:
            ValueError: If any range is invalid
        """
        for range_obj in ranges:
            if range_obj.start > total_pages:
                raise ValueError(
                    f"Start page {range_obj.start} exceeds total pages {total_pages}"
                )
            if range_obj.end > total_pages:
                raise ValueError(
                    f"End page {range_obj.end} exceeds total pages {total_pages}"
                )

    def create_document_from_ranges(
        self,
        pdf_path: Path,
        ranges: List[PageRange],
    ) -> Document:
        """
        Create a Document with segments based on page ranges.

        Args:
            pdf_path: Path to the PDF file
            ranges: List of page ranges

        Returns:
            Document object with segments

        Raises:
            ValueError: If ranges are invalid
        """
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()

        # Validate ranges
        self.validate_ranges(ranges, total_pages)

        # Create Document object
        document = Document(
            original_filename=pdf_path.name,
            file_path=pdf_path,
            title=pdf_path.stem,
            total_pages=total_pages,
            has_toc=False,
        )

        # Create segments from ranges
        for range_obj in ranges:
            segment = Segment(
                title=range_obj.title,
                start_page=range_obj.start,
                end_page=range_obj.end,
                level=1,  # All manual ranges are top level
                status=SegmentStatus.READY,
            )
            document.add_segment(segment)

        return document

    def split_and_save(
        self,
        pdf_path: Path,
        ranges: List[PageRange],
        output_dir: Optional[Path] = None,
    ) -> Document:
        """
        Split PDF by page ranges and save segment files.

        Args:
            pdf_path: Path to the PDF file
            ranges: List of page ranges
            output_dir: Output directory (overrides instance output_dir)

        Returns:
            Document object with segments and saved files
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir) if output_dir else self.output_dir

        if output_dir is None:
            output_dir = pdf_path.parent / f"{pdf_path.stem}_segments"

        output_dir.mkdir(parents=True, exist_ok=True)

        # Create document with segments
        document = self.create_document_from_ranges(pdf_path, ranges)

        # Open PDF for splitting
        doc = fitz.open(pdf_path)

        # Save each segment as a separate PDF
        for idx, segment in enumerate(document.segments, 1):
            # Create safe filename from title
            safe_title = re.sub(r'[<>:"/\\|?*]', "_", segment.title)
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
        document.metadata["split_mode"] = "manual"

        return document


def split_pdf_by_ranges(
    pdf_path: Path,
    range_str: str,
    output_dir: Optional[Path] = None,
) -> Document:
    """
    Convenience function to split PDF by page range string.

    Args:
        pdf_path: Path to the PDF file
        range_str: Page range string (e.g., "1-10, 15-20, 25-30")
        output_dir: Output directory

    Returns:
        Document object with segments
    """
    splitter = ManualSplitter(output_dir)
    ranges = ManualSplitter.parse_page_ranges(range_str)
    return splitter.split_and_save(pdf_path, ranges, output_dir)
