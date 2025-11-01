"""
PySideMap Coordinate Reference System Manager

Manages coordinate transformations and coordinate reference system operations
using pyproj as the primary transformation engine.

This module provides:
- Basic support for EPSG:4326 (WGS84) and EPSG:3857 (Web Mercator)
- Coordinate transformation using pyproj
- Integration with coordinate systems from data-model.md
- Comprehensive error handling for CRS operations
"""

from typing import Union, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import logging

try:
    import pyproj
    from pyproj import CRS, Transformer, Proj
    PYPROJ_AVAILABLE = True
except ImportError:
    pyproj = None
    CRS = None
    Transformer = None
    Proj = None
    PYPROJ_AVAILABLE = False

from ..utils.types import Coordinate, BoundingBox
from ..exceptions import CRSError


# Setup logging for CRS operations
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CRSInfo:
    """Information about a coordinate reference system.
    
    Attributes:
        epsg_code: EPSG code if available
        proj4_string: PROJ4 projection definition
        wkt: Well-Known Text representation
        name: Human-readable CRS name
        authority: Defining organization
        accuracy: Transformation accuracy in meters (if known)
    """
    epsg_code: Optional[int]
    proj4_string: str
    wkt: Optional[str]
    name: str
    authority: str
    accuracy: Optional[float] = None


class CRSManager:
    """Manages coordinate reference systems and transformations.
    
    This class provides a high-level interface for coordinate transformations
    and CRS management using pyproj as the backend engine.
    
    Attributes:
        default_crs: Default coordinate reference system for new coordinates
        cache_size: Number of transformers to cache for performance
    """
    
    # Predefined CRS information for common systems
    _CRS_DATABASE = {
        4326: CRSInfo(
            epsg_code=4326,
            proj4_string="+proj=longlat +datum=WGS84 +no_defs",
            wkt='GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]',
            name="WGS 84 Geographic",
            authority="EPSG"
        ),
        3857: CRSInfo(
            epsg_code=3857,
            proj4_string="+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs",
            wkt='PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","3857"]]',
            name="WGS 84 / Pseudo-Mercator",
            authority="EPSG"
        )
    }
    
    def __init__(self, default_crs: int = 4326, cache_size: int = 100):
        """Initialize CRS manager.
        
        Args:
            default_crs: Default CRS for new coordinates (EPSG code)
            cache_size: Number of transformers to cache
            
        Raises:
            CRSError: If pyproj is not available
        """
        if not PYPROJ_AVAILABLE:
            raise CRSError(
                "pyproj is required for coordinate transformations. "
                "Install with: pip install pyproj"
            )
        
        self.default_crs = default_crs
        self.cache_size = cache_size
        self._transformer_cache: Dict[str, Transformer] = {}
        self._crs_cache: Dict[int, CRS] = {}
        
        # Initialize default CRS in cache
        self._get_crs(self.default_crs)
        logger.info(f"CRS Manager initialized with default CRS: EPSG:{default_crs}")
    
    def _get_crs(self, crs_code: int) -> CRS:
        """Get CRS object from cache or create new.
        
        Args:
            crs_code: EPSG code
            
        Returns:
            CRS object
            
        Raises:
            CRSError: If CRS code is not supported
        """
        if crs_code not in self._crs_cache:
            try:
                if crs_code in self._CRS_DATABASE:
                    # Use predefined CRS info
                    crs_info = self._CRS_DATABASE[crs_code]
                    self._crs_cache[crs_code] = CRS.from_epsg(crs_code)
                else:
                    # Try to create from EPSG code
                    self._crs_cache[crs_code] = CRS.from_epsg(crs_code)
            except Exception as e:
                raise CRSError(
                    f"Failed to create CRS for EPSG:{crs_code}: {e}",
                    source_crs=crs_code
                )
        
        return self._crs_cache[crs_code]
    
    def _get_transformer(self, from_crs: int, to_crs: int) -> Transformer:
        """Get transformer from cache or create new.
        
        Args:
            from_crs: Source CRS (EPSG code)
            to_crs: Target CRS (EPSG code)
            
        Returns:
            Transformer object
            
        Raises:
            CRSError: If transformer creation fails
        """
        cache_key = f"{from_crs}_to_{to_crs}"
        
        if cache_key not in self._transformer_cache:
            try:
                from_crs_obj = self._get_crs(from_crs)
                to_crs_obj = self._get_crs(to_crs)
                
                self._transformer_cache[cache_key] = Transformer.from_crs(
                    from_crs_obj, to_crs_obj, always_xy=True
                )
                
                # Manage cache size
                if len(self._transformer_cache) > self.cache_size:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(self._transformer_cache))
                    del self._transformer_cache[oldest_key]
                    
            except Exception as e:
                raise CRSError(
                    f"Failed to create transformer from EPSG:{from_crs} to EPSG:{to_crs}: {e}",
                    source_crs=from_crs,
                    target_crs=to_crs
                )
        
        return self._transformer_cache[cache_key]
    
    def transform_point(self, 
                       coordinate: Coordinate, 
                       target_crs: int,
                       source_crs: Optional[int] = None) -> Coordinate:
        """Transform a coordinate from one CRS to another.
        
        Args:
            coordinate: Source coordinate
            target_crs: Target coordinate reference system (EPSG code)
            source_crs: Source CRS (uses coordinate.crs if not specified)
            
        Returns:
            Transformed coordinate
            
        Raises:
            CRSError: If transformation fails
        """
        if source_crs is None:
            source_crs = coordinate.crs
            if source_crs is None:
                raise CRSError(
                    "Source CRS must be specified either in coordinate or as parameter",
                    coordinates=(coordinate.x, coordinate.y)
                )
        
        if source_crs == target_crs:
            # No transformation needed
            return Coordinate(coordinate.x, coordinate.y, coordinate.z, target_crs)
        
        try:
            transformer = self._get_transformer(source_crs, target_crs)
            
            # Transform coordinates
            x, y = transformer.transform(coordinate.x, coordinate.y)
            
            # Transform Z coordinate if present
            z = coordinate.z
            if z is not None:
                # Note: pyproj doesn't handle vertical transformations by default
                # For simplicity, we just copy the Z value
                logger.warning("Z coordinate transformation not supported, copying value as-is")
            
            return Coordinate(x, y, z, target_crs)
            
        except Exception as e:
            raise CRSError(
                f"Failed to transform coordinate: {e}",
                source_crs=source_crs,
                target_crs=target_crs,
                coordinates=(coordinate.x, coordinate.y)
            )
    
    def transform_bbox(self, 
                      bbox: BoundingBox, 
                      target_crs: int,
                      source_crs: Optional[int] = None) -> BoundingBox:
        """Transform a bounding box from one CRS to another.
        
        Args:
            bbox: Source bounding box
            target_crs: Target coordinate reference system (EPSG code)
            source_crs: Source CRS (uses bbox.crs if not specified)
            
        Returns:
            Transformed bounding box
            
        Raises:
            CRSError: If transformation fails
        """
        if source_crs is None:
            source_crs = bbox.crs
            if source_crs is None:
                raise CRSError(
                    "Source CRS must be specified either in bbox or as parameter",
                    coordinates=(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
                )
        
        if source_crs == target_crs:
            # No transformation needed
            return BoundingBox(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y, target_crs)
        
        try:
            # Transform all four corners
            corners = [
                (bbox.min_x, bbox.min_y),  # Bottom-left
                (bbox.max_x, bbox.min_y),  # Bottom-right
                (bbox.max_x, bbox.max_y),  # Top-right
                (bbox.min_x, bbox.max_y)   # Top-left
            ]
            
            transformer = self._get_transformer(source_crs, target_crs)
            transformed_corners = [transformer.transform(x, y) for x, y in corners]
            
            # Find new bounds
            x_coords = [x for x, y in transformed_corners]
            y_coords = [y for x, y in transformed_corners]
            
            new_min_x = min(x_coords)
            new_max_x = max(x_coords)
            new_min_y = min(y_coords)
            new_max_y = max(y_coords)
            
            return BoundingBox(new_min_x, new_min_y, new_max_x, new_max_y, target_crs)
            
        except Exception as e:
            raise CRSError(
                f"Failed to transform bounding box: {e}",
                source_crs=source_crs,
                target_crs=target_crs
            )
    
    def get_crs_info(self, crs_code: int) -> CRSInfo:
        """Get information about a coordinate reference system.
        
        Args:
            crs_code: EPSG code
            
        Returns:
            CRS information object
            
        Raises:
            CRSError: If CRS code is not supported
        """
        if crs_code not in self._CRS_DATABASE:
            try:
                crs_obj = self._get_crs(crs_code)
                return CRSInfo(
                    epsg_code=crs_code,
                    proj4_string=crs_obj.to_proj4(),
                    wkt=crs_obj.to_wkt(),
                    name=crs_obj.to_string(),
                    authority="EPSG"
                )
            except Exception as e:
                raise CRSError(
                    f"Failed to get CRS info for EPSG:{crs_code}: {e}",
                    source_crs=crs_code
                )
        
        return self._CRS_DATABASE[crs_code]
    
    def is_supported(self, crs_code: int) -> bool:
        """Check if a CRS is supported.
        
        Args:
            crs_code: EPSG code
            
        Returns:
            True if CRS is supported
        """
        try:
            self._get_crs(crs_code)
            return True
        except CRSError:
            return False
    
    def get_supported_crs(self) -> Dict[int, CRSInfo]:
        """Get all supported coordinate reference systems.
        
        Returns:
            Dictionary of supported CRS codes to CRS info
        """
        return self._CRS_DATABASE.copy()
    
    def get_default_crs(self) -> int:
        """Get the default CRS.
        
        Returns:
            Default CRS EPSG code
        """
        return self.default_crs
    
    def set_default_crs(self, crs_code: int) -> None:
        """Set the default CRS.
        
        Args:
            crs_code: New default CRS (EPSG code)
            
        Raises:
            CRSError: If CRS is not supported
        """
        if not self.is_supported(crs_code):
            raise CRSError(f"CRS EPSG:{crs_code} is not supported", source_crs=crs_code)
        
        self.default_crs = crs_code
        logger.info(f"Default CRS changed to EPSG:{crs_code}")
    
    def clear_cache(self) -> None:
        """Clear the transformer and CRS caches."""
        self._transformer_cache.clear()
        self._crs_cache.clear()
        logger.info("CRS Manager caches cleared")
    
    def __str__(self) -> str:
        """String representation of CRS manager."""
        return f"CRSManager(default_crs=EPSG:{self.default_crs}, cache_size={self.cache_size})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"CRSManager(default_crs={self.default_crs}, "
                f"cache_size={self.cache_size}, "
                f"supported_crs={len(self._CRS_DATABASE)})")


# Common CRS constants for convenience
WGS84 = 4326  # WGS84 Geographic
WEB_MERCATOR = 3857  # Web Mercator / Pseudo-Mercator


# Utility functions for common transformations
def create_coordinate_in_crs(x: float, y: float, crs: int = WGS84, z: Optional[float] = None) -> Coordinate:
    """Create a coordinate in the specified CRS.
    
    Args:
        x: X coordinate
        y: Y coordinate
        crs: Coordinate reference system (EPSG code)
        z: Optional Z coordinate
        
    Returns:
        Coordinate object
    """
    return Coordinate(x, y, z, crs)


def wgs84_to_web_mercator(coordinate: Coordinate, crs_manager: Optional[CRSManager] = None) -> Coordinate:
    """Convert WGS84 coordinate to Web Mercator.
    
    Args:
        coordinate: WGS84 coordinate
        crs_manager: CRS manager instance (creates default if None)
        
    Returns:
        Web Mercator coordinate
        
    Raises:
        CRSError: If transformation fails
    """
    if crs_manager is None:
        crs_manager = CRSManager()
    
    return crs_manager.transform_point(coordinate, WEB_MERCATOR)


def web_mercator_to_wgs84(coordinate: Coordinate, crs_manager: Optional[CRSManager] = None) -> Coordinate:
    """Convert Web Mercator coordinate to WGS84.
    
    Args:
        coordinate: Web Mercator coordinate
        crs_manager: CRS manager instance (creates default if None)
        
    Returns:
        WGS84 coordinate
        
    Raises:
        CRSError: If transformation fails
    """
    if crs_manager is None:
        crs_manager = CRSManager()
    
    return crs_manager.transform_point(coordinate, WGS84)