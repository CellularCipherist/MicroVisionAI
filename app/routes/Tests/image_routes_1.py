"""
Image routes module for handling image upload, processing, and metadata management in the FastAPI application.
"""

import os
import logging
from typing import List, Dict
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from app.services import imagej_service, image_service
from app.config import load_config
from app.dependencies import get_db
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)

config = load_config()

# In-memory storage for metadata (replace with database in production)
image_metadata: Dict[str, Dict] = {}

@router.post("/upload-image/")
async def upload_image(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    macro_script: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process images using the provided macro script.

    Args:
        background_tasks (BackgroundTasks): FastAPI background tasks.
        files (List[UploadFile]): List of uploaded image files.
        macro_script (str, optional): The ImageJ macro script to be executed.
        db (Session): Database session.

    Returns:
        StreamingResponse: A ZIP file containing the processed images and results.

    Raises:
        HTTPException: If no files are uploaded or if there's an error during processing.
    """
    logger.info(f"Received files: {[file.filename for file in files]}")
    logger.info(f"Received macro script: {macro_script}")

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    try:
        # Extract metadata for each file
        for file in files:
            preview_data = await image_service.generate_image_preview(file)
            image_metadata[file.filename] = preview_data['metadata']

        # TODO: Store metadata in the database instead of in-memory
        # for file_name, metadata in image_metadata.items():
        #     db_metadata = models.ImageMetadata(file_name=file_name, metadata=metadata)
        #     db.add(db_metadata)
        # db.commit()

        zip_path, error_logs = await imagej_service.execute_image_macro(files, macro_script, image_metadata, background_tasks)
        logger.info(f"Received zip_path: {zip_path}")

        if zip_path and os.path.exists(zip_path):
            file_size = os.path.getsize(zip_path)
            logger.info(f"ZIP file exists. Size: {file_size} bytes")

            def iterfile():
                with open(zip_path, mode="rb") as file_like:
                    yield from file_like

            return StreamingResponse(
                iterfile(),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename=results.zip"}
            )
        else:
            logger.error(f"ZIP file not found or empty: {zip_path}")
            raise HTTPException(status_code=500, detail="Failed to process images")

    except Exception as e:
        logger.error(f"Error processing images: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing the images: {str(e)}")

@router.post("/get_image_preview/")
async def get_image_preview(file: UploadFile = File(...)):
    """
    Generate a preview of the uploaded image and return its metadata.

    Args:
        file (UploadFile): The uploaded image file.

    Returns:
        JSONResponse: A JSON object containing the base64-encoded image preview and metadata.

    Raises:
        HTTPException: If there's an error generating the preview or extracting metadata.
    """
    try:
        preview_data = await image_service.generate_image_preview(file)
        return JSONResponse(content=preview_data)
    except HTTPException as e:
        logger.error(f"Failed to generate preview: {str(e.detail)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during preview generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while generating the preview")

@router.get("/get_all_metadata/")
async def get_all_metadata():
    """
    Retrieve metadata for all uploaded images.

    Returns:
        JSONResponse: A JSON object containing metadata for all uploaded images.
    """
    return JSONResponse(content=image_metadata)

# Shutdown hook to clean up resources
@router.on_event("shutdown")
def shutdown_event():
    image_service.shutdown()
