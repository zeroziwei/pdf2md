"""
Markdown post-processing and cleaning utilities.

Cleans up extracted markdown by removing headers, footers, noise, and normalizing formatting.
"""

import re
from typing import List, Optional

from pdf2md.core.config import PostProcessConfig


class MarkdownCleaner:
    """
    Cleans and normalizes Markdown content extracted from PDFs.
    """

    def __init__(self, config: Optional[PostProcessConfig] = None):
        """
        Initialize the markdown cleaner.

        Args:
            config: Post-processing configuration
        """
        self.config = config or PostProcessConfig()

    def clean(self, markdown: str) -> str:
        """
        Apply all cleaning operations to markdown.

        Args:
            markdown: Raw markdown content

        Returns:
            Cleaned markdown content
        """
        # Apply cleaning steps in order
        if self.config.remove_headers_footers:
            markdown = self.remove_headers_footers(markdown)

        if self.config.clean_whitespace:
            markdown = self.clean_whitespace(markdown)

        if self.config.normalize_headings:
            markdown = self.normalize_headings(markdown)

        if self.config.fix_ocr_errors:
            markdown = self.fix_common_ocr_errors(markdown)

        if self.config.unify_list_format:
            markdown = self.unify_list_formatting(markdown)

        return markdown

    def remove_headers_footers(self, markdown: str) -> str:
        """
        Remove common header and footer patterns.

        Args:
            markdown: Input markdown

        Returns:
            Markdown with headers/footers removed
        """
        lines = markdown.split("\n")
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()

            # Check against header patterns
            is_header = False
            for pattern in self.config.header_patterns:
                if re.match(pattern, line_stripped):
                    is_header = True
                    break

            # Check against footer patterns
            is_footer = False
            for pattern in self.config.footer_patterns:
                if re.match(pattern, line_stripped):
                    is_footer = True
                    break

            # Keep line if it's not a header or footer
            if not is_header and not is_footer:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def clean_whitespace(self, markdown: str) -> str:
        """
        Clean up excessive whitespace and empty lines.

        Args:
            markdown: Input markdown

        Returns:
            Markdown with cleaned whitespace
        """
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in markdown.split("\n")]

        # Collapse multiple empty lines into max 2
        cleaned_lines = []
        empty_count = 0

        for line in lines:
            if not line:
                empty_count += 1
                if empty_count <= 2:
                    cleaned_lines.append(line)
            else:
                empty_count = 0
                cleaned_lines.append(line)

        # Remove leading/trailing empty lines
        while cleaned_lines and not cleaned_lines[0]:
            cleaned_lines.pop(0)

        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)

    def normalize_headings(self, markdown: str) -> str:
        """
        Normalize heading format and spacing.

        Args:
            markdown: Input markdown

        Returns:
            Markdown with normalized headings
        """
        lines = markdown.split("\n")
        normalized_lines = []

        for i, line in enumerate(lines):
            # Check if line is a heading
            heading_match = re.match(r"^(#{1,6})\s*(.*)", line)

            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # Ensure proper spacing before heading (except first line)
                if i > 0 and normalized_lines and normalized_lines[-1]:
                    normalized_lines.append("")

                # Normalize heading format
                normalized_lines.append(f"{'#' * level} {title}")

                # Ensure spacing after heading
                if i < len(lines) - 1 and lines[i + 1]:
                    normalized_lines.append("")
            else:
                normalized_lines.append(line)

        return "\n".join(normalized_lines)

    def fix_common_ocr_errors(self, markdown: str) -> str:
        """
        Fix common OCR errors using pattern matching.

        Args:
            markdown: Input markdown

        Returns:
            Markdown with fixed OCR errors
        """
        # Common OCR substitutions
        replacements = [
            (r"\bl\b", "I"),  # lowercase L to I (context-dependent)
            (r"\bO\b", "0"),  # uppercase O to 0 in numbers
            (r"(\d)\s+(\d)", r"\1\2"),  # Remove spaces in numbers
            (r"[''`]", "'"),  # Normalize quotes
            (r"[" "„]", '"'),  # Normalize double quotes
            (r"—|–", "-"),  # Normalize dashes
            (r"…", "..."),  # Normalize ellipsis
        ]

        for pattern, replacement in replacements:
            markdown = re.sub(pattern, replacement, markdown)

        return markdown

    def unify_list_formatting(self, markdown: str) -> str:
        """
        Unify list formatting (use consistent markers).

        Args:
            markdown: Input markdown

        Returns:
            Markdown with unified list formatting
        """
        lines = markdown.split("\n")
        formatted_lines = []

        for line in lines:
            # Unify unordered list markers to "-"
            if re.match(r"^\s*[•\*\+]\s+", line):
                line = re.sub(r"^\s*[•\*\+]\s+", "- ", line)

            # Normalize ordered list format
            if re.match(r"^\s*\d+[\.)]\s+", line):
                match = re.match(r"^\s*(\d+)[\.)]\s+(.*)", line)
                if match:
                    num = match.group(1)
                    content = match.group(2)
                    line = f"{num}. {content}"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def remove_page_breaks(self, markdown: str) -> str:
        """
        Remove explicit page break markers.

        Args:
            markdown: Input markdown

        Returns:
            Markdown without page breaks
        """
        # Remove common page break patterns
        patterns = [
            r"---+\s*Page \d+\s*---+",
            r"\[Page \d+\]",
            r"Page \d+ of \d+",
            r"^\s*-{3,}\s*$",  # Horizontal rules that might be page breaks
        ]

        for pattern in patterns:
            markdown = re.sub(pattern, "", markdown, flags=re.MULTILINE)

        return markdown

    def merge_hyphenated_words(self, markdown: str) -> str:
        """
        Merge words split across lines with hyphens.

        Args:
            markdown: Input markdown

        Returns:
            Markdown with merged words
        """
        # Match word-\nword pattern
        markdown = re.sub(r"(\w+)-\n(\w+)", r"\1\2", markdown)
        return markdown

    def extract_title_from_content(self, markdown: str) -> Optional[str]:
        """
        Extract document title from content (first heading or capitalized line).

        Args:
            markdown: Markdown content

        Returns:
            Extracted title or None
        """
        lines = markdown.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for heading
            heading_match = re.match(r"^#{1,3}\s+(.+)", line)
            if heading_match:
                return heading_match.group(1).strip()

            # Check for all-caps title
            if line.isupper() and len(line) > 5:
                return line.title()

            # First substantial line
            if len(line) > 10:
                return line

        return None

    def split_into_sections(self, markdown: str) -> List[tuple[str, str]]:
        """
        Split markdown into sections based on headings.

        Args:
            markdown: Markdown content

        Returns:
            List of (heading, content) tuples
        """
        sections = []
        current_heading = "Introduction"
        current_content = []

        lines = markdown.split("\n")

        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.+)", line)

            if heading_match:
                # Save previous section
                if current_content:
                    sections.append((current_heading, "\n".join(current_content)))

                # Start new section
                current_heading = heading_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections.append((current_heading, "\n".join(current_content)))

        return sections


def clean_markdown(markdown: str, config: Optional[PostProcessConfig] = None) -> str:
    """
    Convenience function to clean markdown.

    Args:
        markdown: Raw markdown content
        config: Post-processing configuration

    Returns:
        Cleaned markdown content
    """
    cleaner = MarkdownCleaner(config)
    return cleaner.clean(markdown)
