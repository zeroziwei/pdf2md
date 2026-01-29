"""
PDF2MD - PDF to Markdown conversion tool with multiple extraction engines.
"""

__version__ = "0.1.0"

from pdf2md.core.document import Document, Segment
from pdf2md.core.config import ConversionConfig, ExtractorType

__all__ = [
    "Document",
    "Segment",
    "ConversionConfig",
    "ExtractorType",
]
