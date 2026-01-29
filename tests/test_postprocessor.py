"""
Tests for markdown post-processing.
"""

import pytest
from pdf2md.postprocessor import MarkdownCleaner, clean_markdown
from pdf2md.core.config import PostProcessConfig


class TestMarkdownCleaner:
    """Test MarkdownCleaner class."""
    
    def test_clean_whitespace(self):
        """Test whitespace cleaning."""
        cleaner = MarkdownCleaner()
        
        input_text = """

Line 1    


Line 2


        """
        
        expected = "Line 1\n\n\nLine 2"
        result = cleaner.clean_whitespace(input_text)
        assert result == expected
    
    def test_normalize_headings(self):
        """Test heading normalization."""
        cleaner = MarkdownCleaner()
        
        input_text = "##  Heading with extra spaces  \nContent here"
        result = cleaner.normalize_headings(input_text)
        
        assert "## Heading with extra spaces" in result
    
    def test_unify_list_formatting(self):
        """Test list formatting unification."""
        cleaner = MarkdownCleaner()
        
        input_text = """
* Item 1
• Item 2
+ Item 3
1) Numbered 1
2. Numbered 2
        """
        
        result = cleaner.unify_list_formatting(input_text)
        
        # All unordered should be "-"
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result
        
        # All ordered should be "N."
        assert "1. Numbered 1" in result
        assert "2. Numbered 2" in result
    
    def test_remove_page_breaks(self):
        """Test page break removal."""
        cleaner = MarkdownCleaner()
        
        input_text = """
Content before
--- Page 5 ---
Content after
[Page 10]
More content
        """
        
        result = cleaner.remove_page_breaks(input_text)
        
        assert "Page 5" not in result
        assert "[Page 10]" not in result
        assert "Content before" in result
        assert "Content after" in result
    
    def test_merge_hyphenated_words(self):
        """Test merging hyphenated words across lines."""
        cleaner = MarkdownCleaner()
        
        input_text = "This is a long-\nword that was split."
        result = cleaner.merge_hyphenated_words(input_text)
        
        assert "longword" in result
        assert "long-\n" not in result
    
    def test_extract_title(self):
        """Test title extraction."""
        cleaner = MarkdownCleaner()
        
        # Test with heading
        markdown1 = "# Document Title\n\nContent here"
        title1 = cleaner.extract_title_from_content(markdown1)
        assert title1 == "Document Title"
        
        # Test with all-caps
        markdown2 = "DOCUMENT TITLE\n\nContent here"
        title2 = cleaner.extract_title_from_content(markdown2)
        assert title2 == "Document Title"
    
    def test_split_into_sections(self):
        """Test splitting markdown into sections."""
        cleaner = MarkdownCleaner()
        
        markdown = """
# Section 1
Content for section 1

## Section 2
Content for section 2

# Section 3
Content for section 3
        """
        
        sections = cleaner.split_into_sections(markdown)
        
        assert len(sections) >= 2
        assert any("Section 1" in s[0] for s in sections)
        assert any("Section 2" in s[0] for s in sections)
    
    def test_full_clean(self):
        """Test full cleaning pipeline."""
        config = PostProcessConfig(
            remove_headers_footers=True,
            clean_whitespace=True,
            normalize_headings=True,
            unify_list_format=True,
        )
        cleaner = MarkdownCleaner(config)
        
        input_text = """


##  Chapter Title  

* Item 1
• Item 2


Content here    


        """
        
        result = cleaner.clean(input_text)
        
        # Should be cleaner
        assert result.count("\n\n\n") <= 1  # No triple line breaks
        assert "## Chapter Title" in result
        assert "- Item 1" in result
        assert "- Item 2" in result


def test_clean_markdown_function():
    """Test convenience function."""
    input_text = "##  Heading  \n\n\n\nContent"
    result = clean_markdown(input_text)
    
    assert "## Heading" in result
    assert "\n\n\n\n" not in result
