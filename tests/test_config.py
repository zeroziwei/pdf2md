"""
Tests for configuration classes.
"""

import pytest
from pathlib import Path
from pdf2md.core.config import (
    ConversionConfig,
    ExtractorType,
    SplitMode,
    PostProcessConfig,
    OcrConfig,
    MinerUConfig,
)


class TestExtractorType:
    """Test ExtractorType enum."""

    def test_extractor_types(self):
        """Test all extractor types."""
        assert ExtractorType.AUTO == "auto"
        assert ExtractorType.DIRECT == "direct"
        assert ExtractorType.OCR == "ocr"
        assert ExtractorType.MINERU == "mineru"


class TestConversionConfig:
    """Test ConversionConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = ConversionConfig()
        assert config.extractor_type == ExtractorType.AUTO
        assert config.split_mode == SplitMode.TOC
        assert config.enable_post_processing is True
        assert config.output_dir.exists()

    def test_custom_config(self):
        """Test custom configuration."""
        output_dir = Path("custom_output")
        config = ConversionConfig(
            extractor_type=ExtractorType.DIRECT,
            split_mode=SplitMode.MANUAL,
            output_dir=output_dir,
            enable_post_processing=False,
        )
        assert config.extractor_type == ExtractorType.DIRECT
        assert config.split_mode == SplitMode.MANUAL
        assert config.output_dir == output_dir
        assert config.enable_post_processing is False


class TestPostProcessConfig:
    """Test PostProcessConfig class."""

    def test_default_post_process_config(self):
        """Test default post-processing configuration."""
        config = PostProcessConfig()
        assert config.remove_headers_footers is True
        assert config.clean_whitespace is True
        assert config.normalize_headings is True
        assert config.fix_ocr_errors is False
        assert config.unify_list_format is True
        assert len(config.header_patterns) > 0
        assert len(config.footer_patterns) > 0


class TestOcrConfig:
    """Test OcrConfig class."""

    def test_default_ocr_config(self):
        """Test default OCR configuration."""
        config = OcrConfig()
        assert config.lang == "en"
        assert config.use_gpu is False
        assert config.enable_layout_analysis is True

    def test_custom_ocr_config(self):
        """Test custom OCR configuration."""
        config = OcrConfig(
            lang="chi_sim",
            use_gpu=True,
            enable_layout_analysis=False,
        )
        assert config.lang == "chi_sim"
        assert config.use_gpu is True
        assert config.enable_layout_analysis is False


class TestMinerUConfig:
    """Test MinerUConfig class."""

    def test_default_mineru_config(self):
        """Test default MinerU configuration."""
        config = MinerUConfig()
        assert config.api_token == ""
        assert config.model_version == "vlm"
        assert config.timeout == 300

    def test_custom_mineru_config(self):
        """Test custom MinerU configuration."""
        config = MinerUConfig(
            api_token="test_token",
            model_version="pipeline",
            timeout=600,
        )
        assert config.api_token == "test_token"
        assert config.model_version == "pipeline"
        assert config.timeout == 600
