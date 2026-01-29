"""
Tests for document and segment models.
"""

import pytest
from pathlib import Path
from pdf2md.core.document import Document, Segment, SegmentStatus


class TestSegment:
    """Test Segment class."""
    
    def test_create_segment(self):
        """Test creating a segment."""
        segment = Segment(
            title="Chapter 1",
            start_page=1,
            end_page=10,
            level=1,
        )
        assert segment.title == "Chapter 1"
        assert segment.start_page == 1
        assert segment.end_page == 10
        assert segment.level == 1
        assert segment.status == SegmentStatus.CREATED
        assert segment.page_count == 10
    
    def test_segment_status_update(self):
        """Test updating segment status."""
        segment = Segment(title="Test")
        assert segment.status == SegmentStatus.CREATED
        
        segment.update_status(SegmentStatus.CONVERTING)
        assert segment.status == SegmentStatus.CONVERTING
        
        segment.update_status(SegmentStatus.FAILED, "Test error")
        assert segment.status == SegmentStatus.FAILED
        assert segment.error_message == "Test error"
    
    def test_segment_page_count(self):
        """Test page count calculation."""
        segment = Segment(start_page=5, end_page=15)
        assert segment.page_count == 11


class TestDocument:
    """Test Document class."""
    
    def test_create_document(self):
        """Test creating a document."""
        doc = Document(
            original_filename="test.pdf",
            file_path=Path("test.pdf"),
            title="Test Document",
            total_pages=100,
            has_toc=True,
        )
        assert doc.original_filename == "test.pdf"
        assert doc.title == "Test Document"
        assert doc.total_pages == 100
        assert doc.has_toc is True
        assert doc.segment_count == 0
    
    def test_add_segment(self):
        """Test adding segments to document."""
        doc = Document(title="Test")
        
        segment1 = Segment(title="Chapter 1", start_page=1, end_page=10)
        segment2 = Segment(title="Chapter 2", start_page=11, end_page=20)
        
        doc.add_segment(segment1)
        doc.add_segment(segment2)
        
        assert doc.segment_count == 2
        assert segment1.parent_doc_id == doc.document_id
        assert segment2.parent_doc_id == doc.document_id
    
    def test_get_segment(self):
        """Test retrieving segment by ID."""
        doc = Document(title="Test")
        
        segment = Segment(title="Chapter 1", start_page=1, end_page=10)
        doc.add_segment(segment)
        
        retrieved = doc.get_segment(segment.segment_id)
        assert retrieved is not None
        assert retrieved.segment_id == segment.segment_id
        assert retrieved.title == "Chapter 1"
        
        # Test non-existent segment
        none_segment = doc.get_segment("non_existent_id")
        assert none_segment is None
