"""
Image service module for handling image-related operations in the FastAPI application.
"""

import os
import tempfile
import io
import base64
import logging
from fastapi import UploadFile, HTTPException
from PIL import Image
import bioformats
import javabridge

logger = logging.getLogger(__name__)

# Initialize JavaBridge for bioformats
javabridge.start_vm(class_path=bioformats.JARS)

def is_bioformats_compatible(file_path):
    """
    Check if the file is compatible with bioformats.

    Args:
        file_path (str): Path to the image file.

    Returns:
        bool: True if compatible, False otherwise.
    """
    try:
        with bioformats.ImageReader(file_path) as reader:
            return True
    except Exception:
        return False

def extract_metadata(file_path, file_name):
    """
    Extract metadata from the image file.

    Args:
        file_path (str): Path to the image file.
        file_name (str): Name of the uploaded file.

    Returns:
        dict: Extracted metadata.
    """
    metadata = {'file_name': file_name}
    try:
        omexml = bioformats.get_omexml_metadata(file_path)
        metadata['ome_metadata'] = omexml
        # Add more specific metadata extraction as needed
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}")
    return metadata

async def generate_image_preview(file: UploadFile) -> dict:
    """
    Generate a base64-encoded preview of the uploaded image file.
    Convert bioformats-compatible files to PNG before encoding.

    Args:
        file (UploadFile): The uploaded image file.

    Returns:
        dict: A dictionary containing the base64-encoded preview data and metadata.

    Raises:
        HTTPException: If there's an error generating the preview.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(await file.read())
            temp_file.flush()

            if is_bioformats_compatible(temp_file.name):
                with bioformats.ImageReader(temp_file.name) as reader:
                    image = reader.read()
                    png_buffer = io.BytesIO()
                    Image.fromarray(image).save(png_buffer, format="PNG")
                    png_buffer.seek(0)
                    img_str = base64.b64encode(png_buffer.getvalue()).decode()
                    preview_data = f"data:image/png;base64,{img_str}"
                    logger.info(f"Generated PNG preview for bioformats-compatible file: {file.filename}")
            else:
                image = Image.open(temp_file.name)
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                preview_data = f"data:image/png;base64,{img_str}"
                logger.info(f"Generated PNG preview for {file.filename}")

            metadata = extract_metadata(temp_file.name, file.filename)

        os.unlink(temp_file.name)
        return {"preview": preview_data, "metadata": metadata}

    except Exception as e:
        logger.error(f"Failed to generate image preview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image preview: {str(e)}")

# Shutdown JavaBridge when the application stops
def shutdown():
    javabridge.kill_vm()

# Make sure to call shutdown() when your application stops
