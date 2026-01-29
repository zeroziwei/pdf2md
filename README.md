# PDF2MD - PDF to Markdown Converter

A powerful and flexible tool to convert PDF documents to Markdown format with multiple extraction engines. Supports splitting PDFs by table of contents or page ranges, and offers direct text extraction, OCR, and advanced MinerU processing.

## ✨ Features

- **Multiple Extraction Engines**
  - **Direct**: Fast text extraction for standard PDFs with text layers
  - **OCR**: PaddleOCR integration for scanned documents (supports multiple languages including Chinese)
  - **MinerU**: Advanced processing for complex layouts, mathematical formulas, and tables

- **Flexible PDF Splitting**
  - Split by Table of Contents (TOC)
  - Split by custom page ranges
  - Process entire PDF without splitting

- **Intelligent Post-Processing**
  - Remove headers and footers
  - Clean up whitespace and formatting
  - Normalize headings
  - Unify list formatting
  - Fix common OCR errors

- **Command-Line Interface**
  - Easy-to-use CLI with progress indicators
  - Batch processing support
  - Rich terminal output

## 📦 Installation

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf2md.git
cd pdf2md

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### Installation with OCR Support

For OCR functionality (scanned PDFs):

```bash
pip install -e ".[ocr]"
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## 🚀 Quick Start

### 1. Get PDF Information

```bash
pdf2md info document.pdf
```

This will show:
- Total pages
- Whether it has a table of contents
- If text is extractable (or needs OCR)
- Document metadata

### 2. Split a PDF

**Split by Table of Contents:**

```bash
pdf2md split book.pdf -o output/
```

**Split by Page Ranges:**

```bash
pdf2md split book.pdf --mode manual --pages "1-10,15-20,25-30" -o output/
```

### 3. Convert PDF to Markdown

**Auto-detect best engine:**

```bash
pdf2md convert document.pdf -o output.md
```

**Use specific engine:**

```bash
# Direct extraction (fastest)
pdf2md convert document.pdf --engine direct -o output.md

# OCR for scanned PDFs
pdf2md convert scanned.pdf --engine ocr --ocr-lang chi_sim -o output.md

# MinerU for complex layouts
pdf2md convert paper.pdf --engine mineru --mineru-token YOUR_TOKEN -o output.md
```

**Convert specific pages:**

```bash
pdf2md convert book.pdf --start 1 --end 10 -o chapter1.md
```

### 4. Full Pipeline (Split + Convert)

```bash
# Process entire book with TOC
pdf2md process book.pdf --split-by toc --engine direct -o output/

# Process with manual ranges and OCR
pdf2md process doc.pdf --split-by manual --pages "1-10,15-20" --engine ocr -o output/

# Process without splitting
pdf2md process paper.pdf --split-by none --engine auto -o output/
```

## 📚 Usage Examples

### Example 1: Academic Textbook

```bash
# 1. Check if book has TOC
pdf2md info textbook.pdf

# 2. Split by chapters
pdf2md split textbook.pdf --mode toc -o chapters/

# 3. Convert each chapter with direct extraction
pdf2md process textbook.pdf --split-by toc --engine direct --clean -o output/
```

### Example 2: Scanned Document (Chinese)

```bash
# Convert scanned Chinese document with OCR
pdf2md convert scanned.pdf --engine ocr --ocr-lang chi_sim -o output.md
```

### Example 3: Research Paper with Math

```bash
# Use MinerU for complex math and tables
pdf2md convert paper.pdf --engine mineru --mineru-token YOUR_TOKEN -o paper.md
```

### Example 4: Extract Specific Pages

```bash
# Extract pages 10-50 from a large document
pdf2md convert large_doc.pdf --start 10 --end 50 --engine direct -o excerpt.md
```

## 🛠️ Configuration

### OCR Languages

PaddleOCR supports multiple languages. Common options:

- `en` - English
- `chi_sim` - Simplified Chinese
- `chi_tra` - Traditional Chinese
- `japan` - Japanese
- `korean` - Korean
- `french` - French
- `german` - German
- `spanish` - Spanish

### MinerU API

To use MinerU, you need an API token:

1. Sign up at [MinerU](https://mineru.net)
2. Get your API token
3. Use it with `--mineru-token YOUR_TOKEN`

### Post-Processing Options

Disable cleaning if you want raw output:

```bash
pdf2md convert doc.pdf --no-clean -o raw_output.md
```

## 🏗️ Architecture

The project follows a modular architecture:

```
pdf2md/
├── core/              # Core domain models and configuration
├── splitters/         # PDF splitting logic (TOC, manual)
├── extractors/        # Conversion engines (Direct, OCR, MinerU)
├── postprocessor/     # Markdown cleaning and normalization
└── cli/               # Command-line interface
```

For detailed architecture information, see [`docs/architecture.md`](docs/architecture.md).

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pdf2md --cov-report=html

# Run specific test file
pytest tests/test_splitters.py
```

## 📖 API Usage

You can also use PDF2MD as a Python library:

```python
from pathlib import Path
from pdf2md.core.config import ConversionConfig, ExtractorType
from pdf2md.splitters import split_pdf_by_toc
from pdf2md.extractors import DirectExtractor, ExtractorRouter
from pdf2md.postprocessor import clean_markdown

# Split PDF by TOC
document = split_pdf_by_toc(Path("book.pdf"), output_dir=Path("output"))

# Convert to markdown
config = ConversionConfig(
    extractor_type=ExtractorType.DIRECT,
    output_dir=Path("output")
)

router = ExtractorRouter(config)
router.register_extractor(ExtractorType.DIRECT, DirectExtractor(config))

markdown = router.extract(Path("book.pdf"))

# Clean markdown
cleaned = clean_markdown(markdown)

# Save
Path("output.md").write_text(cleaned, encoding="utf-8")
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/pdf2md.git
cd pdf2md

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

### Project Structure

```
pdf2markdown-master/
├── src/
│   └── pdf2md/           # Main package
│       ├── core/         # Domain models
│       ├── splitters/    # PDF splitting
│       ├── extractors/   # Conversion engines
│       ├── postprocessor/ # Markdown cleaning
│       └── cli/          # Command-line interface
├── tests/                # Test suite
├── examples/             # Usage examples
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration
└── README.md            # This file
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR engine
- [MinerU](https://mineru.net) - Advanced PDF processing
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting

## 📞 Support

If you encounter any issues or have questions:

- Open an issue on [GitHub](https://github.com/yourusername/pdf2md/issues)
- Check the [documentation](docs/architecture.md)

## 🗺️ Roadmap

Future enhancements:

- [ ] Web interface (FastAPI + React)
- [ ] Batch processing with async queue
- [ ] Table extraction improvements
- [ ] Image extraction and embedding
- [ ] Custom post-processing rules
- [ ] Export to other formats (HTML, DOCX)
- [ ] GUI application

---

**Made with ❤️ for the PDF processing community**
