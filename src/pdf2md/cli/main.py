"""
Command-line interface for PDF2MD.

Provides commands for splitting, converting, and processing PDFs to Markdown.
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from pdf2md.core.config import (
    ConversionConfig,
    ExtractorType,
    OcrConfig,
    MinerUConfig,
)
from pdf2md.splitters import TocSplitter, ManualSplitter
from pdf2md.extractors import (
    DirectExtractor,
    OcrExtractor,
    MinerUExtractor,
    ExtractorRouter,
    BaseExtractor,
)
from pdf2md.postprocessor import clean_markdown

app = typer.Typer(
    name="pdf2md",
    help="PDF to Markdown conversion tool with multiple extraction engines.",
    add_completion=False,
)
console = Console()


@app.command()
def split(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF file", exists=True),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory"
    ),
    mode: str = typer.Option(
        "toc", "--mode", "-m", help="Split mode: 'toc' or 'manual'"
    ),
    pages: Optional[str] = typer.Option(
        None, "--pages", "-p", help="Page ranges for manual mode (e.g., '1-10,15-20')"
    ),
    level: int = typer.Option(
        1, "--level", "-l", help="TOC level to split on (for toc mode)"
    ),
):
    """
    Split a PDF by table of contents or page ranges.

    Examples:

        # Split by TOC (chapters)
        pdf2md split book.pdf -o output/

        # Split by page ranges
        pdf2md split book.pdf --mode manual --pages "1-10,15-20,25-30"
    """
    console.print(f"[bold blue]Splitting PDF:[/bold blue] {pdf_path.name}")

    try:
        if mode == "toc":
            splitter = TocSplitter(output_dir)

            if not splitter.has_toc(pdf_path):
                console.print(
                    "[bold red]Error:[/bold red] PDF has no table of contents!"
                )
                console.print(
                    "Try using manual mode: --mode manual --pages '1-10,15-20'"
                )
                raise typer.Exit(1)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Splitting by TOC...", total=None)
                document = splitter.split_and_save(pdf_path, output_dir, level)
                progress.update(task, completed=True)

            console.print(
                f"[bold green]✓[/bold green] Split into {document.segment_count} segments"
            )

        elif mode == "manual":
            if not pages:
                console.print(
                    "[bold red]Error:[/bold red] Page ranges required for manual mode!"
                )
                console.print("Use --pages '1-10,15-20' to specify ranges")
                raise typer.Exit(1)

            splitter = ManualSplitter(output_dir)
            ranges = ManualSplitter.parse_page_ranges(pages)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Splitting by page ranges...", total=None)
                document = splitter.split_and_save(pdf_path, ranges, output_dir)
                progress.update(task, completed=True)

            console.print(
                f"[bold green]✓[/bold green] Split into {document.segment_count} segments"
            )

        else:
            console.print(
                f"[bold red]Error:[/bold red] Invalid mode '{mode}'. Use 'toc' or 'manual'"
            )
            raise typer.Exit(1)

        # Display segments
        _display_segments(document)

        console.print(
            f"\n[bold]Output directory:[/bold] {document.metadata.get('output_dir', output_dir)}"
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def convert(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF file", exists=True),
    output_file: Path = typer.Option(
        "output.md", "--output", "-o", help="Output markdown file"
    ),
    engine: str = typer.Option(
        "auto", "--engine", "-e", help="Extraction engine: auto, direct, ocr, mineru"
    ),
    clean: bool = typer.Option(
        True, "--clean/--no-clean", help="Apply post-processing"
    ),
    start_page: Optional[int] = typer.Option(
        None, "--start", help="Start page (1-indexed)"
    ),
    end_page: Optional[int] = typer.Option(None, "--end", help="End page (1-indexed)"),
    mineru_token: Optional[str] = typer.Option(
        None, "--mineru-token", help="MinerU API token"
    ),
    ocr_lang: str = typer.Option(
        "en", "--ocr-lang", help="OCR language (en, chi_sim, chi_tra, etc.)"
    ),
):
    """
    Convert a PDF to Markdown using specified extraction engine.

    Examples:

        # Auto-detect best engine
        pdf2md convert document.pdf -o output.md

        # Use direct extraction
        pdf2md convert document.pdf -e direct -o output.md

        # Use OCR for scanned PDFs
        pdf2md convert scanned.pdf -e ocr --ocr-lang chi_sim -o output.md

        # Convert specific page range
        pdf2md convert book.pdf --start 1 --end 10 -o chapter1.md
    """
    console.print(f"[bold blue]Converting PDF:[/bold blue] {pdf_path.name}")
    console.print(f"[bold]Engine:[/bold] {engine}")

    try:
        # Create configuration
        config = ConversionConfig(
            extractor_type=ExtractorType(engine),
            output_dir=output_file.parent,
            enable_post_processing=clean,
            ocr_config=OcrConfig(lang=ocr_lang),
            mineru_config=MinerUConfig(api_token=mineru_token or ""),
        )

        # Create segment if page range specified
        segment = None
        if start_page and end_page:
            from pdf2md.core.document import Segment

            segment = Segment(
                title=pdf_path.stem,
                start_page=start_page,
                end_page=end_page,
            )

        # Initialize extractor router
        router = ExtractorRouter(config)

        # Register available extractors
        router.register_extractor(ExtractorType.DIRECT, DirectExtractor(config))

        try:
            router.register_extractor(ExtractorType.OCR, OcrExtractor(config))
        except ImportError:
            console.print(
                "[yellow]Warning:[/yellow] PaddleOCR not available, OCR engine disabled"
            )

        if config.mineru_config.api_token:
            router.register_extractor(ExtractorType.MINERU, MinerUExtractor(config))

        # Extract markdown
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting text...", total=None)
            markdown = router.extract(pdf_path, segment)
            progress.update(task, completed=True)

        console.print("[bold green]✓[/bold green] Text extracted")

        # Apply post-processing if enabled
        if clean:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Cleaning markdown...", total=None)
                markdown = clean_markdown(markdown, config.post_process_config)
                progress.update(task, completed=True)

            console.print("[bold green]✓[/bold green] Markdown cleaned")

        # Save output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")

        console.print(f"\n[bold green]✓ Conversion complete![/bold green]")
        console.print(f"[bold]Output:[/bold] {output_file}")
        console.print(f"[bold]Size:[/bold] {len(markdown)} characters")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback

        console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def process(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF file", exists=True),
    output_dir: Path = typer.Option(
        "output", "--output", "-o", help="Output directory"
    ),
    split_by: str = typer.Option(
        "toc", "--split-by", help="Split mode: 'toc', 'manual', or 'none'"
    ),
    pages: Optional[str] = typer.Option(
        None, "--pages", help="Page ranges for manual split"
    ),
    engine: str = typer.Option("auto", "--engine", "-e", help="Extraction engine"),
    clean: bool = typer.Option(
        True, "--clean/--no-clean", help="Apply post-processing"
    ),
    mineru_token: Optional[str] = typer.Option(
        None, "--mineru-token", help="MinerU API token"
    ),
    ocr_lang: str = typer.Option("en", "--ocr-lang", help="OCR language"),
):
    """
    Full pipeline: split PDF, convert segments, and export markdown.

    Examples:

        # Process book with TOC
        pdf2md process book.pdf --split-by toc --engine direct

        # Process with manual page ranges
        pdf2md process doc.pdf --split-by manual --pages "1-10,15-20" --engine ocr

        # Process entire PDF without splitting
        pdf2md process paper.pdf --split-by none --engine mineru --mineru-token YOUR_TOKEN
    """
    console.print(f"[bold blue]Processing PDF:[/bold blue] {pdf_path.name}")
    console.print(f"[bold]Split mode:[/bold] {split_by}")
    console.print(f"[bold]Engine:[/bold] {engine}\n")

    try:
        # Step 1: Split PDF
        document = None

        if split_by == "toc":
            console.print("[bold]Step 1:[/bold] Splitting by TOC...")
            splitter = TocSplitter(output_dir)

            if not splitter.has_toc(pdf_path):
                console.print(
                    "[bold red]Error:[/bold red] No TOC found. Use --split-by manual or --split-by none"
                )
                raise typer.Exit(1)

            document = splitter.split_and_save(pdf_path, output_dir)
            console.print(
                f"[bold green]✓[/bold green] Split into {document.segment_count} segments\n"
            )

        elif split_by == "manual":
            if not pages:
                console.print(
                    "[bold red]Error:[/bold red] Page ranges required. Use --pages '1-10,15-20'"
                )
                raise typer.Exit(1)

            console.print("[bold]Step 1:[/bold] Splitting by page ranges...")
            splitter = ManualSplitter(output_dir)
            ranges = ManualSplitter.parse_page_ranges(pages)
            document = splitter.split_and_save(pdf_path, ranges, output_dir)
            console.print(
                f"[bold green]✓[/bold green] Split into {document.segment_count} segments\n"
            )

        elif split_by == "none":
            console.print("[bold]Step 1:[/bold] No splitting (processing entire PDF)\n")

        # Step 2: Convert segments to Markdown
        config = ConversionConfig(
            extractor_type=ExtractorType(engine),
            output_dir=output_dir,
            enable_post_processing=clean,
            ocr_config=OcrConfig(lang=ocr_lang),
            mineru_config=MinerUConfig(api_token=mineru_token or ""),
        )

        router = ExtractorRouter(config)
        router.register_extractor(ExtractorType.DIRECT, DirectExtractor(config))

        try:
            router.register_extractor(ExtractorType.OCR, OcrExtractor(config))
        except ImportError:
            pass

        if config.mineru_config.api_token:
            router.register_extractor(ExtractorType.MINERU, MinerUExtractor(config))

        console.print("[bold]Step 2:[/bold] Converting to Markdown...")

        if document and document.segments:
            # Process each segment
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Converting segments...", total=len(document.segments)
                )

                for segment in document.segments:
                    segment_pdf = Path(segment.metadata.get("pdf_path", ""))
                    if not segment_pdf.exists():
                        continue

                    # Extract markdown
                    markdown = router.extract(segment_pdf, segment)

                    # Clean if enabled
                    if clean:
                        markdown = clean_markdown(markdown, config.post_process_config)

                    # Save markdown
                    md_filename = segment_pdf.stem + ".md"
                    md_path = output_dir / md_filename
                    md_path.write_text(markdown, encoding="utf-8")

                    segment.metadata["markdown_path"] = str(md_path)
                    progress.update(task, advance=1)

            console.print(
                f"[bold green]✓[/bold green] Converted {document.segment_count} segments\n"
            )

        else:
            # Process entire PDF
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Converting PDF...", total=None)
                markdown = router.extract(pdf_path)

                if clean:
                    markdown = clean_markdown(markdown, config.post_process_config)

                md_path = output_dir / f"{pdf_path.stem}.md"
                output_dir.mkdir(parents=True, exist_ok=True)
                md_path.write_text(markdown, encoding="utf-8")

                progress.update(task, completed=True)

            console.print(f"[bold green]✓[/bold green] Converted PDF\n")

        console.print(f"[bold green]✓ Processing complete![/bold green]")
        console.print(f"[bold]Output directory:[/bold] {output_dir}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback

        console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def info(
    pdf_path: Path = typer.Argument(..., help="Path to the PDF file", exists=True),
):
    """
    Display information about a PDF file.

    Examples:

        pdf2md info document.pdf
    """
    import fitz

    console.print(f"[bold blue]PDF Information:[/bold blue] {pdf_path.name}\n")

    try:
        doc = fitz.open(pdf_path)

        # Basic info
        table = Table(title="Document Properties")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Filename", pdf_path.name)
        table.add_row("File Size", f"{pdf_path.stat().st_size / 1024:.2f} KB")
        table.add_row("Total Pages", str(doc.page_count))

        # Check for TOC
        toc = doc.get_toc()
        has_toc = len(toc) > 0
        table.add_row("Has TOC", "Yes" if has_toc else "No")
        if has_toc:
            table.add_row("TOC Entries", str(len(toc)))

        # Check if text-extractable
        is_extractable = BaseExtractor.is_text_extractable(pdf_path)
        table.add_row("Text Extractable", "Yes" if is_extractable else "No (needs OCR)")

        # Metadata
        metadata = doc.metadata
        if metadata.get("title"):
            table.add_row("Title", metadata["title"])
        if metadata.get("author"):
            table.add_row("Author", metadata["author"])
        if metadata.get("subject"):
            table.add_row("Subject", metadata["subject"])

        console.print(table)

        # Display TOC preview
        if has_toc:
            console.print("\n[bold]Table of Contents Preview:[/bold]")
            for i, (level, title, page) in enumerate(toc[:10]):
                indent = "  " * (level - 1)
                console.print(f"{indent}- {title} (page {page})")

            if len(toc) > 10:
                console.print(f"  ... and {len(toc) - 10} more entries")

        doc.close()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


def _display_segments(document):
    """Display segments in a table."""

    table = Table(title="Segments")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Title", style="white")
    table.add_column("Pages", style="yellow", width=12)

    for idx, segment in enumerate(document.segments, 1):
        table.add_row(
            str(idx),
            segment.title[:50],
            f"{segment.start_page}-{segment.end_page}",
        )

    console.print()
    console.print(table)


@app.command()
def version():
    """Display version information."""
    from pdf2md import __version__

    console.print(f"[bold]pdf2md[/bold] version {__version__}")


if __name__ == "__main__":
    app()
