import os
import zipfile
import logging
import asyncio
import aiofiles
from typing import List, Optional, Set
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor
from functools import partial

logger = logging.getLogger(__name__)

class FileService:
    """
    Service for handling file operations in the FastAPI application.

    Provides asynchronous file operations including:
    - File creation monitoring
    - ZIP archive creation
    - Output file parsing
    - Temporary file cleanup
    """

    def __init__(self):
        self.logger = logger
        self._executor = ThreadPoolExecutor()

    async def wait_for_file(
        self,
        file_path: str,
        timeout: int = 60,
        check_interval: float = 0.5
    ) -> bool:
        """
        Wait asynchronously for a file to be created and written.

        Args:
            file_path: Path to the file to wait for
            timeout: Maximum time to wait in seconds
            check_interval: Interval between checks in seconds

        Returns:
            True if the file exists and is non-empty, False if timeout reached
        """
        path = Path(file_path)
        end_time = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < end_time:
            if path.exists() and path.stat().st_size > 0:
                return True
            await asyncio.sleep(check_interval)

        self.logger.warning(f"Timeout reached waiting for file: {path}")
        return False

    async def create_zip_file(
        self,
        file_paths: List[str],
        zip_filename: str
    ) -> Optional[str]:
        """
        Create a ZIP archive containing the specified files.

        Args:
            file_paths: List of file paths to include in the ZIP
            zip_filename: Name of the ZIP file to create

        Returns:
            Path to the created ZIP file, or None if creation failed
        """
        if not file_paths:
            self.logger.warning("No files provided for ZIP creation")
            return None

        try:
            zip_path = Path(zip_filename)

            def _create_zip(paths: List[str], zip_path: Path) -> Optional[str]:
                seen_files: Set[str] = set()

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in paths:
                        path = Path(file_path)
                        if not path.exists():
                            self.logger.warning(f"File not found, skipping: {path}")
                            continue

                        if str(path) in seen_files:
                            self.logger.warning(f"Duplicate file skipped: {path}")
                            continue

                        arcname = path.relative_to(zip_path.parent)
                        zipf.write(path, arcname)
                        seen_files.add(str(path))
                        self.logger.debug(f"Added to ZIP: {arcname}")

                if zip_path.exists():
                    size = zip_path.stat().st_size
                    self.logger.info(f"ZIP created successfully: {zip_path} ({size} bytes)")
                    return str(zip_path)

                self.logger.error(f"ZIP file not found after creation: {zip_path}")
                return None

            return await asyncio.get_event_loop().run_in_executor(
                self._executor,
                partial(_create_zip, file_paths, zip_path)
            )

        except Exception as e:
            self.logger.error(f"Error creating ZIP file: {str(e)}", exc_info=True)
            return None

    async def parse_saved_files(
        self,
        output: str,
        temp_dir: str,
        original_filename: str
    ) -> List[str]:
        """
        Parse output log and collect saved files.

        Args:
            output: Output log from the ImageJ macro
            temp_dir: Temporary directory containing saved files
            original_filename: Original filename of the processed image

        Returns:
            List of paths to valid output files
        """
        files: Set[str] = set()
        temp_path = Path(temp_dir)
        log_file = temp_path / "output_log.txt"

        if log_file.exists():
            async with aiofiles.open(log_file, 'r') as f:
                async for line in f:
                    if line.startswith("OUTPUT_FILE:"):
                        file_path = Path(
                            line[len("OUTPUT_FILE:"):].strip().replace('//', '/')
                        ).resolve()

                        if file_path.exists() and file_path.stat().st_size > 0:
                            files.add(str(file_path))
                            self.logger.info(f"Valid output file found: {file_path}")
                        else:
                            self.logger.warning(f"Invalid or empty file: {file_path}")

        # Collect files from subdirectories
        for path in temp_path.rglob(f"{original_filename}*"):
            if path.is_file() and path.stat().st_size > 0:
                files.add(str(path))
            elif path.is_file():
                self.logger.warning(f"Empty file skipped: {path}")

        if not files:
            self.logger.warning(f"No valid files found for {original_filename}")

        return list(files)

    async def cleanup_temp_files(self, path: str, delay: int = 300) -> None:
        """
        Clean up temporary files and directories after a delay.

        Args:
            path: Path to temporary file or directory
            delay: Delay in seconds before cleanup
        """
        await asyncio.sleep(delay)
        try:
            path_obj = Path(path)
            if path_obj.is_dir():
                shutil.rmtree(path_obj)
                self.logger.info(f"Removed temporary directory: {path_obj}")
            elif path_obj.is_file():
                path_obj.unlink()
                self.logger.info(f"Removed temporary file: {path_obj}")
            else:
                self.logger.warning(f"Path not found for cleanup: {path_obj}")
        except Exception as e:
            self.logger.error(f"Cleanup failed for {path}: {str(e)}", exc_info=True)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with resource cleanup."""
        self._executor.shutdown(wait=True)


# Initialize service instance
file_service = FileService()
