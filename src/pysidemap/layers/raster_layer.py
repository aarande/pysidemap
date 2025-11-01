"""
PySideMap Raster Layer

Simple raster layer implementation providing basic raster data handling
and foundation for tile loading and rendering.

This module provides:
- Basic raster layer with simple rendering (no reprojection yet)
- Support for basic tile loading patterns (foundation for Phase 3)
- Integration with base layer framework
- Raster-specific configuration and metadata management
"""

from typing import List, Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import time

from .base_layer import BaseLayer, LayerState, BaseLayerError
from ..utils.types import LayerConfig, BoundingBox, Feature, Coordinate, LayerType
from ..exceptions import DataLoadError, ValidationError


logger = logging.getLogger(__name__)


class RasterDataType(Enum):
    """Types of raster data sources."""
    XYZ_TILES = "xyz_tiles"
    WMS = "wms"
    GEOTIFF = "geotiff"
    PNG = "png"
    JPEG = "jpeg"
    UNKNOWN = "unknown"


class RasterRenderingMode(Enum):
    """Raster rendering modes."""
    TILE_BASED = "tile_based"  # For tile services (XYZ, WMS)
    IMAGE_BASED = "image_based"  # For single images (GeoTIFF, PNG)
    VECTOR_BASED = "vector_based"  # For rasterized vector data


@dataclass
class RasterMetadata:
    """Metadata for raster data.
    
    Attributes:
        width: Width in pixels
        height: Height in pixels
        bands: Number of bands (channels)
        data_type: Data type (e.g., uint8, float32)
        resolution: Spatial resolution (units per pixel)
        no_data_value: No data value
        color_map: Color mapping information
    """
    width: Optional[int] = None
    height: Optional[int] = None
    bands: int = 1
    data_type: str = "uint8"
    resolution: Optional[float] = None
    no_data_value: Optional[float] = None
    color_map: Optional[Dict[int, Tuple[int, int, int, int]]] = None  # value -> RGBA


@dataclass
class TileConfig:
    """Configuration for tile-based raster data.
    
    Attributes:
        url_template: URL template for tile requests
        min_zoom: Minimum zoom level
        max_zoom: Maximum zoom level
        tile_size: Tile size in pixels (default 256)
        attribution: Tile attribution text
        subdomains: List of subdomains for load balancing
    """
    url_template: str = ""
    min_zoom: int = 0
    max_zoom: int = 19
    tile_size: int = 256
    attribution: str = ""
    subdomains: List[str] = field(default_factory=list)


class RasterLayerError(BaseLayerError):
    """Exception for raster layer-specific errors."""
    pass


class RasterLayer(BaseLayer):
    """Basic raster layer implementation.
    
    This class provides a foundation for raster data visualization including
    tile-based services (XYZ, WMS) and single image files (GeoTIFF, PNG).
    
    For Phase 2, this provides basic layer framework integration.
    Phase 3 will add actual tile loading and rendering capabilities.
    
    Attributes:
        raster_config: Raster-specific configuration
        metadata: Raster metadata
        rendering_mode: How to render the raster data
    """
    
    def __init__(self, 
                 config: LayerConfig,
                 raster_config: Optional[Dict[str, Any]] = None,
                 metadata: Optional[RasterMetadata] = None,
                 rendering_mode: RasterRenderingMode = RasterRenderingMode.TILE_BASED,
                 **kwargs):
        """Initialize raster layer.
        
        Args:
            config: Layer configuration
            raster_config: Raster-specific configuration
            metadata: Raster metadata
            rendering_mode: Rendering mode
            **kwargs: Additional arguments passed to BaseLayer
            
        Raises:
            RasterLayerError: If configuration is invalid
        """
        # Ensure this is a raster layer type
        if config.layer_type != LayerType.RASTER:
            raise ValidationError(
                f"RasterLayer requires RASTER layer type, got {config.layer_type}",
                expected_type="RASTER",
                field_name="layer_type"
            )
        
        self.raster_config = raster_config or {}
        self.metadata = metadata or RasterMetadata()
        self.rendering_mode = rendering_mode
        
        # Initialize tile config if needed
        if self.rendering_mode == RasterRenderingMode.TILE_BASED:
            self.tile_config = TileConfig(**self.raster_config)
        else:
            self.tile_config = None
        
        # Raster-specific state
        self._tiles_loaded = False
        self._cache_size = self.raster_config.get('cache_size', 100)
        self._tile_cache: Dict[str, Any] = {}
        
        super().__init__(config, **kwargs)
        
        logger.info(f"RasterLayer initialized: {self.name} ({self.rendering_mode.value})")
    
    def _initialize_layer(self) -> None:
        """Initialize raster layer-specific components."""
        super()._initialize_layer()
        
        try:
            self._setup_raster_config()
            self._validate_raster_config()
            self._change_state(LayerState.READY)
        except Exception as e:
            logger.error(f"Failed to initialize raster layer {self.name}: {e}")
            self._error_message = str(e)
            self._change_state(LayerState.ERROR)
            raise RasterLayerError(f"Failed to initialize raster layer: {e}") from e
    
    def _setup_raster_config(self) -> None:
        """Setup raster-specific configuration."""
        # Extract data type from raster_config or infer from name
        data_source = self.config.data_source
        
        if 'type' in data_source:
            data_type_str = data_source['type'].lower()
            if 'xyz' in data_type_str:
                self.data_type = RasterDataType.XYZ_TILES
                self.rendering_mode = RasterRenderingMode.TILE_BASED
            elif 'wms' in data_type_str:
                self.data_type = RasterDataType.WMS
                self.rendering_mode = RasterRenderingMode.TILE_BASED
            elif 'geotiff' in data_type_str:
                self.data_type = RasterDataType.GEOTIFF
                self.rendering_mode = RasterRenderingMode.IMAGE_BASED
            elif 'png' in data_type_str:
                self.data_type = RasterDataType.PNG
                self.rendering_mode = RasterRenderingMode.IMAGE_BASED
            elif 'jpeg' in data_type_str:
                self.data_type = RasterDataType.JPEG
                self.rendering_mode = RasterRenderingMode.IMAGE_BASED
            else:
                self.data_type = RasterDataType.UNKNOWN
        else:
            # Default to XYZ tiles for backward compatibility
            self.data_type = RasterDataType.XYZ_TILES
            self.rendering_mode = RasterRenderingMode.TILE_BASED
        
        logger.debug(f"Raster layer {self.name} configured as {self.data_type.value}")
    
    def _validate_raster_config(self) -> None:
        """Validate raster configuration.
        
        Raises:
            RasterLayerError: If configuration is invalid
        """
        if self.rendering_mode == RasterRenderingMode.TILE_BASED:
            if not self.tile_config or not self.tile_config.url_template:
                raise RasterLayerError(
                    "Tile-based raster layers require a URL template"
                )
            
            if self.tile_config.min_zoom > self.tile_config.max_zoom:
                raise RasterLayerError(
                    f"Min zoom ({self.tile_config.min_zoom}) cannot be greater than "
                    f"max zoom ({self.tile_config.max_zoom})"
                )
        
        # Validate tile size if specified
        if self.tile_config and self.tile_config.tile_size not in [256, 512]:
            logger.warning(
                f"Non-standard tile size: {self.tile_config.tile_size}. "
                "Standard sizes are 256 and 512."
            )
    
    @property
    def data_type(self) -> RasterDataType:
        """Get raster data type."""
        return self._data_type
    
    @data_type.setter
    def data_type(self, value: RasterDataType) -> None:
        """Set raster data type."""
        self._data_type = value
    
    @property
    def rendering_mode(self) -> RasterRenderingMode:
        """Get rendering mode."""
        return self._rendering_mode
    
    @rendering_mode.setter
    def rendering_mode(self, value: RasterRenderingMode) -> None:
        """Set rendering mode."""
        self._rendering_mode = value
    
    @property
    def tiles_loaded(self) -> bool:
        """Check if tiles have been loaded."""
        return self._tiles_loaded
    
    @property
    def zoom_level_range(self) -> Tuple[int, int]:
        """Get zoom level range for tile-based layers.
        
        Returns:
            Tuple of (min_zoom, max_zoom)
            
        Raises:
            RasterLayerError: If not a tile-based layer
        """
        if self.rendering_mode != RasterRenderingMode.TILE_BASED:
            raise RasterLayerError("Zoom level range only available for tile-based layers")
        
        if not self.tile_config:
            raise RasterLayerError("Tile config not initialized")
        
        return (self.tile_config.min_zoom, self.tile_config.max_zoom)
    
    @property
    def url_template(self) -> str:
        """Get URL template for tile-based layers.
        
        Returns:
            URL template string
            
        Raises:
            RasterLayerError: If not a tile-based layer
        """
        if self.rendering_mode != RasterRenderingMode.TILE_BASED:
            raise RasterLayerError("URL template only available for tile-based layers")
        
        if not self.tile_config:
            raise RasterLayerError("Tile config not initialized")
        
        return self.tile_config.url_template
    
    def load(self) -> None:
        """Load raster layer data.
        
        For Phase 2, this is a placeholder that simulates loading.
        Phase 3 will implement actual tile loading and caching.
        
        Raises:
            DataLoadError: If data loading fails
        """
        if self._state == LayerState.DISPOSED:
            raise RasterLayerError("Cannot load disposed layer")
        
        self._change_state(LayerState.LOADING)
        start_time = time.time()
        
        try:
            logger.info(f"Loading raster layer: {self.name}")
            
            # Phase 2: Simulate loading process
            self._simulate_loading_process()
            
            # Set default extent if not already set
            if self.extent is None:
                self._set_default_extent()
            
            self._tiles_loaded = True
            self._load_time = time.time() - start_time
            
            self._change_state(LayerState.READY)
            logger.info(f"Raster layer loaded successfully: {self.name} ({self._load_time:.2f}s)")
            
        except Exception as e:
            logger.error(f"Failed to load raster layer {self.name}: {e}")
            self._error_message = str(e)
            self._change_state(LayerState.ERROR)
            raise DataLoadError(f"Failed to load raster layer: {e}", cause=e) from e
    
    def _simulate_loading_process(self) -> None:
        """Simulate the loading process for demonstration.
        
        In Phase 3, this will be replaced with actual tile loading.
        """
        # Simulate some processing time
        time.sleep(0.1)
        
        # For tile-based layers, validate URL template
        if self.rendering_mode == RasterRenderingMode.TILE_BASED:
            if self.tile_config and self.tile_config.url_template:
                # Basic URL template validation
                required_tokens = ['{z}', '{x}', '{y}']
                template = self.tile_config.url_template
                for token in required_tokens:
                    if token not in template:
                        raise RasterLayerError(
                            f"URL template missing required token: {token}. "
                            f"Template: {template}"
                        )
        
        logger.debug(f"Loading simulation complete for {self.name}")
    
    def _set_default_extent(self) -> None:
        """Set default spatial extent for the raster layer."""
        # For global datasets (like world maps), set a reasonable default extent
        if self.rendering_mode == RasterRenderingMode.TILE_BASED:
            # Default to world extent in WGS84
            self.extent = BoundingBox(
                min_x=-180.0,
                min_y=-85.0, 
                max_x=180.0,
                max_y=85.0,
                crs=4326  # WGS84
            )
        else:
            # For image-based rasters, we'll need to determine extent from metadata
            # For now, set a placeholder
            self.extent = BoundingBox(
                min_x=0.0,
                min_y=0.0,
                max_x=1.0,
                max_y=1.0,
                crs=4326
            )
    
    def unload(self) -> None:
        """Unload raster layer data to free memory."""
        logger.info(f"Unloading raster layer: {self.name}")
        
        # Clear tile cache
        self._tile_cache.clear()
        self._tiles_loaded = False
        
        # Reset metadata if needed
        # (In Phase 3, we might want to keep some metadata cached)
        
        self._change_state(LayerState.READY)
        logger.debug(f"Raster layer unloaded: {self.name}")
    
    def get_features_in_bbox(self, bbox: BoundingBox) -> List[Feature]:
        """Get features within bounding box.
        
        For raster layers, this returns information about raster tiles
        that would be visible in the given bounding box.
        
        Args:
            bbox: Bounding box to query
            
        Returns:
            List of features (tiles) within the bounding box
            
        Raises:
            RasterLayerError: If layer is not loaded
        """
        if not self.loaded:
            raise RasterLayerError("Cannot query features on unloaded layer")
        
        # For Phase 2, return an empty list as we don't have actual features yet
        # Phase 3 will implement actual tile identification and feature creation
        logger.debug(f"Querying raster features in bbox: {bbox}")
        
        return []
    
    def get_feature_count(self) -> int:
        """Get total number of features in the layer.
        
        For raster layers, this returns the number of tiles or pixels
        that would be visible at the current zoom level.
        
        Returns:
            Number of features (tiles/pixels)
            
        Raises:
            RasterLayerError: If layer is not loaded
        """
        if not self.loaded:
            raise RasterLayerError("Cannot get feature count for unloaded layer")
        
        # For Phase 2, return 0 as we don't have actual features yet
        # Phase 3 will implement actual feature counting
        return 0
    
    def get_tile_url(self, x: int, y: int, z: int) -> str:
        """Get URL for a specific tile.
        
        Args:
            x: Tile x coordinate
            y: Tile y coordinate
            z: Zoom level
            
        Returns:
            URL for the requested tile
            
        Raises:
            RasterLayerError: If not a tile-based layer or configuration invalid
        """
        if self.rendering_mode != RasterRenderingMode.TILE_BASED:
            raise RasterLayerError("Tile URLs only available for tile-based layers")
        
        if not self.tile_config:
            raise RasterLayerError("Tile config not initialized")
        
        if z < self.tile_config.min_zoom or z > self.tile_config.max_zoom:
            raise RasterLayerError(f"Zoom level {z} outside valid range")
        
        # Substitute placeholders in URL template
        url = self.tile_config.url_template
        url = url.replace('{x}', str(x))
        url = url.replace('{y}', str(y))
        url = url.replace('{z}', str(z))
        
        # Handle subdomains if specified
        if self.tile_config.subdomains:
            import hashlib
            # Simple hash to select subdomain
            tile_string = f"{z}/{x}/{y}"
            hash_value = int(hashlib.md5(tile_string.encode()).hexdigest(), 16)
            subdomain_index = hash_value % len(self.tile_config.subdomains)
            subdomain = self.tile_config.subdomains[subdomain_index]
            url = url.replace('{s}', subdomain)
        else:
            # Remove subdomain placeholder if no subdomains configured
            url = url.replace('{s}', '')
        
        return url
    
    def dispose(self) -> None:
        """Dispose of raster layer resources."""
        logger.info(f"Disposing raster layer: {self.name}")
        
        # Clear caches
        self._tile_cache.clear()
        
        # Call parent dispose
        super().dispose()
        
        logger.info(f"Raster layer disposed: {self.name}")
    
    def __str__(self) -> str:
        """String representation of raster layer."""
        return f"RasterLayer({self.name}, {self.data_type.value}, {self.rendering_mode.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"RasterLayer(name='{self.name}', "
                f"data_type={self.data_type.value}, "
                f"rendering_mode={self.rendering_mode.value}, "
                f"loaded={self.loaded})")


# Factory function for creating raster layers
def create_raster_layer(name: str, 
                       data_source: Union[str, Dict[str, Any]],
                       **kwargs) -> RasterLayer:
    """Create a raster layer from configuration.
    
    Args:
        name: Layer name
        data_source: Data source (URL template or file path)
        **kwargs: Additional layer configuration
        
    Returns:
        RasterLayer instance
    """
    # Create layer configuration
    config = create_layer_config(name=name, layer_type=LayerType.RASTER, **kwargs)
    
    # Determine data source type
    if isinstance(data_source, str):
        # Assume it's a URL template for tiles
        raster_config = {
            'type': 'xyz_tiles',
            'url_template': data_source
        }
    else:
        # Assume it's a configuration dictionary
        raster_config = data_source.copy()
    
    return RasterLayer(config=config, raster_config=raster_config)