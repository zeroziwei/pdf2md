"""
PDF splitting utilities.
"""

from pdf2md.splitters.toc_splitter import TocSplitter, split_pdf_by_toc
from pdf2md.splitters.manual_splitter import (
    ManualSplitter,
    PageRange,
    split_pdf_by_ranges,
)

__all__ = [
    "TocSplitter",
    "split_pdf_by_toc",
    "ManualSplitter",
    "PageRange",
    "split_pdf_by_ranges",
]
