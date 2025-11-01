"""PySideMap - PySide6 GIS Visualization Widget

A production-ready PySide6 GIS visualization widget for seamless integration 
with PySide6 applications while supporting multiple geospatial data formats, 
coordinate transformations, and interactive map operations.

Main Classes (Phase 2 - Foundational Infrastructure):
- Exceptions: Comprehensive error handling for all GIS operations
- Types: Core spatial data type definitions (Coordinate, BoundingBox, Geometry, etc.)
- CRSManager: Coordinate reference system management with pyproj integration
- BaseLayer: Abstract base class for spatial data layers
- RasterLayer: Raster data layer implementation
- GISGraphicsView: Core GIS widget inheriting from QGraphicsView

This completes Phase 2! Ready for User Story 1 (Phase 3).
"""

# Phase 2 - Available components
from .exceptions import (
    PySideMapError,
    DataLoadError,
    CRSError, 
    MemoryError,
    NetworkError,
    ValidationError,
    InitializationError,
    PerformanceError
)

from .utils.types import (
    Coordinate,
    BoundingBox,
    Geometry,
    LayerConfig,
    Feature,
    GeometryType,
    LayerType,
    create_coordinate,
    create_bounding_box,
    create_geometry,
    create_layer_config
)

from .coordinate_systems import (
    CRSManager,
    CRSInfo,
    WGS84,
    WEB_MERCATOR,
    create_coordinate_in_crs,
    wgs84_to_web_mercator,
    web_mercator_to_wgs84
)

from .layers import (
    BaseLayer,
    RasterLayer,
    LayerState,
    LayerEventType,
    LayerEvent,
    BaseLayerError,
    RasterLayerError,
    create_raster_layer
)

from .widgets import (
    GISGraphicsView,
    ViewState,
    InteractionMode,
    ViewportInfo,
    GISViewError,
    create_gis_view
)

__version__ = "0.1.0"
__all__ = [
    # Exceptions
    "PySideMapError",
    "DataLoadError",
    "CRSError",
    "MemoryError", 
    "NetworkError",
    "ValidationError",
    "InitializationError",
    "PerformanceError",
    # Types
    "Coordinate",
    "BoundingBox",
    "Geometry",
    "LayerConfig",
    "Feature",
    "GeometryType",
    "LayerType",
    "create_coordinate",
    "create_bounding_box", 
    "create_geometry",
    "create_layer_config",
    # Coordinate Systems
    "CRSManager",
    "CRSInfo",
    "WGS84",
    "WEB_MERCATOR",
    "create_coordinate_in_crs",
    "wgs84_to_web_mercator",
    "web_mercator_to_wgs84",
    # Layers
    "BaseLayer",
    "RasterLayer",
    "LayerState",
    "LayerEventType",
    "LayerEvent",
    "BaseLayerError",
    "RasterLayerError",
    "create_raster_layer",
    # Widgets
    "GISGraphicsView",
    "ViewState",
    "InteractionMode",
    "ViewportInfo",
    "GISViewError",
    "create_gis_view"
]