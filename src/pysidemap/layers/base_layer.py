"""
PySideMap Base Layer

Abstract base class providing the common interface and lifecycle management
for all spatial data layers in the GIS visualization widget.

This module provides:
- BaseLayer abstract class with common layer interface
- Layer lifecycle management per data-model.md
- Foundation for raster and vector layers
- Integration with data providers and coordinate systems
- Spatial extent and performance management
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import time

from ..utils.types import LayerConfig, BoundingBox, Feature, Geometry, Coordinate, CRSLike
from ..coordinate_systems import CRSManager, WGS84
from ..exceptions import (
    PySideMapError,
    DataLoadError,
    CRSError,
    ValidationError,
    MemoryError
)


logger = logging.getLogger(__name__)


class LayerState(Enum):
    """Layer lifecycle states."""
    UNINITIALIZED = "uninitialized"
    LOADING = "loading"
    READY = "ready"
    VISIBLE = "visible"
    HIDDEN = "hidden"
    ERROR = "error"
    DISPOSED = "disposed"


class LayerEventType(Enum):
    """Types of layer events."""
    LOAD_STARTED = "load_started"
    LOAD_COMPLETED = "load_completed"
    LOAD_FAILED = "load_failed"
    STATE_CHANGED = "state_changed"
    VISIBILITY_CHANGED = "visibility_changed"
    STYLE_UPDATED = "style_updated"
    EXTENT_UPDATED = "extent_updated"


@dataclass
class LayerEvent:
    """Event information for layer state changes.
    
    Attributes:
        event_type: Type of event
        timestamp: When the event occurred
        layer_id: ID of the layer that triggered the event
        message: Event message
        data: Additional event data
    """
    event_type: LayerEventType
    timestamp: float
    layer_id: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)


class BaseLayerError(PySideMapError):
    """Base exception for layer-related errors."""
    pass


class BaseLayer(ABC):
    """Abstract base class for all spatial data layers.
    
    This class defines the common interface that all layer implementations
    must provide for integration with the GIS graphics view. It manages
    the layer lifecycle and provides common functionality for spatial data layers.
    
    Attributes:
        config: Layer configuration
        _state: Current layer state
        _event_handlers: Event handlers for layer events
        _extent: Spatial extent of the layer
        _crs_manager: Coordinate reference system manager
        _loaded_features: Features that have been loaded
        _last_access: Timestamp of last layer access
    """
    
    def __init__(self, config: LayerConfig, crs_manager: Optional[CRSManager] = None):
        """Initialize base layer.
        
        Args:
            config: Layer configuration
            crs_manager: Coordinate reference system manager
            
        Raises:
            BaseLayerError: If configuration is invalid
        """
        self.config = config
        self.crs_manager = crs_manager or CRSManager()
        self._state = LayerState.UNINITIALIZED
        self._event_handlers: Dict[LayerEventType, List[callable]] = {}
        self._extent: Optional[BoundingBox] = config.extent
        self._loaded_features: List[Feature] = []
        self._last_access = time.time()
        self._load_time: Optional[float] = None
        self._error_message: Optional[str] = None
        
        # Initialize layer
        self._initialize_layer()
        
        logger.info(f"BaseLayer initialized: {self.name} ({self.layer_id})")
    
    def _initialize_layer(self) -> None:
        """Initialize layer-specific components."""
        try:
            self._validate_config()
            self._setup_crs()
            self._notify_event(LayerEventType.STATE_CHANGED, "Layer initialized")
            self._change_state(LayerState.READY)
        except Exception as e:
            logger.error(f"Failed to initialize layer {self.name}: {e}")
            self._error_message = str(e)
            self._change_state(LayerState.ERROR)
            raise BaseLayerError(f"Failed to initialize layer: {e}") from e
    
    def _validate_config(self) -> None:
        """Validate layer configuration.
        
        Raises:
            ValidationError: If configuration is invalid
        """
        if not self.config.name:
            raise ValidationError("Layer name is required", field_name="name")
        
        if not 0.0 <= self.config.opacity <= 1.0:
            raise ValidationError(
                f"Opacity must be between 0.0 and 1.0, got {self.config.opacity}",
                invalid_value=self.config.opacity,
                expected_type="float between 0.0 and 1.0",
                field_name="opacity"
            )
        
        if self.config.z_order < 0:
            raise ValidationError(
                f"Z-order must be non-negative, got {self.config.z_order}",
                invalid_value=self.config.z_order,
                expected_type="non-negative integer",
                field_name="z_order"
            )
    
    def _setup_crs(self) -> None:
        """Setup coordinate reference system for the layer.
        
        Raises:
            CRSError: If CRS setup fails
        """
        # For now, we'll use the default CRS from the CRS manager
        # In future phases, this will be derived from the data source
        if not self.crs_manager.is_supported(WGS84):
            raise CRSError(f"Default CRS {WGS84} is not supported")
        
        logger.debug(f"CRS setup complete for layer {self.name}")
    
    @property
    def layer_id(self) -> str:
        """Get layer identifier."""
        return self.config.layer_id
    
    @property
    def name(self) -> str:
        """Get layer name."""
        return self.config.name
    
    @property
    def state(self) -> LayerState:
        """Get current layer state."""
        return self._state
    
    @property
    def visible(self) -> bool:
        """Get layer visibility."""
        return self.config.visible and self._state in [LayerState.READY, LayerState.VISIBLE]
    
    @visible.setter
    def visible(self, value: bool) -> None:
        """Set layer visibility."""
        if self.config.visible != value:
            old_visible = self.config.visible
            self.config.visible = value
            
            if value and self._state == LayerState.READY:
                self._change_state(LayerState.VISIBLE)
            elif not value and self._state == LayerState.VISIBLE:
                self._change_state(LayerState.HIDDEN)
            
            self._notify_event(
                LayerEventType.VISIBILITY_CHANGED,
                f"Visibility changed from {old_visible} to {value}",
                data={"old_visible": old_visible, "new_visible": value}
            )
    
    @property
    def opacity(self) -> float:
        """Get layer opacity."""
        return self.config.opacity
    
    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set layer opacity."""
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Opacity must be between 0.0 and 1.0, got {value}")
        
        old_opacity = self.config.opacity
        self.config.opacity = value
        
        self._notify_event(
            LayerEventType.STYLE_UPDATED,
            f"Opacity changed from {old_opacity} to {value}",
            data={"old_opacity": old_opacity, "new_opacity": value}
        )
    
    @property
    def z_order(self) -> int:
        """Get layer z-order (stacking order)."""
        return self.config.z_order
    
    @z_order.setter
    def z_order(self, value: int) -> None:
        """Set layer z-order."""
        if value < 0:
            raise ValueError(f"Z-order must be non-negative, got {value}")
        
        old_z_order = self.config.z_order
        self.config.z_order = value
        
        self._notify_event(
            LayerEventType.STYLE_UPDATED,
            f"Z-order changed from {old_z_order} to {value}",
            data={"old_z_order": old_z_order, "new_z_order": value}
        )
    
    @property
    def extent(self) -> Optional[BoundingBox]:
        """Get layer spatial extent."""
        return self._extent
    
    @extent.setter
    def extent(self, value: Optional[BoundingBox]) -> None:
        """Set layer spatial extent."""
        old_extent = self._extent
        self._extent = value
        
        if value != old_extent:
            self._notify_event(
                LayerEventType.EXTENT_UPDATED,
                f"Extent updated from {old_extent} to {value}",
                data={"old_extent": old_extent, "new_extent": value}
            )
    
    @property
    def loaded(self) -> bool:
        """Check if layer data is loaded."""
        return self._state in [LayerState.READY, LayerState.VISIBLE, LayerState.HIDDEN]
    
    @property
    def error_message(self) -> Optional[str]:
        """Get error message if layer is in error state."""
        return self._error_message
    
    @property
    def last_access_time(self) -> float:
        """Get timestamp of last layer access."""
        return self._last_access
    
    def _change_state(self, new_state: LayerState) -> None:
        """Change layer state and notify handlers.
        
        Args:
            new_state: New layer state
        """
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            
            self._notify_event(
                LayerEventType.STATE_CHANGED,
                f"State changed from {old_state.value} to {new_state.value}",
                data={"old_state": old_state.value, "new_state": new_state.value}
            )
            
            logger.debug(f"Layer {self.name} state changed: {old_state.value} -> {new_state.value}")
    
    def _notify_event(self, event_type: LayerEventType, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Notify all registered event handlers.
        
        Args:
            event_type: Type of event
            message: Event message
            data: Additional event data
        """
        event = LayerEvent(
            event_type=event_type,
            timestamp=time.time(),
            layer_id=self.layer_id,
            message=message,
            data=data or {}
        )
        
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    def add_event_handler(self, event_type: LayerEventType, handler: callable) -> None:
        """Add event handler for layer events.
        
        Args:
            event_type: Type of event to handle
            handler: Event handler function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: LayerEventType, handler: callable) -> None:
        """Remove event handler.
        
        Args:
            event_type: Type of event
            handler: Event handler to remove
        """
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass  # Handler not found
    
    def update_style(self, **kwargs) -> None:
        """Update layer styling.
        
        Args:
            **kwargs: Style properties to update
        """
        old_style = self.config.style.copy()
        self.config.update_style(**kwargs)
        
        self._notify_event(
            LayerEventType.STYLE_UPDATED,
            f"Style updated with {kwargs}",
            data={"old_style": old_style, "new_style": self.config.style}
        )
    
    def get_style(self, property_name: str, default: Any = None) -> Any:
        """Get style property value.
        
        Args:
            property_name: Name of style property
            default: Default value if property not found
            
        Returns:
            Style property value or default
        """
        return self.config.get_style(property_name, default)
    
    def _update_last_access(self) -> None:
        """Update last access timestamp."""
        self._last_access = time.time()
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    def load(self) -> None:
        """Load layer data.
        
        This method should:
        1. Change state to LOADING
        2. Load spatial data from the data source
        3. Calculate spatial extent if not already set
        4. Change state to READY on success or ERROR on failure
        
        Raises:
            DataLoadError: If data loading fails
            BaseLayerError: For other layer-specific errors
        """
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """Unload layer data to free memory.
        
        This method should:
        1. Clear loaded features
        2. Release any cached data
        3. Change state to READY (data unloaded but layer ready for reload)
        """
        pass
    
    @abstractmethod
    def get_features_in_bbox(self, bbox: BoundingBox) -> List[Feature]:
        """Get features within bounding box.
        
        Args:
            bbox: Bounding box to query
            
        Returns:
            List of features within the bounding box
            
        Raises:
            BaseLayerError: If layer is not loaded
            CRSError: If CRS mismatch
        """
        pass
    
    @abstractmethod
    def get_feature_count(self) -> int:
        """Get total number of features in the layer.
        
        Returns:
            Number of features
            
        Raises:
            BaseLayerError: If layer is not loaded
        """
        pass
    
    def dispose(self) -> None:
        """Dispose of layer resources.
        
        This method should:
        1. Unload any loaded data
        2. Clear event handlers
        3. Change state to DISPOSED
        """
        logger.info(f"Disposing layer: {self.name} ({self.layer_id})")
        
        try:
            self.unload()
        except Exception as e:
            logger.warning(f"Error during layer unload: {e}")
        
        # Clear event handlers
        self._event_handlers.clear()
        
        # Change to disposed state
        self._change_state(LayerState.DISPOSED)
        
        logger.info(f"Layer disposed: {self.name}")
    
    def __str__(self) -> str:
        """String representation of layer."""
        return f"BaseLayer({self.name}, state={self._state.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"BaseLayer(name='{self.name}', "
                f"id='{self.layer_id}', "
                f"state={self._state.value}, "
                f"visible={self.visible})")


# Utility functions for common layer operations

def create_layer_from_config(config: LayerConfig, **kwargs) -> BaseLayer:
    """Factory function to create layer from configuration.
    
    Args:
        config: Layer configuration
        **kwargs: Additional layer-specific arguments
        
    Returns:
        BaseLayer instance
        
    Raises:
        BaseLayerError: If layer creation fails
    """
    # This is a placeholder for future layer factory implementation
    # In Phase 3, this will create specific layer types based on config
    raise NotImplementedError("Layer factory will be implemented in Phase 3")


def validate_layer_compatibility(layer1: BaseLayer, layer2: BaseLayer) -> bool:
    """Check if two layers are compatible for overlaying.
    
    Args:
        layer1: First layer
        layer2: Second layer
        
    Returns:
        True if layers are compatible
    """
    # For now, layers are compatible if they're both loaded
    # In future phases, this will check CRS compatibility, etc.
    return layer1.loaded and layer2.loaded