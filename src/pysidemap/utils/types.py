"""
PySideMap Type Definitions

Core type definitions for spatial data structures and layer configuration.
These types provide type safety and consistent interfaces across the GIS widget.
"""

from typing import Union, Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid


class GeometryType(Enum):
    """Geometry types supported by the GIS widget."""
    POINT = "Point"
    LINESTRING = "LineString"
    POLYGON = "Polygon"
    MULTIPOINT = "MultiPoint"
    MULTILINESTRING = "MultiLineString"
    MULTIPOLYGON = "MultiPolygon"
    GEOMETRYCOLLECTION = "GeometryCollection"


class LayerType(Enum):
    """Layer types supported by the GIS widget."""
    RASTER = "raster"
    VECTOR = "vector"


class CRSError(Exception):
    """Exception raised for coordinate reference system errors."""
    pass


@dataclass(frozen=True)
class Coordinate:
    """Represents a spatial coordinate with optional CRS information.
    
    Attributes:
        x: X coordinate value
        y: Y coordinate value
        z: Optional Z coordinate value (elevation/depth)
        crs: Optional coordinate reference system (EPSG code)
    """
    x: float
    y: float
    z: Optional[float] = None
    crs: Optional[int] = None
    
    def __post_init__(self):
        """Validate coordinate values."""
        if not isinstance(self.x, (int, float)):
            raise TypeError(f"X coordinate must be numeric, got {type(self.x)}")
        if not isinstance(self.y, (int, float)):
            raise TypeError(f"Y coordinate must be numeric, got {type(self.y)}")
        if self.z is not None and not isinstance(self.z, (int, float)):
            raise TypeError(f"Z coordinate must be numeric, got {type(self.z)}")
        if self.crs is not None and not isinstance(self.crs, int):
            raise TypeError(f"CRS must be an integer EPSG code, got {type(self.crs)}")
    
    def to_tuple(self, include_z: bool = False, include_crs: bool = False) -> Union[Tuple[float, float], Tuple[float, float, float]]:
        """Convert coordinate to tuple format.
        
        Args:
            include_z: Whether to include Z coordinate
            include_crs: Whether to include CRS in tuple (not recommended for coordinates)
        
        Returns:
            Coordinate as tuple
        """
        if include_z and self.z is not None:
            return (self.x, self.y, self.z)
        return (self.x, self.y)
    
    def distance_to(self, other: 'Coordinate') -> float:
        """Calculate Euclidean distance to another coordinate.
        
        Args:
            other: Target coordinate
            
        Returns:
            Distance in coordinate units
            
        Raises:
            CRSError: If coordinates are in different CRS
        """
        if self.crs != other.crs:
            raise CRSError(f"Cannot calculate distance between different CRS: {self.crs} vs {other.crs}")
        
        dx = self.x - other.x
        dy = self.y - other.y
        
        if self.z is not None and other.z is not None:
            dz = self.z - other.z
            return (dx*dx + dy*dy + dz*dz) ** 0.5
        return (dx*dx + dy*dy) ** 0.5
    
    def __str__(self) -> str:
        """String representation of coordinate."""
        result = f"({self.x}, {self.y})"
        if self.z is not None:
            result = f"({self.x}, {self.y}, {self.z})"
        if self.crs is not None:
            result += f" @ CRS:{self.crs}"
        return result


@dataclass(frozen=True)
class BoundingBox:
    """Represents a rectangular spatial extent.
    
    Attributes:
        min_x: Minimum X coordinate
        min_y: Minimum Y coordinate
        max_x: Maximum X coordinate
        max_y: Maximum Y coordinate
        crs: Coordinate reference system for the bounding box
    """
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    crs: Optional[int] = None
    
    def __post_init__(self):
        """Validate bounding box coordinates."""
        if self.min_x > self.max_x:
            raise ValueError(f"min_x ({self.min_x}) cannot be greater than max_x ({self.max_x})")
        if self.min_y > self.max_y:
            raise ValueError(f"min_y ({self.min_y}) cannot be greater than max_y ({self.max_y})")
        if self.crs is not None and not isinstance(self.crs, int):
            raise TypeError(f"CRS must be an integer EPSG code, got {type(self.crs)}")
    
    @property
    def width(self) -> float:
        """Width of bounding box."""
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        """Height of bounding box."""
        return self.max_y - self.min_y
    
    @property
    def center(self) -> Coordinate:
        """Center point of bounding box."""
        center_x = (self.min_x + self.max_x) / 2
        center_y = (self.min_y + self.max_y) / 2
        return Coordinate(center_x, center_y, crs=self.crs)
    
    def contains(self, coordinate: Coordinate) -> bool:
        """Check if coordinate is within bounding box.
        
        Args:
            coordinate: Coordinate to test
            
        Returns:
            True if coordinate is within bounds
            
        Raises:
            CRSError: If coordinate CRS differs from bounding box CRS
        """
        if self.crs != coordinate.crs:
            raise CRSError(f"Cannot test containment between different CRS: {self.crs} vs {coordinate.crs}")
        
        return (self.min_x <= coordinate.x <= self.max_x and 
                self.min_y <= coordinate.y <= self.max_y)
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box intersects with another.
        
        Args:
            other: Other bounding box
            
        Returns:
            True if bounding boxes intersect
            
        Raises:
            CRSError: If bounding boxes are in different CRS
        """
        if self.crs != other.crs:
            raise CRSError(f"Cannot test intersection between different CRS: {self.crs} vs {other.crs}")
        
        return not (self.max_x < other.min_x or 
                   self.min_x > other.max_x or
                   self.max_y < other.min_y or 
                   self.min_y > other.max_y)
    
    def expanded_by(self, margin: float) -> 'BoundingBox':
        """Create a new bounding box expanded by margin on all sides.
        
        Args:
            margin: Margin to add to each side
            
        Returns:
            New expanded bounding box
        """
        return BoundingBox(
            self.min_x - margin,
            self.min_y - margin,
            self.max_x + margin,
            self.max_y + margin,
            self.crs
        )
    
    def __str__(self) -> str:
        """String representation of bounding box."""
        result = f"[{self.min_x}, {self.min_y}, {self.max_x}, {self.max_y}]"
        if self.crs is not None:
            result += f" @ CRS:{self.crs}"
        return result


@dataclass
class Geometry:
    """Represents a spatial geometry object.
    
    Attributes:
        geometry_type: Type of geometry
        coordinates: Geometry coordinates in appropriate format
        crs: Coordinate reference system
        properties: Optional properties/attributes
    """
    geometry_type: GeometryType
    coordinates: Union[
        Tuple[float, float],  # Point
        List[Tuple[float, float]],  # LineString
        List[List[Tuple[float, float]]],  # Polygon
        List[Tuple[float, float]],  # MultiPoint
        List[List[Tuple[float, float]]],  # MultiLineString
        List[List[List[Tuple[float, float]]]],  # MultiPolygon
        List[Any]  # GeometryCollection
    ]
    crs: Optional[int] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate geometry data."""
        if not isinstance(self.geometry_type, GeometryType):
            raise TypeError(f"geometry_type must be GeometryType, got {type(self.geometry_type)}")
        if self.crs is not None and not isinstance(self.crs, int):
            raise TypeError(f"CRS must be an integer EPSG code, got {type(self.crs)}")
        if not isinstance(self.properties, dict):
            raise TypeError(f"properties must be a dictionary, got {type(self.properties)}")
    
    @property
    def is_point(self) -> bool:
        """Check if geometry is a point."""
        return self.geometry_type == GeometryType.POINT
    
    @property
    def is_linestring(self) -> bool:
        """Check if geometry is a linestring."""
        return self.geometry_type == GeometryType.LINESTRING
    
    @property
    def is_polygon(self) -> bool:
        """Check if geometry is a polygon."""
        return self.geometry_type == GeometryType.POLYGON
    
    def get_bounding_box(self) -> BoundingBox:
        """Calculate bounding box for geometry.
        
        Returns:
            Bounding box containing the geometry
        """
        if self.geometry_type == GeometryType.POINT:
            x, y = self.coordinates
            return BoundingBox(x, y, x, y, self.crs)
        
        # For multi-part geometries, find min/max across all parts
        all_coords = []
        
        def extract_coords(coords, depth=0):
            """Recursively extract coordinate tuples."""
            if isinstance(coords[0], (int, float)):
                # This is a coordinate tuple
                all_coords.append(coords)
            else:
                # This is a nested structure, recurse
                for coord_tuple in coords:
                    extract_coords(coord_tuple, depth + 1)
        
        extract_coords(self.coordinates)
        
        if not all_coords:
            raise ValueError("No coordinates found in geometry")
        
        min_x = min(coord[0] for coord in all_coords)
        max_x = max(coord[0] for coord in all_coords)
        min_y = min(coord[1] for coord in all_coords)
        max_y = max(coord[1] for coord in all_coords)
        
        return BoundingBox(min_x, min_y, max_x, max_y, self.crs)
    
    def __str__(self) -> str:
        """String representation of geometry."""
        return f"{self.geometry_type.value}({len(self.coordinates)} coords) @ CRS:{self.crs}"


@dataclass
class LayerConfig:
    """Configuration for map layers.
    
    Attributes:
        layer_id: Unique identifier for the layer
        name: Human-readable layer name
        layer_type: Type of layer (raster/vector)
        visible: Whether layer is initially visible
        opacity: Layer opacity (0.0 to 1.0)
        z_order: Layer stacking order (higher values on top)
        style: Visual styling configuration
        data_source: Data source configuration
        extent: Spatial extent for quick culling
        min_zoom: Minimum zoom level for display
        max_zoom: Maximum zoom level for display
    """
    layer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    layer_type: LayerType = LayerType.RASTER
    visible: bool = True
    opacity: float = 1.0
    z_order: int = 0
    style: Dict[str, Any] = field(default_factory=dict)
    data_source: Dict[str, Any] = field(default_factory=dict)
    extent: Optional[BoundingBox] = None
    min_zoom: Optional[float] = None
    max_zoom: Optional[float] = None
    
    def __post_init__(self):
        """Validate layer configuration."""
        if not isinstance(self.layer_type, LayerType):
            raise TypeError(f"layer_type must be LayerType, got {type(self.layer_type)}")
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError(f"opacity must be between 0.0 and 1.0, got {self.opacity}")
        if not isinstance(self.visible, bool):
            raise TypeError(f"visible must be boolean, got {type(self.visible)}")
        if not isinstance(self.z_order, int):
            raise TypeError(f"z_order must be integer, got {type(self.z_order)}")
    
    @property
    def is_raster(self) -> bool:
        """Check if layer is a raster layer."""
        return self.layer_type == LayerType.RASTER
    
    @property
    def is_vector(self) -> bool:
        """Check if layer is a vector layer."""
        return self.layer_type == LayerType.VECTOR
    
    def update_style(self, **kwargs) -> None:
        """Update layer styling.
        
        Args:
            **kwargs: Style properties to update
        """
        self.style.update(kwargs)
    
    def get_style(self, property_name: str, default: Any = None) -> Any:
        """Get style property value.
        
        Args:
            property_name: Name of style property
            default: Default value if property not found
            
        Returns:
            Style property value or default
        """
        return self.style.get(property_name, default)
    
    def __str__(self) -> str:
        """String representation of layer configuration."""
        return f"LayerConfig({self.name}, {self.layer_type.value}, visible={self.visible})"


@dataclass
class Feature:
    """Represents a spatial feature with geometry and properties.
    
    Attributes:
        feature_id: Unique feature identifier
        geometry: Spatial geometry
        properties: Feature attributes/properties
        layer_id: ID of the layer this feature belongs to
    """
    feature_id: str
    geometry: Geometry
    properties: Dict[str, Any] = field(default_factory=dict)
    layer_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate feature data."""
        if not isinstance(self.geometry, Geometry):
            raise TypeError(f"geometry must be Geometry, got {type(self.geometry)}")
        if not isinstance(self.properties, dict):
            raise TypeError(f"properties must be dictionary, got {type(self.properties)}")
    
    @property
    def bounding_box(self) -> BoundingBox:
        """Get bounding box of feature geometry."""
        return self.geometry.get_bounding_box()
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get feature property value.
        
        Args:
            key: Property key
            default: Default value if property not found
            
        Returns:
            Property value or default
        """
        return self.properties.get(key, default)
    
    def __str__(self) -> str:
        """String representation of feature."""
        return f"Feature({self.feature_id}, {self.geometry.geometry_type.value})"


# Type aliases for common use cases
CoordinateLike = Union[Coordinate, Tuple[float, float], List[float]]
BoundingBoxLike = Union[BoundingBox, Tuple[float, float, float, float], List[float]]
GeometryLike = Union[Geometry, Dict[str, Any]]


def create_coordinate(x: float, y: float, z: Optional[float] = None, crs: Optional[int] = None) -> Coordinate:
    """Factory function to create Coordinate objects.
    
    Args:
        x: X coordinate
        y: Y coordinate
        z: Optional Z coordinate
        crs: Optional EPSG code
    
    Returns:
        Coordinate object
    """
    return Coordinate(x, y, z, crs)


def create_bounding_box(min_x: float, min_y: float, max_x: float, max_y: float, crs: Optional[int] = None) -> BoundingBox:
    """Factory function to create BoundingBox objects.
    
    Args:
        min_x: Minimum X coordinate
        min_y: Minimum Y coordinate
        max_x: Maximum X coordinate
        max_y: Maximum Y coordinate
        crs: Optional EPSG code
    
    Returns:
        BoundingBox object
    """
    return BoundingBox(min_x, min_y, max_x, max_y, crs)


def create_geometry(geometry_type: Union[str, GeometryType], coordinates: Any, crs: Optional[int] = None, properties: Optional[Dict[str, Any]] = None) -> Geometry:
    """Factory function to create Geometry objects.
    
    Args:
        geometry_type: Type of geometry
        coordinates: Geometry coordinates
        crs: Optional EPSG code
        properties: Optional properties
    
    Returns:
        Geometry object
    """
    if isinstance(geometry_type, str):
        geometry_type = GeometryType(geometry_type)
    return Geometry(geometry_type, coordinates, crs, properties or {})


def create_layer_config(name: str, layer_type: Union[str, LayerType], **kwargs) -> LayerConfig:
    """Factory function to create LayerConfig objects.
    
    Args:
        name: Layer name
        layer_type: Type of layer
        **kwargs: Additional configuration options
    
    Returns:
        LayerConfig object
    """
    if isinstance(layer_type, str):
        layer_type = LayerType(layer_type)
    return LayerConfig(name=name, layer_type=layer_type, **kwargs)