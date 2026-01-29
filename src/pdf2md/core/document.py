"""
Core domain models for documents and segments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import uuid4


class SegmentStatus(str, Enum):
    """Status of a segment conversion."""
    CREATED = "created"
    SPLITTING = "splitting"
    READY = "ready"
    CONVERTING = "converting"
    CONVERTED = "converted"
    POST_PROCESSING = "post_processing"
    DONE = "done"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Segment:
    """
    Represents a segment of a PDF document.
    
    Attributes:
        segment_id: Unique identifier for the segment
        title: Title of the segment (e.g., chapter name)
        start_page: Starting page number (1-indexed)
        end_page: Ending page number (1-indexed, inclusive)
        level: Hierarchy level in TOC (1 = top level)
        parent_doc_id: Reference to parent document ID
        status: Current processing status
        markdown_content: Generated markdown content (after conversion)
        metadata: Additional metadata (file paths, conversion params, etc.)
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        error_message: Error message if status is FAILED
    """
    segment_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    start_page: int = 1
    end_page: int = 1
    level: int = 1
    parent_doc_id: str = ""
    status: SegmentStatus = SegmentStatus.CREATED
    markdown_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    @property
    def page_count(self) -> int:
        """Get the number of pages in this segment."""
        return self.end_page - self.start_page + 1
    
    def update_status(self, status: SegmentStatus, error_message: Optional[str] = None):
        """Update the status and timestamp."""
        self.status = status
        self.updated_at = datetime.now()
        if error_message:
            self.error_message = error_message


@dataclass
class Document:
    """
    Represents a PDF document with its segments.
    
    Attributes:
        document_id: Unique identifier for the document
        original_filename: Original filename of the PDF
        file_path: Path to the original PDF file
        title: Document title
        total_pages: Total number of pages
        has_toc: Whether the document has a table of contents
        segments: List of segments created from this document
        metadata: Additional metadata
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    document_id: str = field(default_factory=lambda: str(uuid4()))
    original_filename: str = ""
    file_path: Path = field(default_factory=Path)
    title: str = ""
    total_pages: int = 0
    has_toc: bool = False
    segments: list[Segment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_segment(self, segment: Segment):
        """Add a segment to the document."""
        segment.parent_doc_id = self.document_id
        self.segments.append(segment)
        self.updated_at = datetime.now()
    
    def get_segment(self, segment_id: str) -> Optional[Segment]:
        """Get a segment by ID."""
        return next((s for s in self.segments if s.segment_id == segment_id), None)
    
    @property
    def segment_count(self) -> int:
        """Get the total number of segments."""
        return len(self.segments)
