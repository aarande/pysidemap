"""PySideMap Utilities Package

This package contains utility modules for spatial data processing,
coordinate transformations, and general helper functions.
"""

# Phase 2 - Available components
from .types import (
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
    create_layer_config,
    CoordinateLike,
    BoundingBoxLike,
    GeometryLike
)

# Future utilities (later phases)
# from .spatial_index import SpatialIndex
# from .gdal_utils import GdalUtils

__all__ = [
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
    "CoordinateLike",
    "BoundingBoxLike", 
    "GeometryLike",
    # Future exports
    # "SpatialIndex",
    # "GdalUtils"
]