import logging
import os
import asyncio
from typing import Optional, Tuple, Any
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from .config import load_config
from .services import imagej_service, image_service, file_service
from .routes import image_routes, chat_routes

class AtlasApplication:
    """FastAPI application wrapper for Atlas image processing service."""

    def __init__(self) -> None:
        """Initialize Atlas application with configuration and services."""
        self.app: FastAPI = FastAPI(
            title="Atlas Image Processing",
            description="AI-powered ImageJ macro generation service",
            version="0.1.0"
        )
        self.config: dict = load_config()
        self.logger: logging.Logger = self._setup_logging()
        self.imagej_service = imagej_service
        self.templates: Optional[Jinja2Templates] = None
        self.macro_template: Optional[str] = None
        self.PROJECT_ROOT: Path = Path(__file__).parent.parent
        self.IJ: Optional[Any] = None
        self.BF: Optional[Any] = None

        # Configure CORS
        origins = self.config.get('cors.origins', ["http://localhost:8000"])
        self._setup_cors(origins)

    def _setup_cors(self, origins: list) -> None:
        """Configure CORS middleware with security settings."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "X-Requested-With"
            ],
            expose_headers=["*"]
        )

    def _setup_logging(self) -> logging.Logger:
        """Configure application logging."""
        log_level = self.config.get('logging.level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _mount_static_files(self) -> None:
        """Mount static file directory."""
        static_dir = self.PROJECT_ROOT / self.config.get('paths.static_dir', 'app/static')
        if not static_dir.exists():
            raise RuntimeError(f"Static directory not found: {static_dir}")
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        self.logger.info(f"Static files mounted: {static_dir}")

    def _setup_templates(self) -> None:
        """Configure Jinja2 templates."""
        template_dir = self.PROJECT_ROOT / self.config.get('paths.template_dir', 'app/templates')
        if not template_dir.exists():
            raise RuntimeError(f"Template directory not found: {template_dir}")
        self.templates = Jinja2Templates(directory=str(template_dir))
        self.logger.info(f"Templates configured: {template_dir}")

    def _load_macro_template(self) -> None:
        """Load ImageJ macro template."""
        template_path = Path(self.config.get('paths.macro_template'))
        if not template_path.exists():
            raise RuntimeError(f"Macro template not found: {template_path}")
        self.macro_template = template_path.read_text()
        self.logger.info(f"Macro template loaded: {template_path}")

    def _include_routers(self) -> None:
        """Include API route handlers."""
        self.app.include_router(
            image_routes.router,
            prefix="/api/v1",
            tags=["images"]
        )
        self.app.include_router(
            chat_routes.router,
            prefix="/api/v1",
            tags=["chat"]
        )
        self.logger.info("API routes configured")

    async def startup_event(self) -> None:
        """Initialize services on application startup."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.imagej_service.initialize)
            self.IJ, self.BF = self.imagej_service.get_imagej_objects()
            self.logger.info("ImageJ service initialized")
        except Exception as e:
            self.logger.critical(f"ImageJ initialization failed: {e}")
            raise RuntimeError("Critical startup error: ImageJ initialization failed")

    async def shutdown_event(self) -> None:
        """Clean up services on application shutdown."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.imagej_service.shutdown
            )
            self.logger.info("ImageJ service shutdown complete")
        except Exception as e:
            self.logger.error(f"ImageJ shutdown error: {e}")

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application instance."""
        try:
            self._mount_static_files()
            self._setup_templates()
            self._load_macro_template()
            self._include_routers()
            self.app.add_event_handler("startup", self.startup_event)
            self.app.add_event_handler("shutdown", self.shutdown_event)
            self._setup_root_endpoint()
            self.logger.info("Application successfully created")
            return self.app
        except Exception as e:
            self.logger.critical(f"Application creation failed: {e}")
            raise

    def _setup_root_endpoint(self) -> None:
        """Configure root endpoint."""
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root(request: Request) -> HTMLResponse:
            """Serve the application frontend."""
            return self.templates.TemplateResponse("index.html", {"request": request})


# Create application instance
atlas_app = AtlasApplication()
app = atlas_app.create_app()
