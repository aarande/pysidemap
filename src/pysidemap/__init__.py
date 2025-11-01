"""PySideMap - PySide6 GIS Visualization Widget

A production-ready PySide6 GIS visualization widget for seamless integration 
with PySide6 applications while supporting multiple geospatial data formats, 
coordinate transformations, and interactive map operations.

Main Classes:
- GISGraphicsView: Main widget class inheriting from QGraphicsView
- BaseLayer: Abstract base class for spatial data layers
- RasterLayer: Raster data layer implementation
- VectorLayer: Vector data layer implementation
"""

from .widgets.gis_graphics_view import GISGraphicsView
from .layers.base_layer import BaseLayer
from .layers.raster_layer import RasterLayer
from .layers.vector_layer import VectorLayer
from .coordinate_systems.crs_manager import CRSManager
from .exceptions import (
    DataLoadError,
    CRSError, 
    MemoryError,
    NetworkError,
    ValidationError
)

__version__ = "0.1.0"
__all__ = [
    "GISGraphicsView",
    "BaseLayer", 
    "RasterLayer",
    "VectorLayer",
    "CRSManager",
    "DataLoadError",
    "CRSError",
    "MemoryError", 
    "NetworkError",
    "ValidationError"
]