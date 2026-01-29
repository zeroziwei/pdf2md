"""
Tests for PDF splitting functionality.
"""

import pytest
from pathlib import Path
from pdf2md.splitters import ManualSplitter, PageRange


class TestPageRange:
    """Test PageRange class."""

    def test_create_page_range(self):
        """Test creating a page range."""
        pr = PageRange(1, 10, "Test Range")
        assert pr.start == 1
        assert pr.end == 10
        assert pr.title == "Test Range"
        assert pr.page_count == 10

    def test_page_range_validation(self):
        """Test page range validation."""
        with pytest.raises(ValueError):
            PageRange(0, 10)  # Start page < 1

        with pytest.raises(ValueError):
            PageRange(10, 5)  # End < start

    def test_page_range_default_title(self):
        """Test default title generation."""
        pr = PageRange(5, 15)
        assert pr.title == "Pages 5-15"


class TestManualSplitter:
    """Test ManualSplitter class."""

    def test_parse_single_range(self):
        """Test parsing single page range."""
        ranges = ManualSplitter.parse_page_ranges("1-10")
        assert len(ranges) == 1
        assert ranges[0].start == 1
        assert ranges[0].end == 10

    def test_parse_multiple_ranges(self):
        """Test parsing multiple page ranges."""
        ranges = ManualSplitter.parse_page_ranges("1-10, 15-20, 25-30")
        assert len(ranges) == 3
        assert ranges[0].start == 1
        assert ranges[0].end == 10
        assert ranges[1].start == 15
        assert ranges[1].end == 20
        assert ranges[2].start == 25
        assert ranges[2].end == 30

    def test_parse_single_page(self):
        """Test parsing single page as range."""
        ranges = ManualSplitter.parse_page_ranges("5")
        assert len(ranges) == 1
        assert ranges[0].start == 5
        assert ranges[0].end == 5

    def test_parse_invalid_format(self):
        """Test parsing invalid format."""
        with pytest.raises(ValueError):
            ManualSplitter.parse_page_ranges("abc")

        with pytest.raises(ValueError):
            ManualSplitter.parse_page_ranges("1-10-15")

    def test_validate_ranges(self):
        """Test range validation."""
        ranges = [PageRange(1, 10), PageRange(15, 20)]

        # Should pass
        ManualSplitter.validate_ranges(ranges, 50)

        # Should fail
        with pytest.raises(ValueError):
            ManualSplitter.validate_ranges(ranges, 15)  # End of second range > total


class TestTocSplitter:
    """Test TocSplitter class (requires actual PDF)."""

    # These tests would need actual PDF files
    # Skipping for now, can be added with test fixtures
    pass
