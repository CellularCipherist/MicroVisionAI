# app/services/imagej_service.py

import os
import logging
import time
import asyncio
import aiofiles
import tempfile
from typing import List, Tuple, Optional, Dict, Any
from fastapi import UploadFile, BackgroundTasks, HTTPException
from werkzeug.utils import secure_filename
import imagej
import jpype
import scyjava
import sys
from pathlib import Path

from ..config import load_config
from app.services import file_service

logger = logging.getLogger(__name__)

class ImageJService:
    """Service class for handling ImageJ operations."""

    def __init__(self):
        """Initialize the ImageJService instance."""
        self.config = load_config()
        self.ij = None
        self.IJ = None
        self.BF = None
        self.logger = logger
        self.file_service = file_service

    def set_file_service(self, file_service):
        """Set the file service instance."""
        self.file_service = file_service

    def initialize(self, retries: int = 3, delay: int = 5):
        """
        Initialize ImageJ with retry mechanism.

        Args:
            retries (int): Number of retry attempts
            delay (int): Delay between retries in seconds

        Raises:
            RuntimeError: If initialization fails after all retries
        """
        for attempt in range(1, retries + 1):
            try:
                self.logger.info("Initializing ImageJ...")
                self.logger.debug(f"Python version: {sys.version}")
                self.logger.debug(f"JPype version: {jpype.__version__}")
                self.logger.debug(f"ImageJ version: {imagej.__version__}")

                start_time = time.time()

                self._configure_java_options()

                imagej_dir = self.config.get('paths.imagej_dir')
                self.logger.info(f"ImageJ directory: {imagej_dir}")

                self.ij = imagej.init(imagej_dir, mode='headless')
                self.logger.info("JVM started successfully")

                self.ij.ui().setHeadless(True)
                self.IJ, self.BF = self._import_imagej_classes()

                self._log_version_info()

                elapsed_time = time.time() - start_time
                self.logger.info(f"ImageJ initialized successfully in {elapsed_time:.2f} seconds.")
                break
            except Exception as e:
                self.logger.error(f"Failed to initialize ImageJ (Attempt {attempt}/{retries}): {str(e)}", exc_info=True)
                if attempt < retries:
                    self.logger.info(f"Retrying ImageJ initialization in {delay} seconds...")
                    time.sleep(delay)
                else:
                    self.logger.error("Exceeded maximum retries for ImageJ initialization.")
                    raise RuntimeError(f"Failed to initialize ImageJ after {retries} attempts.") from e

    def _configure_java_options(self):
        """Configure Java options for ImageJ initialization."""
        scyjava.config.add_option('-Xmx16g')
        scyjava.config.add_option('-Djava.awt.headless=true')

        bf_jar = self.config.get('paths.bioformats_dir')
        if bf_jar:
            scyjava.config.add_classpath(bf_jar)

    def _import_imagej_classes(self) -> Tuple[Any, Any]:
        """
        Import necessary ImageJ classes.

        Returns:
            Tuple containing IJ and BF objects
        """
        try:
            IJ = scyjava.jimport('ij.IJ')
            BF = scyjava.jimport('loci.plugins.BF')
            self.logger.info("ImageJ and Bio-Formats plugins imported successfully")
            return IJ, BF
        except Exception as e:
            self.logger.error(f"Failed to import ImageJ classes: {str(e)}", exc_info=True)
            raise

    def get_imagej_objects(self) -> Tuple[Any, Any]:
        """
        Get the IJ and BF objects if initialized.

        Returns:
            Tuple containing IJ and BF objects

        Raises:
            RuntimeError if ImageJ not initialized
        """
        if not self.IJ or not self.BF:
            raise RuntimeError("ImageJ has not been initialized. Call initialize() first.")
        return self.IJ, self.BF

    def _log_version_info(self):
        """Log version information for ImageJ and Bio-Formats."""
        self.logger.info(f"Fiji version: {self.ij.getVersion()}")
        bf_version = scyjava.jimport('loci.formats.FormatTools').VERSION
        self.logger.info(f"Bio-Formats version: {bf_version}")

    async def execute_image_macro(
        self,
        files: List[UploadFile],
        macro_script: str,
        macro_params: dict,
        background_tasks: BackgroundTasks
    ) -> Tuple[str, List[str]]:
        """
        Execute a macro script on the uploaded images and return results as ZIP.

        Args:
            files: List of uploaded image files
            macro_script: The macro script to execute
            macro_params: Parameters for the macro
            background_tasks: Background tasks for cleanup

        Returns:
            Tuple containing ZIP file path and error logs
        """
        if not self.file_service:
            raise RuntimeError("FileService is not initialized.")

        self.logger.info(f"Starting macro execution on {len(files)} files.")
        error_logs = []
        output_files = []
        temp_dir = tempfile.mkdtemp()

        try:
            # Create subdirectories
            subdirs = ['Images', 'Statistics', 'Metadata']
            for subdir in subdirs:
                os.makedirs(os.path.join(temp_dir, subdir), exist_ok=True)

            for file in files:
                image_filename = secure_filename(file.filename)
                original_filename = os.path.splitext(image_filename)[0]
                image_path = os.path.join(temp_dir, image_filename)
                await self._save_upload_file(file, image_path)

                try:
                    self.logger.info(f"Processing image: {image_path}")
                    full_macro = self._prepare_macro_script(
                        image_path=image_path,
                        temp_dir=temp_dir,
                        original_filename=original_filename,
                        user_macro=macro_script,
                        macro_params=macro_params
                    )

                    # Execute the macro
                    output = self.IJ.runMacro(full_macro) or self.IJ.getLog() or ""
                    self.logger.debug(f"Macro output:\n{output}")

                    # Parse saved files
                    saved_files = await self.file_service.parse_saved_files(output, temp_dir, original_filename)
                    self.logger.info(f"Saved files for {image_filename}: {saved_files}")
                    output_files.extend(saved_files)

                except Exception as e:
                    error_message = f"Error processing {image_filename}: {str(e)}"
                    error_logs.append(error_message)
                    self.logger.error(error_message, exc_info=True)

            if output_files:
                self.logger.info(f"Creating ZIP file with {len(output_files)} files.")
                zip_filename = os.path.join(temp_dir, 'results.zip')
                zip_path = await self.file_service.create_zip_file(output_files, zip_filename)
                if zip_path and os.path.exists(zip_path):
                    self.logger.info(f"ZIP file created successfully: {zip_path}")
                    return zip_path, error_logs
                else:
                    error_message = "Failed to create zip file."
                    self.logger.error(error_message)
                    error_logs.append(error_message)
                    raise HTTPException(status_code=500, detail=error_message)
            else:
                error_message = "No output files were generated."
                self.logger.error(error_message)
                error_logs.append(error_message)
                raise HTTPException(status_code=500, detail=error_message)

        finally:
            # Cleanup temporary files after the response is sent
            background_tasks.add_task(self.file_service.cleanup_temp_files, temp_dir)

    def _prepare_macro_script(
        self,
        image_path: str,
        temp_dir: str,
        original_filename: str,
        user_macro: str,
        macro_params: dict
    ) -> str:
        """
        Prepare the full macro script with variable definitions.

        Args:
            image_path: Path to the input image
            temp_dir: Temporary directory for outputs
            original_filename: Original filename without extension
            user_macro: User-provided macro script
            macro_params: Macro parameters

        Returns:
            Complete macro script ready for execution
        """
        var_definitions = f"""
        var inputPath = "{image_path}";
        var outputDir = "{temp_dir}{os.sep}";
        var originalFileName = "{original_filename}";
        var minSize = {macro_params.get('minSize', 10)};
        var maxSize = "{macro_params.get('maxSize', 'Infinity')}";
        var minCircularity = {macro_params.get('minCircularity', 0.00)};
        var maxCircularity = {macro_params.get('maxCircularity', 1.00)};
        """

        # Load and modify macro template
        macro_template_path = self.config.get('paths.macro_template')
        with open(macro_template_path, 'r') as template_file:
            macro_template = template_file.read()

        full_macro = var_definitions + macro_template.replace("{user_macro}", user_macro or "")
        self.logger.debug(f"Full macro script:\n{full_macro}")
        return full_macro

    async def _save_upload_file(self, file: UploadFile, destination: str):
        """
        Save an uploaded file to the specified destination.

        Args:
            file: The uploaded file
            destination: The destination path
        """
        try:
            async with aiofiles.open(destination, 'wb') as out_file:
                await out_file.write(await file.read())
            self.logger.info(f"File saved successfully: {destination}")
        except Exception as e:
            self.logger.error(f"Failed to save uploaded file to {destination}: {str(e)}", exc_info=True)
            raise

    def shutdown(self):
        """Shut down ImageJ and clean up resources."""
        if self.ij:
            self.ij.context().dispose()
            self.ij = None
            self.logger.info("ImageJ context disposed.")
        self.IJ = None
        self.BF = None
        self.logger.info("ImageJ shut down successfully.")


# Initialize service instances
imagej_service = ImageJService()
imagej_service.set_file_service(file_service)
