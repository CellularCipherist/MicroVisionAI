import os
import io
import base64
import tempfile
import logging
import uuid
import asyncio
import scyjava
from typing import Dict, Tuple
from fastapi import HTTPException, BackgroundTasks
from PIL import Image, UnidentifiedImageError
from app.services import imagej_service, file_service
from ..config import load_config

class ImageService:
    def __init__(self):
        self.config = load_config()
        self.logger = logging.getLogger(__name__)

    def _load_macro_template(self, input_path: str, output_dir: str, filename: str, output_log_path: str) -> str:
        template_path = self.config.get('paths.conversion_template')
        if not os.path.exists(template_path):
            raise RuntimeError(f"Macro template does not exist at: {template_path}")

        with open(template_path, 'r') as template_file:
            macro_template = template_file.read()

        try:
            formatted_macro = macro_template.format(
                input_path=input_path.replace('\\', '/'),
                output_dir=output_dir.replace('\\', '/'),
                filename=os.path.splitext(filename)[0],
                output_log_path=output_log_path.replace('\\', '/')
            )
        except KeyError as e:
            self.logger.error(f"Error formatting macro template: {e}")
            raise RuntimeError(f"Macro template formatting error: {e}")

        return formatted_macro

    async def process_image(self, original_path: str, background_tasks: BackgroundTasks, filename: str) -> Dict:
        self.logger.info(f"Processing image: {filename}")

        try:
            file_uuid = str(uuid.uuid4())
            unique_filename = f"{file_uuid}_{filename}"
            result = await self.run_preview_macro(original_path, os.path.dirname(original_path), unique_filename, background_tasks)

            return {
                'metadata': result['metadata'],
                'preview_path': result['preview_path'],
                'original_path': original_path,
                'file_type': os.path.splitext(filename)[1][1:],
                'unique_filename': unique_filename
            }
        except Exception as e:
            self.logger.error(f"Failed to process image: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

    async def run_preview_macro(self, input_path: str, output_dir: str, filename: str, background_tasks: BackgroundTasks) -> Dict:
        self.logger.info(f"Running headless preview macro for file: {filename}")

        temp_dir = tempfile.mkdtemp()
        output_log_path = os.path.join(temp_dir, "output_log.txt")

        try:
            IJ, BF = imagej_service.get_imagej_objects()
            user_macro = self._load_macro_template(input_path, output_dir, filename, output_log_path)

            self.logger.info("Executing macro script...")
            output = IJ.runMacro(user_macro)
            output = scyjava.to_python(output) if output is not None else ""
            self.logger.info(f"Macro output: {output}")

            # Wait for the log file to be created and written
            log_content = await self._wait_for_file_content(output_log_path, timeout=60)

            metadata, preview_path = self._extract_paths_from_log(log_content)

            # Wait for the preview file to be created
            await self._wait_for_file(preview_path, timeout=120)

            if not os.path.exists(preview_path):
                raise ValueError(f"Preview image was not generated or found at: {preview_path}")

            return {
                'metadata': metadata,
                'preview_path': preview_path
            }

        except Exception as e:
            self.logger.error(f"Error in run_preview_macro: {str(e)}", exc_info=True)
            if os.path.exists(output_log_path):
                with open(output_log_path, 'r') as log_file:
                    self.logger.error(f"Output log file contents: {log_file.read()}")
            raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")
        finally:
            background_tasks.add_task(file_service.cleanup_temp_files, temp_dir)

    async def _wait_for_file(self, file_path: str, timeout: int = 120, check_interval: float = 1.0) -> None:
        start_time = asyncio.get_event_loop().time()
        while not os.path.exists(file_path):
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"File not created within {timeout} seconds: {file_path}")
            await asyncio.sleep(check_interval)

        # Additional check for file size
        file_size = 0
        for _ in range(10):  # Check file size stability for 10 seconds
            current_size = os.path.getsize(file_path)
            if current_size > 0 and current_size == file_size:
                return  # File size is stable and non-zero
            file_size = current_size
            await asyncio.sleep(1)

        if file_size == 0:
            raise ValueError(f"File created but empty: {file_path}")

    async def _wait_for_file_content(self, file_path: str, timeout: int = 60, check_interval: float = 1.0) -> str:
        start_time = asyncio.get_event_loop().time()
        content = ""
        while not content:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"File content not available within {timeout} seconds: {file_path}")
            try:
                with open(file_path, 'r') as file:
                    content = file.read().strip()
            except (FileNotFoundError, PermissionError):
                pass
            if not content:
                await asyncio.sleep(check_interval)
        return content

    def _extract_paths_from_log(self, log_content: str) -> Tuple[Dict, str]:
        metadata_path = None
        preview_path = None
        metadata = {}

        for line in log_content.split('\n'):
            line = line.strip()
            if line.startswith('METADATA_PATH:'):
                metadata_path = line.split(':', 1)[1].strip()
            elif line.startswith('PREVIEW_PATH:'):
                preview_path = line.split(':', 1)[1].strip()

        if metadata_path and os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = {'raw': f.read()}
        else:
            self.logger.warning(f"Metadata file not found at expected path: {metadata_path}")

        return metadata, preview_path

    async def generate_image_preview(self, file_path: str) -> str:
        try:
            with Image.open(file_path) as img:
                img = img.convert('RGB') if img.mode not in ['RGB', 'L'] else img
                img.thumbnail((200, 200))
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode()
                return f"data:image/png;base64,{img_str}"
        except UnidentifiedImageError:
            self.logger.error(f"Failed to identify image format for file: {file_path}")
            raise HTTPException(status_code=400, detail="Failed to identify the image format.")
        except Exception as e:
            self.logger.error(f"Failed to generate image preview: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to generate image preview: {str(e)}")

# Initialize the service
image_service = ImageService()
