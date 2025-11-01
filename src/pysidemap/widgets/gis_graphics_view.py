"""
PySideMap GIS Graphics View

Core GIS widget implementation providing the foundation for map visualization
and interaction within PySide6 applications.

This module provides:
- GISGraphicsView class inheriting from QGraphicsView
- Basic scene setup and widget initialization
- Foundation for PySide6 integration per quickstart.md
- Layer management framework
- Coordinate system integration
"""

from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid

try:
    from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget
    from PySide6.QtCore import Qt, Signal, QPoint, QRectF, QObject
    from PySide6.QtGui import QWheelEvent, QMouseEvent, QKeyEvent, QTransform
    PYSIDE6_AVAILABLE = True
except ImportError:
    # Fallback for development/testing without PySide6
    PYSIDE6_AVAILABLE = False
    # Create dummy classes for type hints
    class QGraphicsView: pass
    class QGraphicsScene: pass
    class QWidget: pass
    class Qt: pass
    class Signal: 
        def __init__(self, *args): pass
    class QPoint: pass
    class QRectF: pass
    class QObject: pass
    class QWheelEvent: pass
    class QMouseEvent: pass
    class QKeyEvent: pass
    class QTransform: pass


from ..coordinate_systems import CRSManager, WGS84, WEB_MERCATOR
from ..layers import BaseLayer, LayerState, LayerEvent, LayerEventType
from ..utils.types import Coordinate, BoundingBox, LayerConfig
from ..exceptions import InitializationError, PySideMapError


logger = logging.getLogger(__name__)


class ViewState(Enum):
    """GIS view states."""
    INITIALIZING = "initializing"
    READY = "ready"
    LOADING = "loading"
    ERROR = "error"


class InteractionMode(Enum):
    """Interaction modes for the GIS view."""
    PAN = "pan"
    ZOOM = "zoom"
    SELECT = "select"
    MEASURE = "measure"
    INFO = "info"


@dataclass
class ViewportInfo:
    """Information about the current viewport.
    
    Attributes:
        center: Center coordinate
        zoom_level: Current zoom level
        scale: Current scale factor
        width: Viewport width in pixels
        height: Viewport height in pixels
        bounding_box: Current visible bounding box
    """
    center: Coordinate
    zoom_level: float
    scale: float
    width: int
    height: int
    bounding_box: Optional[BoundingBox] = None


class GISViewError(PySideMapError):
    """Exception for GIS view-related errors."""
    pass


class GISGraphicsView(QGraphicsView):
    """Core GIS graphics view widget.
    
    This widget provides the foundation for map visualization and interaction.
    It inherits from QGraphicsView to leverage PySide6's graphics system
    for efficient rendering and interaction.
    
    For Phase 2, this provides basic widget framework and scene setup.
    Phase 3 will add actual map display and interaction capabilities.
    
    Signals:
        layer_added: Emitted when a layer is added
        layer_removed: Emitted when a layer is removed
        view_changed: Emitted when the view changes (zoom, pan, etc.)
        selection_changed: Emitted when selection changes
        error_occurred: Emitted when an error occurs
    
    Attributes:
        _layers: List of layers managed by the view
        _crs_manager: Coordinate reference system manager
        _view_state: Current state of the view
        _interaction_mode: Current interaction mode
        _viewport_info: Information about current viewport
    """
    
    # Signals (only available when PySide6 is available)
    if PYSIDE6_AVAILABLE:
        layer_added = Signal(str)  # layer_id
        layer_removed = Signal(str)  # layer_id
        view_changed = Signal(object)  # ViewportInfo
        selection_changed = Signal(list)  # List of selected feature IDs
        error_occurred = Signal(str, str)  # error_type, message
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 initial_crs: int = WGS84,
                 enable_opengl: bool = False,
                 **kwargs):
        """Initialize GIS graphics view.
        
        Args:
            parent: Parent widget
            initial_crs: Initial coordinate reference system (EPSG code)
            enable_opengl: Enable OpenGL rendering for better performance
            **kwargs: Additional arguments
            
        Raises:
            InitializationError: If initialization fails
        """
        if not PYSIDE6_AVAILABLE:
            raise InitializationError(
                "PySide6 is required for GISGraphicsView. "
                "Install with: pip install PySide6"
            )
        
        super().__init__(parent)
        
        # Core components
        self.crs_manager = CRSManager(default_crs=initial_crs)
        self._layers: List[BaseLayer] = []
        self._layer_index: Dict[str, BaseLayer] = {}
        
        # View state
        self._view_state = ViewState.INITIALIZING
        self._interaction_mode = InteractionMode.PAN
        self._viewport_info = self._create_initial_viewport()
        
        # Configuration
        self._enable_opengl = enable_opengl
        self._background_color = (240, 240, 240)  # Light gray
        
        # Initialize the widget
        self._initialize_widget()
        
        logger.info(f"GISGraphicsView initialized with CRS: EPSG:{initial_crs}")
    
    def _initialize_widget(self) -> None:
        """Initialize the widget components."""
        try:
            # Setup graphics scene
            self._setup_scene()
            
            # Configure view behavior
            self._configure_view_behavior()
            
            # Setup coordinate system
            self._setup_coordinate_system()
            
            # Setup event handling
            self._setup_event_handlers()
            
            self._view_state = ViewState.READY
            logger.info("GISGraphicsView initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize GISGraphicsView: {e}")
            self._view_state = ViewState.ERROR
            if hasattr(self, 'error_occurred'):
                self.error_occurred.emit("initialization_error", str(e))
            raise InitializationError(f"Failed to initialize GIS view: {e}") from e
    
    def _setup_scene(self) -> None:
        """Setup the graphics scene."""
        # Create scene if not already created
        if self.scene() is None:
            scene = QGraphicsScene(self)
            self.setScene(scene)
        
        # Configure scene
        scene = self.scene()
        scene.setBackgroundBrush(Qt.GlobalColor.white)
        
        # Set scene rect for infinite scrolling
        # Use a large but finite rectangle to avoid performance issues
        scene.setSceneRect(-1000000, -1000000, 2000000, 2000000)
        
        logger.debug("Graphics scene configured")
    
    def _configure_view_behavior(self) -> None:
        """Configure view interaction behavior."""
        # Enable anti-aliasing for better rendering
        self.setRenderHint(Qt.RenderHint.Antialiasing, True)
        
        # Enable OpenGL if requested and available
        if self._enable_opengl:
            try:
                # OpenGL will be enabled in Phase 3 when we have actual rendering
                logger.debug("OpenGL rendering requested but not yet implemented")
            except Exception as e:
                logger.warning(f"Failed to enable OpenGL: {e}")
        
        # Configure scroll bars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Configure drag mode for pan/zoom
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        logger.debug("View behavior configured")
    
    def _setup_coordinate_system(self) -> None:
        """Setup coordinate system for the view."""
        # Set up transformation between geographic and screen coordinates
        # For Phase 2, we'll use a simple identity transformation
        # Phase 3 will implement proper coordinate transformations
        
        # Set initial viewport
        initial_center = Coordinate(0, 0, crs=self.crs_manager.get_default_crs())
        self._viewport_info.center = initial_center
        
        logger.debug("Coordinate system configured")
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for the view."""
        # Mouse wheel zoom will be implemented in Phase 3
        # For now, we'll just log the events
        logger.debug("Event handlers configured")
    
    def _create_initial_viewport(self) -> ViewportInfo:
        """Create initial viewport information."""
        return ViewportInfo(
            center=Coordinate(0, 0, crs=self.crs_manager.get_default_crs()),
            zoom_level=1.0,
            scale=1.0,
            width=self.width(),
            height=self.height()
        )
    
    # Layer management methods
    
    def add_layer(self, layer: BaseLayer) -> str:
        """Add a layer to the view.
        
        Args:
            layer: Layer to add
            
        Returns:
            Layer ID
            
        Raises:
            GISViewError: If layer cannot be added
        """
        if layer.layer_id in self._layer_index:
            raise GISViewError(f"Layer with ID {layer.layer_id} already exists")
        
        if self._view_state != ViewState.READY:
            raise GISViewError(f"Cannot add layer in state {self._view_state.value}")
        
        try:
            # Add layer to management
            self._layers.append(layer)
            self._layer_index[layer.layer_id] = layer
            
            # Add layer to scene (Phase 3 will implement actual rendering)
            self._add_layer_to_scene(layer)
            
            # Setup layer event handling
            layer.add_event_handler(LayerEventType.STATE_CHANGED, self._on_layer_state_changed)
            
            # Emit signal
            if hasattr(self, 'layer_added'):
                self.layer_added.emit(layer.layer_id)
            
            logger.info(f"Layer added: {layer.name} ({layer.layer_id})")
            return layer.layer_id
            
        except Exception as e:
            logger.error(f"Failed to add layer {layer.name}: {e}")
            raise GISViewError(f"Failed to add layer: {e}") from e
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer from the view.
        
        Args:
            layer_id: ID of layer to remove
            
        Returns:
            True if layer was removed
            
        Raises:
            GISViewError: If layer cannot be removed
        """
        if layer_id not in self._layer_index:
            logger.warning(f"Layer {layer_id} not found for removal")
            return False
        
        if self._view_state != ViewState.READY:
            raise GISViewError(f"Cannot remove layer in state {self._view_state.value}")
        
        try:
            layer = self._layer_index[layer_id]
            
            # Remove from scene
            self._remove_layer_from_scene(layer)
            
            # Remove from management
            del self._layer_index[layer_id]
            self._layers.remove(layer)
            
            # Emit signal
            if hasattr(self, 'layer_removed'):
                self.layer_removed.emit(layer_id)
            
            logger.info(f"Layer removed: {layer.name} ({layer_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove layer {layer_id}: {e}")
            raise GISViewError(f"Failed to remove layer: {e}") from e
    
    def get_layer(self, layer_id: str) -> Optional[BaseLayer]:
        """Get layer by ID.
        
        Args:
            layer_id: Layer ID
            
        Returns:
            Layer if found, None otherwise
        """
        return self._layer_index.get(layer_id)
    
    def get_all_layers(self) -> List[BaseLayer]:
        """Get all layers.
        
        Returns:
            List of all layers
        """
        return self._layers.copy()
    
    def get_visible_layers(self) -> List[BaseLayer]:
        """Get visible layers.
        
        Returns:
            List of visible layers
        """
        return [layer for layer in self._layers if layer.visible]
    
    def _add_layer_to_scene(self, layer: BaseLayer) -> None:
        """Add layer to the graphics scene.
        
        Args:
            layer: Layer to add
        """
        # Phase 3 will implement actual layer rendering in the scene
        # For now, we just log the addition
        logger.debug(f"Adding layer {layer.name} to scene")
    
    def _remove_layer_from_scene(self, layer: BaseLayer) -> None:
        """Remove layer from the graphics scene.
        
        Args:
            layer: Layer to remove
        """
        # Phase 3 will implement actual layer removal from scene
        # For now, we just log the removal
        logger.debug(f"Removing layer {layer.name} from scene")
    
    def _on_layer_state_changed(self, event: LayerEvent) -> None:
        """Handle layer state change events.
        
        Args:
            event: Layer event
        """
        logger.debug(f"Layer state changed: {event.layer_id} -> {event.message}")
        
        # Update view if needed
        # Phase 3 will implement actual view updates
    
    # Viewport and interaction methods
    
    def get_viewport_info(self) -> ViewportInfo:
        """Get current viewport information.
        
        Returns:
            Current viewport information
        """
        # Update viewport info
        self._viewport_info.width = self.width()
        self._viewport_info.height = self.height()
        
        return self._viewport_info
    
    def set_center(self, coordinate: Coordinate) -> None:
        """Set the view center.
        
        Args:
            coordinate: Center coordinate
        """
        old_center = self._viewport_info.center
        self._viewport_info.center = coordinate
        
        # Update view transform (Phase 3 will implement actual transformation)
        logger.debug(f"View center changed: {old_center} -> {coordinate}")
        
        # Emit signal
        if hasattr(self, 'view_changed'):
            self.view_changed.emit(self._viewport_info)
    
    def set_zoom_level(self, zoom_level: float) -> None:
        """Set the zoom level.
        
        Args:
            zoom_level: Zoom level (1.0 = 100%)
        """
        if zoom_level <= 0:
            raise ValueError(f"Zoom level must be positive, got {zoom_level}")
        
        old_zoom = self._viewport_info.zoom_level
        self._viewport_info.zoom_level = zoom_level
        
        # Update view transform (Phase 3 will implement actual zoom)
        logger.debug(f"Zoom level changed: {old_zoom} -> {zoom_level}")
        
        # Emit signal
        if hasattr(self, 'view_changed'):
            self.view_changed.emit(self._viewport_info)
    
    def zoom_to_extent(self, bbox: BoundingBox) -> None:
        """Zoom to show a specific bounding box.
        
        Args:
            bbox: Bounding box to zoom to
        """
        # Calculate center and zoom level to fit the bounding box
        center = bbox.center
        self.set_center(center)
        
        # Calculate appropriate zoom level (Phase 3 will implement actual calculation)
        logger.debug(f"Zooming to extent: {bbox}")
        
        # Emit signal
        if hasattr(self, 'view_changed'):
            self.view_changed.emit(self._viewport_info)
    
    def set_interaction_mode(self, mode: InteractionMode) -> None:
        """Set the interaction mode.
        
        Args:
            mode: Interaction mode
        """
        old_mode = self._interaction_mode
        self._interaction_mode = mode
        
        # Update drag mode based on interaction mode
        if mode == InteractionMode.PAN:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        elif mode == InteractionMode.ZOOM:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        logger.debug(f"Interaction mode changed: {old_mode.value} -> {mode.value}")
    
    # CRS management
    
    def get_crs_manager(self) -> CRSManager:
        """Get the coordinate reference system manager.
        
        Returns:
            CRS manager
        """
        return self.crs_manager
    
    def set_display_crs(self, crs_code: int) -> None:
        """Set the display coordinate reference system.
        
        Args:
            crs_code: EPSG code for display CRS
        """
        if not self.crs_manager.is_supported(crs_code):
            raise GISViewError(f"CRS EPSG:{crs_code} is not supported")
        
        old_crs = self.crs_manager.get_default_crs()
        self.crs_manager.set_default_crs(crs_code)
        
        # Update viewport center CRS if needed
        if self._viewport_info.center.crs != crs_code:
            try:
                self._viewport_info.center = self.crs_manager.transform_point(
                    self._viewport_info.center, crs_code
                )
            except Exception as e:
                logger.warning(f"Failed to transform viewport center: {e}")
        
        logger.info(f"Display CRS changed: EPSG:{old_crs} -> EPSG:{crs_code}")
    
    # State and lifecycle methods
    
    @property
    def view_state(self) -> ViewState:
        """Get current view state."""
        return self._view_state
    
    @property
    def interaction_mode(self) -> InteractionMode:
        """Get current interaction mode."""
        return self._interaction_mode
    
    @property
    def layer_count(self) -> int:
        """Get number of layers."""
        return len(self._layers)
    
    def clear_layers(self) -> None:
        """Clear all layers from the view."""
        layer_ids = list(self._layer_index.keys())
        for layer_id in layer_ids:
            self.remove_layer(layer_id)
    
    def dispose(self) -> None:
        """Dispose of the view and its resources."""
        logger.info("Disposing GISGraphicsView")
        
        try:
            # Clear all layers
            self.clear_layers()
            
            # Clear scene
            if self.scene():
                self.scene().clear()
            
            # Change state
            self._view_state = ViewState.ERROR  # Use ERROR to indicate disposed
            
            logger.info("GISGraphicsView disposed")
            
        except Exception as e:
            logger.error(f"Error during GISGraphicsView disposal: {e}")
    
    def __str__(self) -> str:
        """String representation of the view."""
        return f"GISGraphicsView(layers={len(self._layers)}, state={self._view_state.value})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"GISGraphicsView(layers={len(self._layers)}, "
                f"state={self._view_state.value}, "
                f"crs=EPSG:{self.crs_manager.get_default_crs()})")


# Factory function for creating GIS views
def create_gis_view(parent: Optional[QWidget] = None, 
                   initial_crs: int = WGS84,
                   **kwargs) -> GISGraphicsView:
    """Create a GIS graphics view widget.
    
    Args:
        parent: Parent widget
        initial_crs: Initial coordinate reference system (EPSG code)
        **kwargs: Additional configuration options
        
    Returns:
        GISGraphicsView instance
    """
    return GISGraphicsView(
        parent=parent,
        initial_crs=initial_crs,
        **kwargs
    )