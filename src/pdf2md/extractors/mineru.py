"""
MinerU API adapter for PDF to Markdown conversion.

Refactored from mineru.py to fit the new modular architecture.
"""

import time
import zipfile
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any

from pdf2md.core.document import Segment
from pdf2md.core.config import ConversionConfig, MinerUConfig
from pdf2md.extractors.base import BaseExtractor


class MinerUExtractor(BaseExtractor):
    """
    Extractor that uses the MinerU API for PDF to Markdown conversion.

    MinerU is particularly good for complex layouts, mathematical formulas,
    and academic papers.
    """

    def __init__(self, config: ConversionConfig):
        """
        Initialize the MinerU extractor.

        Args:
            config: Conversion configuration with MinerU settings
        """
        super().__init__(config)
        self.mineru_config = config.mineru_config
        self.extract_dir: Optional[Path] = (
            None  # Store extraction directory path
        )

        if not self.mineru_config.api_token:
            raise ValueError("MinerU API token not provided in configuration")

    def can_handle(self, pdf_path: Path) -> bool:
        """
        MinerU can handle any PDF, but is best for complex layouts.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True (can always handle as fallback)
        """
        return True

    def extract(
        self, pdf_path: Path, segment: Optional[Segment] = None
    ) -> str:
        """
        Extract text from PDF using MinerU API.

        Args:
            pdf_path: Path to the PDF file
            segment: Optional segment (not used, MinerU processes full files)

        Returns:
            Markdown formatted text

        Raises:
            Exception: If API request fails
        """
        # Upload file and get batch_id
        batch_id = self._upload_file(pdf_path)

        # Wait for processing
        result = self._wait_for_result(batch_id)

        # Download and extract markdown
        markdown = self._download_markdown(result)

        return markdown

    def extract_batch(self, pdf_paths: List[Path]) -> Dict[str, str]:
        """
        Extract text from multiple PDFs in a batch.

        Args:
            pdf_paths: List of PDF file paths

        Returns:
            Dictionary mapping file paths to markdown content
        """
        # Upload all files
        batch_id = self._upload_files(pdf_paths)

        # Wait for all to complete
        results = self._wait_for_batch_results(batch_id)

        # Download all markdowns
        markdown_dict = {}
        for pdf_path, result in zip(pdf_paths, results):
            if result["state"] == "done":
                markdown = self._download_markdown(result)
                markdown_dict[str(pdf_path)] = markdown
            else:
                markdown_dict[str(pdf_path)] = (
                    f"Error: {result.get('err_msg', 'Unknown error')}"
                )

        return markdown_dict

    def _apply_upload_url(
        self, file_name: str, data_id: str
    ) -> Dict[str, Any]:
        """
        Apply for upload URL for a single file.

        Args:
            file_name: Name of the file
            data_id: Business data identifier

        Returns:
            API response with upload URL and batch_id
        """
        url = f"{self.mineru_config.api_base_url}/file-urls/batch"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.mineru_config.api_token}",
        }
        data = {
            "files": [{"name": file_name, "data_id": data_id}],
            "model_version": self.mineru_config.model_version,
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def _apply_upload_urls(self, file_names: List[str]) -> Dict[str, Any]:
        """
        Apply for upload URLs for multiple files.

        Args:
            file_names: List of file names

        Returns:
            API response with upload URLs and batch_id
        """
        url = f"{self.mineru_config.api_base_url}/file-urls/batch"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.mineru_config.api_token}",
        }
        data = {
            "files": [
                {"name": name, "data_id": f"pdf_{i}"}
                for i, name in enumerate(file_names)
            ],
            "model_version": self.mineru_config.model_version,
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def _upload_file_to_url(self, file_path: Path, upload_url: str) -> bool:
        """
        Upload file to the provided URL.

        Args:
            file_path: Path to the file
            upload_url: Pre-signed upload URL

        Returns:
            True if successful
        """
        with open(file_path, "rb") as f:
            response = requests.put(upload_url, data=f, timeout=300)
            return response.status_code == 200

    def _upload_file(self, pdf_path: Path) -> str:
        """
        Upload a single PDF file to MinerU.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            batch_id for tracking the job
        """
        file_name = pdf_path.name
        data_id = f"pdf_{pdf_path.stem}"

        # Get upload URL
        result = self._apply_upload_url(file_name, data_id)

        if result["code"] != 0:
            raise Exception(f"Failed to get upload URL: {result}")

        batch_id = result["data"]["batch_id"]
        upload_url = result["data"]["file_urls"][0]

        # Upload file
        success = self._upload_file_to_url(pdf_path, upload_url)
        if not success:
            raise Exception(f"Failed to upload file: {pdf_path}")

        return batch_id

    def _upload_files(self, pdf_paths: List[Path]) -> str:
        """
        Upload multiple PDF files to MinerU.

        Args:
            pdf_paths: List of PDF file paths

        Returns:
            batch_id for tracking the jobs
        """
        file_names = [p.name for p in pdf_paths]

        # Get upload URLs
        result = self._apply_upload_urls(file_names)

        if result["code"] != 0:
            raise Exception(f"Failed to get upload URLs: {result}")

        batch_id = result["data"]["batch_id"]
        upload_urls = result["data"]["file_urls"]

        # Upload all files
        for pdf_path, upload_url in zip(pdf_paths, upload_urls):
            success = self._upload_file_to_url(pdf_path, upload_url)
            if not success:
                raise Exception(f"Failed to upload file: {pdf_path}")

        return batch_id

    def _get_batch_results(self, batch_id: str) -> Dict[str, Any]:
        """
        Query batch processing results.

        Args:
            batch_id: Batch identifier

        Returns:
            API response with results
        """
        url = f"{self.mineru_config.api_base_url}/extract-results/batch/{batch_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.mineru_config.api_token}",
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def _wait_for_result(
        self, batch_id: str, poll_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Wait for a single file to be processed.

        Args:
            batch_id: Batch identifier
            poll_interval: Seconds between polling

        Returns:
            Result dictionary for the file
        """
        start_time = time.time()

        while True:
            if time.time() - start_time > self.mineru_config.timeout:
                raise TimeoutError(
                    f"Processing timeout after {self.mineru_config.timeout}s"
                )

            results = self._get_batch_results(batch_id)

            if results["code"] == 0:
                extract_results = results["data"]["extract_result"]
                if extract_results:
                    result = extract_results[0]
                    if result["state"] == "done":
                        return result
                    elif result["state"] == "failed":
                        raise Exception(
                            f"Processing failed: {result.get('err_msg', 'Unknown error')}"
                        )

            time.sleep(poll_interval)

    def _wait_for_batch_results(
        self, batch_id: str, poll_interval: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Wait for all files in a batch to be processed.

        Args:
            batch_id: Batch identifier
            poll_interval: Seconds between polling

        Returns:
            List of result dictionaries
        """
        start_time = time.time()

        while True:
            if time.time() - start_time > self.mineru_config.timeout:
                raise TimeoutError(
                    f"Processing timeout after {self.mineru_config.timeout}s"
                )

            results = self._get_batch_results(batch_id)

            if results["code"] == 0:
                extract_results = results["data"]["extract_result"]
                # Check if all are done or failed
                all_finished = all(
                    r["state"] in ["done", "failed"] for r in extract_results
                )
                if all_finished:
                    return extract_results

            time.sleep(poll_interval)

    def _download_markdown(self, result: Dict[str, Any]) -> str:
        """
        Download and extract markdown from result.

        Args:
            result: Result dictionary from API

        Returns:
            Markdown content
        """
        zip_url = result["full_zip_url"]

        # Download ZIP
        response = requests.get(zip_url, timeout=60)
        response.raise_for_status()

        # Save temporarily and extract
        # temp_zip = Path("/tmp") / f"{result['data_id']}.zip"
        # temp_zip = Path("output") / f"{result['data_id']}.zip"
        pdf_dir = self.config.output_dir or Path.cwd()
        temp_zip = pdf_dir / "outputs" / f"{result['data_id']}.zip"
        temp_zip.parent.mkdir(parents=True, exist_ok=True)
        print(f"Saving ZIP to: {temp_zip}")
        with open(temp_zip, "wb") as f:
            f.write(response.content)

        # Extract and read markdown
        extract_dir = temp_zip.parent / result["data_id"]
        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Store extraction directory path for later use
        self.extract_dir = extract_dir

        # Find markdown file (typically named auto/output.md or similar)
        markdown_files = list(extract_dir.rglob("*.md"))
        if not markdown_files:
            raise Exception("No markdown file found in result")

        # Read the first markdown file
        markdown_content = markdown_files[0].read_text(encoding="utf-8")

        # Clean up temporary files
        # temp_zip.unlink()

        return markdown_content
