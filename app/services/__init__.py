# app/services/__init__.py

from .imagej_service import imagej_service
from .atlas_service import (
    generate_improved_prompt,
    generate_macro_from_prompt
)
from .file_service import file_service
from .image_service import image_service

# Set file_service in imagej_service
imagej_service.set_file_service(file_service)

__all__ = [
    'imagej_service',
    'image_service',
    'file_service',
    'generate_improved_prompt',
    'generate_macro_from_prompt',
]
