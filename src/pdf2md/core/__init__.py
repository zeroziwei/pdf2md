"""
Core domain models and configuration for PDF2MD.
"""

from pdf2md.core.document import Document, Segment
from pdf2md.core.config import ConversionConfig, ExtractorType

__all__ = [
    "Document",
    "Segment",
    "ConversionConfig",
    "ExtractorType",
]
