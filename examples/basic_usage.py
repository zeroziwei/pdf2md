"""
Basic usage examples for PDF2MD.

This file demonstrates the core functionality of the PDF2MD library.
"""

from pathlib import Path
from pdf2md.core.config import ConversionConfig, ExtractorType
from pdf2md.splitters import split_pdf_by_toc, split_pdf_by_ranges
from pdf2md.extractors import DirectExtractor, ExtractorRouter
from pdf2md.postprocessor import clean_markdown


def example_split_by_toc():
    """Example: Split a PDF by its table of contents."""
    print("Example 1: Split PDF by TOC")
    print("-" * 50)
    
    pdf_path = Path("sample.pdf")
    output_dir = Path("output/chapters")
    
    # Split the PDF
    document = split_pdf_by_toc(pdf_path, output_dir)
    
    print(f"Split into {document.segment_count} segments:")
    for i, segment in enumerate(document.segments, 1):
        print(f"  {i}. {segment.title} (pages {segment.start_page}-{segment.end_page})")
    
    print(f"\nOutput directory: {output_dir}")


def example_split_by_ranges():
    """Example: Split a PDF by custom page ranges."""
    print("\nExample 2: Split PDF by Page Ranges")
    print("-" * 50)
    
    pdf_path = Path("sample.pdf")
    output_dir = Path("output/segments")
    
    # Define page ranges
    ranges_str = "1-10, 15-20, 25-30"
    
    # Split the PDF
    document = split_pdf_by_ranges(pdf_path, ranges_str, output_dir)
    
    print(f"Split into {document.segment_count} segments:")
    for i, segment in enumerate(document.segments, 1):
        print(f"  {i}. {segment.title} (pages {segment.start_page}-{segment.end_page})")


def example_direct_extraction():
    """Example: Extract text using direct extraction."""
    print("\nExample 3: Direct Text Extraction")
    print("-" * 50)
    
    pdf_path = Path("sample.pdf")
    
    # Create configuration
    config = ConversionConfig(
        extractor_type=ExtractorType.DIRECT,
        output_dir=Path("output"),
    )
    
    # Create extractor
    extractor = DirectExtractor(config)
    
    # Extract markdown
    markdown = extractor.extract(pdf_path)
    
    # Save to file
    output_file = Path("output/sample.md")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown, encoding="utf-8")
    
    print(f"Extracted {len(markdown)} characters")
    print(f"Saved to: {output_file}")


def example_with_post_processing():
    """Example: Extract and clean markdown."""
    print("\nExample 4: Extraction with Post-Processing")
    print("-" * 50)
    
    pdf_path = Path("sample.pdf")
    
    # Create configuration with post-processing enabled
    config = ConversionConfig(
        extractor_type=ExtractorType.DIRECT,
        output_dir=Path("output"),
        enable_post_processing=True,
    )
    
    # Create extractor
    extractor = DirectExtractor(config)
    
    # Extract markdown
    raw_markdown = extractor.extract(pdf_path)
    print(f"Raw markdown: {len(raw_markdown)} characters")
    
    # Clean markdown
    cleaned_markdown = clean_markdown(raw_markdown, config.post_process_config)
    print(f"Cleaned markdown: {len(cleaned_markdown)} characters")
    
    # Save cleaned version
    output_file = Path("output/sample_cleaned.md")
    output_file.write_text(cleaned_markdown, encoding="utf-8")
    
    print(f"Saved to: {output_file}")


def example_router_auto_detection():
    """Example: Use router for automatic engine selection."""
    print("\nExample 5: Automatic Engine Selection")
    print("-" * 50)
    
    pdf_path = Path("sample.pdf")
    
    # Create configuration with AUTO mode
    config = ConversionConfig(
        extractor_type=ExtractorType.AUTO,
        output_dir=Path("output"),
    )
    
    # Create router and register extractors
    router = ExtractorRouter(config)
    router.register_extractor(ExtractorType.DIRECT, DirectExtractor(config))
    # Add more extractors as needed
    
    # Let router choose best engine
    markdown = router.extract(pdf_path)
    
    # Save output
    output_file = Path("output/sample_auto.md")
    output_file.write_text(markdown, encoding="utf-8")
    
    print(f"Extracted {len(markdown)} characters")
    print(f"Saved to: {output_file}")


def example_segment_extraction():
    """Example: Extract specific pages from a PDF."""
    print("\nExample 6: Extract Specific Pages")
    print("-" * 50)
    
    from pdf2md.core.document import Segment
    
    pdf_path = Path("sample.pdf")
    
    # Create a segment for pages 10-20
    segment = Segment(
        title="Chapter 2",
        start_page=10,
        end_page=20,
    )
    
    # Create configuration
    config = ConversionConfig(
        extractor_type=ExtractorType.DIRECT,
        output_dir=Path("output"),
    )
    
    # Extract only the segment
    extractor = DirectExtractor(config)
    markdown = extractor.extract(pdf_path, segment)
    
    # Save
    output_file = Path("output/chapter2.md")
    output_file.write_text(markdown, encoding="utf-8")
    
    print(f"Extracted pages {segment.start_page}-{segment.end_page}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    """
    Run examples (comment out as needed).
    
    Note: These examples assume you have a 'sample.pdf' file.
    Modify the paths to match your actual PDF files.
    """
    
    print("PDF2MD Usage Examples")
    print("=" * 50)
    
    # Uncomment the examples you want to run:
    
    # example_split_by_toc()
    # example_split_by_ranges()
    # example_direct_extraction()
    # example_with_post_processing()
    # example_router_auto_detection()
    # example_segment_extraction()
    
    print("\n" + "=" * 50)
    print("Examples complete!")
