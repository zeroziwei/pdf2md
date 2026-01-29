"""
Advanced usage examples for PDF2MD.

This file demonstrates advanced features and customization options.
"""

from pathlib import Path
from pdf2md.core.config import (
    ConversionConfig,
    ExtractorType,
    PostProcessConfig,
    OcrConfig,
)
from pdf2md.extractors import DirectExtractor, OcrExtractor, ExtractorRouter
from pdf2md.postprocessor import MarkdownCleaner
from pdf2md.splitters import TocSplitter, ManualSplitter, PageRange


def example_custom_post_processing():
    """Example: Custom post-processing configuration."""
    print("Advanced Example 1: Custom Post-Processing")
    print("-" * 50)

    # Create custom post-processing config
    post_config = PostProcessConfig(
        remove_headers_footers=True,
        clean_whitespace=True,
        normalize_headings=True,
        fix_ocr_errors=True,  # Enable OCR error fixing
        unify_list_format=True,
        header_patterns=[
            r"^\s*\d+\s*$",  # Page numbers
            r"^Chapter \d+",
            r"^CONFIDENTIAL",  # Custom pattern
        ],
        footer_patterns=[
            r"^\s*\d+\s*$",
            r"^Copyright",  # Custom pattern
        ],
    )

    # Use custom config
    config = ConversionConfig(
        extractor_type=ExtractorType.DIRECT,
        post_process_config=post_config,
    )

    # Process with custom config
    extractor = DirectExtractor(config)
    markdown = extractor.extract(Path("sample.pdf"))

    # Apply cleaning
    cleaner = MarkdownCleaner(post_config)
    cleaned = cleaner.clean(markdown)

    print(f"Original: {len(markdown)} chars")
    print(f"Cleaned: {len(cleaned)} chars")
    print(f"Reduction: {len(markdown) - len(cleaned)} chars")


def example_ocr_multilingual():
    """Example: OCR with multiple languages."""
    print("\nAdvanced Example 2: OCR with Chinese Support")
    print("-" * 50)

    # Configure OCR for Chinese
    ocr_config = OcrConfig(
        lang="chi_sim",  # Simplified Chinese
        use_gpu=True,  # Use GPU if available
        enable_layout_analysis=True,
    )

    config = ConversionConfig(
        extractor_type=ExtractorType.OCR,
        ocr_config=ocr_config,
        output_dir=Path("output"),
    )

    try:
        extractor = OcrExtractor(config)
        markdown = extractor.extract(Path("chinese_document.pdf"))

        Path("output/chinese_document.md").write_text(markdown, encoding="utf-8")
        print("Chinese document processed successfully")
    except ImportError:
        print("PaddleOCR not installed. Install with: pip install paddleocr")


def example_batch_processing():
    """Example: Process multiple PDFs in batch."""
    print("\nAdvanced Example 3: Batch Processing")
    print("-" * 50)

    pdf_files = [
        Path("document1.pdf"),
        Path("document2.pdf"),
        Path("document3.pdf"),
    ]

    config = ConversionConfig(
        extractor_type=ExtractorType.AUTO,
        output_dir=Path("output/batch"),
    )

    router = ExtractorRouter(config)
    router.register_extractor(ExtractorType.DIRECT, DirectExtractor(config))

    results = {}

    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"Skipping {pdf_path.name} (not found)")
            continue

        try:
            print(f"Processing {pdf_path.name}...")
            markdown = router.extract(pdf_path)

            output_file = config.output_dir / f"{pdf_path.stem}.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(markdown, encoding="utf-8")

            results[pdf_path.name] = "Success"
            print(f"  ✓ Saved to {output_file}")
        except Exception as e:
            results[pdf_path.name] = f"Failed: {e}"
            print(f"  ✗ Error: {e}")

    print("\nBatch Processing Results:")
    for filename, status in results.items():
        print(f"  {filename}: {status}")


def example_custom_page_ranges():
    """Example: Advanced page range splitting."""
    print("\nAdvanced Example 4: Custom Page Range Splitting")
    print("-" * 50)

    # Create custom page ranges with titles
    ranges = [
        PageRange(1, 10, "Introduction"),
        PageRange(11, 50, "Chapter 1: Background"),
        PageRange(51, 100, "Chapter 2: Methods"),
        PageRange(101, 150, "Chapter 3: Results"),
        PageRange(151, 180, "Conclusion"),
    ]

    splitter = ManualSplitter(output_dir=Path("output/custom_split"))
    document = splitter.split_and_save(Path("thesis.pdf"), ranges)

    print(f"Split into {document.segment_count} custom segments:")
    for segment in document.segments:
        print(f"  - {segment.title}: pages {segment.start_page}-{segment.end_page}")


def example_extract_and_analyze():
    """Example: Extract text and perform analysis."""
    print("\nAdvanced Example 5: Extract and Analyze")
    print("-" * 50)

    config = ConversionConfig(
        extractor_type=ExtractorType.DIRECT,
    )

    extractor = DirectExtractor(config)
    markdown = extractor.extract(Path("sample.pdf"))

    # Analyze content
    cleaner = MarkdownCleaner()

    # Extract title
    title = cleaner.extract_title_from_content(markdown)
    print(f"Document title: {title}")

    # Split into sections
    sections = cleaner.split_into_sections(markdown)
    print(f"\nFound {len(sections)} sections:")
    for heading, content in sections[:5]:  # Show first 5
        word_count = len(content.split())
        print(f"  - {heading}: {word_count} words")

    # Statistics
    total_words = len(markdown.split())
    total_lines = len(markdown.split("\n"))
    heading_count = markdown.count("#")

    print(f"\nDocument statistics:")
    print(f"  Total words: {total_words}")
    print(f"  Total lines: {total_lines}")
    print(f"  Headings: {heading_count}")


def example_toc_inspection():
    """Example: Inspect and customize TOC-based splitting."""
    print("\nAdvanced Example 6: TOC Inspection")
    print("-" * 50)

    pdf_path = Path("textbook.pdf")
    splitter = TocSplitter()

    # Check if PDF has TOC
    if not splitter.has_toc(pdf_path):
        print("PDF has no table of contents")
        return

    # Get TOC entries
    toc = splitter.get_toc(pdf_path)

    print(f"TOC has {len(toc)} entries:")

    # Group by level
    by_level = {}
    for level, title, page in toc:
        by_level.setdefault(level, []).append((title, page))

    for level in sorted(by_level.keys()):
        print(f"\nLevel {level} ({len(by_level[level])} entries):")
        for title, page in by_level[level][:5]:  # Show first 5
            print(f"  - {title} (page {page})")
        if len(by_level[level]) > 5:
            print(f"  ... and {len(by_level[level]) - 5} more")

    # Split by different levels
    for level in [1, 2]:
        if level in by_level:
            document = splitter.create_document_from_toc(pdf_path, split_level=level)
            print(
                f"\nSplitting by level {level} would create {document.segment_count} segments"
            )


def example_compare_engines():
    """Example: Compare different extraction engines."""
    print("\nAdvanced Example 7: Compare Extraction Engines")
    print("-" * 50)

    pdf_path = Path("sample.pdf")

    # Test direct extraction
    config_direct = ConversionConfig(extractor_type=ExtractorType.DIRECT)
    extractor_direct = DirectExtractor(config_direct)

    import time

    start = time.time()
    markdown_direct = extractor_direct.extract(pdf_path)
    time_direct = time.time() - start

    print(f"Direct Extraction:")
    print(f"  Time: {time_direct:.2f}s")
    print(f"  Output: {len(markdown_direct)} chars")
    print(f"  Speed: {len(markdown_direct) / time_direct:.0f} chars/sec")

    # Could add OCR comparison here if available
    # Note: This is just a template - actual comparison would need test files


if __name__ == "__main__":
    """
    Run advanced examples (comment out as needed).

    Note: These examples may require specific PDF files and optional dependencies.
    """

    print("PDF2MD Advanced Usage Examples")
    print("=" * 50)

    # Uncomment the examples you want to run:

    # example_custom_post_processing()
    # example_ocr_multilingual()
    # example_batch_processing()
    # example_custom_page_ranges()
    # example_extract_and_analyze()
    # example_toc_inspection()
    # example_compare_engines()

    print("\n" + "=" * 50)
    print("Advanced examples complete!")
