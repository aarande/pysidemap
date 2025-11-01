"""PySideMap Coordinate Systems Package

This package contains coordinate reference system management and transformation utilities.
"""

# Phase 2+ - Available components
from .crs_manager import CRSManager, CRSInfo, WGS84, WEB_MERCATOR
from .crs_manager import (
    create_coordinate_in_crs,
    wgs84_to_web_mercator,
    web_mercator_to_wgs84
)

# Future Phase 4+ exports
# from .reprojection_engine import ReprojectionEngine

__all__ = [
    # Available in Phase 2
    "CRSManager",
    "CRSInfo", 
    "WGS84",
    "WEB_MERCATOR",
    "create_coordinate_in_crs",
    "wgs84_to_web_mercator",
    "web_mercator_to_wgs84",
    # Future exports
    # "ReprojectionEngine"  # Will be available in later phases
]