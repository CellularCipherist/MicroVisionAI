from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Depends, HTTPException, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
import os
import shutil
import tempfile
import logging
import aiofiles
from app.services import image_service, imagej_service
from app.database import get_db, ImageMetadata
from app.config import load_config
from typing import List

logger = logging.getLogger(__name__)
config = load_config()

class ImageRouteHandler:
    def __init__(self, image_service, imagej_service):
        """
        Handles image-related routes, including uploading, deleting, and executing macros on images.
        """
        self.image_service = image_service
        self.imagej_service = imagej_service
        self.logger = logger

    async def upload_image(
        self,
        background_tasks: BackgroundTasks,
        files: List[UploadFile] = File(...),
        execute_macro: bool = Form(False),
        macro_script: str = Form(None),
        db: Session = Depends(get_db)
    ) -> JSONResponse:
        """
        Handles uploading of images, with optional macro execution.
        """
        self.logger.info(f"Received files: {[file.filename for file in files]}")

        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")

        try:
            if execute_macro and macro_script:
                return await self.handle_execute_macro(files, macro_script, background_tasks)
            else:
                return await self.handle_initial_upload(files, background_tasks, db)
        except HTTPException as he:
            db.rollback()
            self.logger.error(f"HTTPException during processing files: {str(he)}", exc_info=True)
            raise he
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error processing files: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error processing files.")

    async def handle_initial_upload(
        self,
        files: List[UploadFile],
        background_tasks: BackgroundTasks,
        db: Session
    ) -> JSONResponse:
        """
        Handles the initial upload of images without macro execution.
        """
        results = []
        for file in files:
            temp_dir = tempfile.mkdtemp()
            try:
                original_path = os.path.join(temp_dir, file.filename)
                async with aiofiles.open(original_path, "wb") as buffer:
                    await buffer.write(await file.read())
                self.logger.info(f"Saved original file to: {original_path}")

                processed_data = await self.image_service.process_image(
                    original_path, background_tasks, file.filename
                )
                preview = await self.image_service.generate_image_preview(processed_data['preview_path'])

                db_metadata = ImageMetadata(
                    file_name=processed_data['unique_filename'],
                    original_path=processed_data['original_path'],
                    preview_path=processed_data['preview_path'],
                    image_metadata=processed_data['metadata'],
                    file_type=processed_data['file_type']
                )
                db.add(db_metadata)
                db.commit()

                self.logger.info(f"Successfully processed and saved file: {file.filename}")

                results.append({
                    "filename": file.filename,
                    "unique_filename": processed_data['unique_filename'],
                    "preview": preview,
                    "metadata": processed_data['metadata'],
                    "file_type": processed_data['file_type']
                })

            except Exception as e:
                self.logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
                db.rollback()
                results.append({
                    "filename": file.filename,
                    "error": str(e)
                })
            finally:
                background_tasks.add_task(shutil.rmtree, temp_dir)

        return JSONResponse(content={"results": results})

    async def delete_image(
        self,
        filename: str,
        db: Session = Depends(get_db)
    ) -> JSONResponse:
        """
        Deletes an image and its metadata from the database and file system.
        """
        try:
            image_metadata = db.query(ImageMetadata).filter(ImageMetadata.file_name == filename).first()
            if not image_metadata:
                raise HTTPException(status_code=404, detail="Image not found")

            # Delete files if they exist
            for path in [image_metadata.original_path, image_metadata.preview_path]:
                if os.path.exists(path):
                    os.remove(path)
                    self.logger.info(f"Deleted file: {path}")

            db.delete(image_metadata)
            db.commit()
            return JSONResponse(content={"message": "Image deleted successfully"})
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deleting image {filename}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error deleting image.")

    async def handle_execute_macro(
        self,
        files: List[UploadFile],
        macro_script: str,
        background_tasks: BackgroundTasks
    ) -> StreamingResponse:
        """
        Executes a macro script on the uploaded images and returns the results as a ZIP file.
        """
        self.logger.info("Executing macro script...")
        zip_path, error_logs = await self.imagej_service.execute_image_macro(
            files, macro_script, {}, background_tasks
        )

        if zip_path and os.path.exists(zip_path):
            self.logger.info(f"Macro executed successfully, results stored at: {zip_path}")

            async def iterfile():
                async with aiofiles.open(zip_path, mode="rb") as file_like:
                    chunk = await file_like.read(1024 * 1024)
                    while chunk:
                        yield chunk
                        chunk = await file_like.read(1024 * 1024)

            return StreamingResponse(
                iterfile(),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename=results.zip"}
            )
        else:
            self.logger.error("Failed to execute macro or generate results ZIP")
            raise HTTPException(status_code=500, detail="Failed to execute macro.")

    async def get_image_preview(
        self,
        filename: str,
        db: Session = Depends(get_db)
    ) -> JSONResponse:
        """
        Fetches a base64-encoded preview image for the given filename.
        """
        try:
            image_metadata = db.query(ImageMetadata).filter(ImageMetadata.file_name == filename).first()
            if not image_metadata or not os.path.exists(image_metadata.preview_path):
                raise HTTPException(status_code=404, detail="Preview not found")

            preview = await self.image_service.generate_image_preview(image_metadata.preview_path)
            return JSONResponse(content={"preview": preview})

        except Exception as e:
            self.logger.error(f"Error generating image preview for {filename}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error generating image preview.")

# Instantiate the handler
image_handler = ImageRouteHandler(image_service, imagej_service)

# Define the API router and map routes to handler methods
router = APIRouter()
router.get("/get-image-preview/{filename}")(image_handler.get_image_preview)
router.post("/upload-image/")(image_handler.upload_image)
router.delete("/delete-image/{filename}")(image_handler.delete_image)
