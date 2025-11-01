"""PySideMap Layers Package

This package contains layer implementations for spatial data visualization.
Layers provide the interface between data sources and the GIS graphics view.
"""

from .base_layer import (
    BaseLayer,
    LayerState,
    LayerEventType,
    LayerEvent,
    BaseLayerError,
    create_layer_from_config,
    validate_layer_compatibility
)

from .raster_layer import (
    RasterLayer,
    RasterDataType,
    RasterRenderingMode,
    RasterMetadata,
    TileConfig,
    RasterLayerError,
    create_raster_layer
)

# Future implementations (later phases)
# from .vector_layer import VectorLayer

__all__ = [
    # Base layer (Phase 2)
    'BaseLayer',
    'LayerState',
    'LayerEventType', 
    'LayerEvent',
    'BaseLayerError',
    'create_layer_from_config',
    'validate_layer_compatibility',
    # Raster layer (Phase 2)
    'RasterLayer',
    'RasterDataType',
    'RasterRenderingMode',
    'RasterMetadata',
    'TileConfig',
    'RasterLayerError',
    'create_raster_layer',
    # Future exports
    # 'VectorLayer'
]