"""
Configuration classes for PDF2MD conversion.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any


class ExtractorType(str, Enum):
    """Types of extraction engines available."""

    AUTO = "auto"  # Auto-detect best engine
    DIRECT = "direct"  # Direct text extraction
    OCR = "ocr"  # OCR-based extraction
    MINERU = "mineru"  # MinerU service


class SplitMode(str, Enum):
    """PDF splitting modes."""

    TOC = "toc"  # Split by table of contents
    MANUAL = "manual"  # Manual page ranges
    NONE = "none"  # No splitting


@dataclass
class PostProcessConfig:
    """Configuration for markdown post-processing."""

    remove_headers_footers: bool = True
    clean_whitespace: bool = True
    normalize_headings: bool = True
    fix_ocr_errors: bool = False
    unify_list_format: bool = True
    header_patterns: list[str] = field(
        default_factory=lambda: [
            r"^\s*\d+\s*$",  # Page numbers
            r"^Chapter \d+",  # Chapter headers
        ]
    )
    footer_patterns: list[str] = field(
        default_factory=lambda: [
            r"^\s*\d+\s*$",  # Page numbers
        ]
    )


@dataclass
class OcrConfig:
    """Configuration for OCR engine."""

    lang: str = "en"  # Language code (e.g., "en", "chi_sim", "chi_tra")
    use_gpu: bool = False
    det_db_thresh: float = 0.3
    det_db_box_thresh: float = 0.5
    enable_layout_analysis: bool = True


@dataclass
class MinerUConfig:
    """Configuration for MinerU API."""

    api_token: str = ""
    api_base_url: str = "https://mineru.net/api/v4"
    model_version: str = "vlm"  # "vlm" or "pipeline"
    timeout: int = 300  # seconds


@dataclass
class ConversionConfig:
    """
    Main configuration for PDF to Markdown conversion.

    Attributes:
        extractor_type: Type of extraction engine to use
        split_mode: How to split the PDF
        output_dir: Directory for output files
        enable_post_processing: Whether to apply post-processing
        post_process_config: Post-processing configuration
        ocr_config: OCR engine configuration
        mineru_config: MinerU API configuration
        preserve_images: Whether to preserve images in markdown
        detect_tables: Whether to detect and convert tables
        metadata: Additional metadata
    """

    extractor_type: ExtractorType = ExtractorType.AUTO
    split_mode: SplitMode = SplitMode.TOC
    output_dir: Path = field(default_factory=lambda: Path("output"))
    enable_post_processing: bool = True
    post_process_config: PostProcessConfig = field(
        default_factory=PostProcessConfig
    )
    ocr_config: OcrConfig = field(default_factory=OcrConfig)
    mineru_config: MinerUConfig = field(default_factory=MinerUConfig)
    preserve_images: bool = False
    detect_tables: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure output directory exists."""
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
