"""
Base extractor interface and router for conversion engines.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF

from pdf2md.core.document import Segment
from pdf2md.core.config import ConversionConfig, ExtractorType


class BaseExtractor(ABC):
    """
    Abstract base class for all PDF extraction engines.

    All extractors must implement the extract method and can_handle method.
    """

    def __init__(self, config: ConversionConfig):
        """
        Initialize the extractor with configuration.

        Args:
            config: Conversion configuration
        """
        self.config = config

    @abstractmethod
    def extract(self, pdf_path: Path, segment: Optional[Segment] = None) -> str:
        """
        Extract text from PDF and convert to Markdown.

        Args:
            pdf_path: Path to the PDF file
            segment: Optional segment info (for page range extraction)

        Returns:
            Markdown formatted text

        Raises:
            Exception: If extraction fails
        """
        pass

    @abstractmethod
    def can_handle(self, pdf_path: Path) -> bool:
        """
        Check if this extractor can handle the given PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if this extractor can handle the PDF, False otherwise
        """
        pass

    @staticmethod
    def is_text_extractable(pdf_path: Path, sample_pages: int = 3) -> bool:
        """
        Check if PDF has extractable text by sampling pages.

        Args:
            pdf_path: Path to the PDF file
            sample_pages: Number of pages to sample

        Returns:
            True if text can be extracted, False if it's image-based
        """
        try:
            doc = fitz.open(pdf_path)
            pages_to_check = min(sample_pages, len(doc))

            text_found = 0
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text().strip()
                if len(text) > 50:  # Threshold: at least 50 chars
                    text_found += 1

            doc.close()

            # If more than half of sampled pages have text, consider it text-extractable
            return text_found > pages_to_check / 2

        except Exception:
            return False


class ExtractorRouter:
    """
    Routes PDF extraction to the appropriate engine based on configuration and PDF type.
    """

    def __init__(self, config: ConversionConfig):
        """
        Initialize the router with configuration.

        Args:
            config: Conversion configuration
        """
        self.config = config
        self._extractors = {}

    def register_extractor(
        self, extractor_type: ExtractorType, extractor: BaseExtractor
    ):
        """
        Register an extractor for a specific type.

        Args:
            extractor_type: Type of extractor
            extractor: Extractor instance
        """
        self._extractors[extractor_type] = extractor

    def get_extractor(self, pdf_path: Path) -> BaseExtractor:
        """
        Get the appropriate extractor for a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Appropriate extractor instance

        Raises:
            ValueError: If no suitable extractor is found
        """
        # If extractor type is specified (not AUTO), use it
        if self.config.extractor_type != ExtractorType.AUTO:
            extractor = self._extractors.get(self.config.extractor_type)
            if extractor:
                return extractor
            raise ValueError(f"Extractor {self.config.extractor_type} not available")

        # AUTO mode: detect best extractor
        # Priority: Direct → OCR → MinerU
        for extractor_type in [
            ExtractorType.DIRECT,
            ExtractorType.OCR,
            ExtractorType.MINERU,
        ]:
            extractor = self._extractors.get(extractor_type)
            if extractor and extractor.can_handle(pdf_path):
                return extractor

        raise ValueError("No suitable extractor found for PDF")

    def extract(self, pdf_path: Path, segment: Optional[Segment] = None) -> str:
        """
        Extract text from PDF using the appropriate engine.

        Args:
            pdf_path: Path to the PDF file
            segment: Optional segment info

        Returns:
            Markdown formatted text
        """
        extractor = self.get_extractor(pdf_path)
        return extractor.extract(pdf_path, segment)
