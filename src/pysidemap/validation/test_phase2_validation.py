"""
PySideMap Phase 2 Validation Script

This script validates that all Phase 2 foundational components work together
and are ready for User Story 1 implementation.

Tests:
1. Import all Phase 2 components
2. Test basic functionality of core classes
3. Verify component integration
4. Check that basic map display widget can be instantiated
5. Validate API consistency
"""

import sys
import traceback
from typing import List, Dict, Any, Optional


def test_imports() -> Dict[str, bool]:
    """Test that all Phase 2 components can be imported."""
    results = {}
    
    try:
        # Test main package import
        import pysidemap
        results["main_package"] = True
        print("✅ Main package import: SUCCESS")
    except Exception as e:
        results["main_package"] = False
        print(f"❌ Main package import: FAILED - {e}")
    
    try:
        # Test exception classes
        from pysidemap.exceptions import (
            PySideMapError, DataLoadError, CRSError, MemoryError, 
            NetworkError, ValidationError, InitializationError, PerformanceError
        )
        results["exceptions"] = True
        print("✅ Exception classes: SUCCESS")
    except Exception as e:
        results["exceptions"] = False
        print(f"❌ Exception classes: FAILED - {e}")
    
    try:
        # Test type definitions
        from pysidemap.utils.types import (
            Coordinate, BoundingBox, Geometry, LayerConfig, Feature,
            GeometryType, LayerType, create_coordinate, create_bounding_box
        )
        results["types"] = True
        print("✅ Type definitions: SUCCESS")
    except Exception as e:
        results["types"] = False
        print(f"❌ Type definitions: FAILED - {e}")
    
    try:
        # Test coordinate systems
        from pysidemap.coordinate_systems import (
            CRSManager, CRSInfo, WGS84, WEB_MERCATOR,
            create_coordinate_in_crs, wgs84_to_web_mercator
        )
        results["coordinate_systems"] = True
        print("✅ Coordinate systems: SUCCESS")
    except Exception as e:
        results["coordinate_systems"] = False
        print(f"❌ Coordinate systems: FAILED - {e}")
    
    try:
        # Test layer framework
        from pysidemap.layers import (
            BaseLayer, RasterLayer, LayerState, LayerEventType,
            BaseLayerError, RasterLayerError, create_raster_layer
        )
        results["layers"] = True
        print("✅ Layer framework: SUCCESS")
    except Exception as e:
        results["layers"] = False
        print(f"❌ Layer framework: FAILED - {e}")
    
    try:
        # Test widgets (PySide6 dependent)
        try:
            from PySide6.QtWidgets import QApplication
            from pysidemap.widgets import (
                GISGraphicsView, ViewState, InteractionMode,
                GISViewError, create_gis_view
            )
            results["widgets"] = True
            print("✅ Widget framework: SUCCESS")
        except ImportError:
            results["widgets"] = "SKIPPED"
            print("⚠️  Widget framework: SKIPPED (PySide6 not available)")
    except Exception as e:
        results["widgets"] = False
        print(f"❌ Widget framework: FAILED - {e}")
    
    return results


def test_basic_functionality() -> Dict[str, bool]:
    """Test basic functionality of core components."""
    results = {}
    
    try:
        # Test coordinate creation and manipulation
        from pysidemap import Coordinate, create_coordinate
        coord = create_coordinate(10.0, 20.0, crs=4326)
        assert coord.x == 10.0
        assert coord.y == 20.0
        assert coord.crs == 4326
        results["coordinate_creation"] = True
        print("✅ Coordinate creation: SUCCESS")
    except Exception as e:
        results["coordinate_creation"] = False
        print(f"❌ Coordinate creation: FAILED - {e}")
    
    try:
        # Test bounding box creation
        from pysidemap import BoundingBox, create_bounding_box
        bbox = create_bounding_box(0, 0, 10, 10, crs=4326)
        assert bbox.min_x == 0
        assert bbox.max_x == 10
        assert bbox.crs == 4326
        results["bounding_box_creation"] = True
        print("✅ Bounding box creation: SUCCESS")
    except Exception as e:
        results["bounding_box_creation"] = False
        print(f"❌ Bounding box creation: FAILED - {e}")
    
    try:
        # Test CRS manager
        from pysidemap.coordinate_systems import CRSManager, WGS84, WEB_MERCATOR
        crs_manager = CRSManager(default_crs=WGS84)
        assert crs_manager.get_default_crs() == WGS84
        assert crs_manager.is_supported(WGS84)
        assert crs_manager.is_supported(WEB_MERCATOR)
        results["crs_manager"] = True
        print("✅ CRS manager: SUCCESS")
    except Exception as e:
        results["crs_manager"] = False
        print(f"❌ CRS manager: FAILED - {e}")
    
    try:
        # Test layer configuration
        from pysidemap.utils.types import LayerConfig, LayerType
        config = LayerConfig(
            layer_id="test_layer",
            name="Test Layer",
            layer_type=LayerType.RASTER,
            data_source={"type": "xyz_tiles", "url_template": "https://tile.example.com/{z}/{x}/{y}.png"}
        )
        assert config.name == "Test Layer"
        assert config.layer_type == LayerType.RASTER
        results["layer_config"] = True
        print("✅ Layer configuration: SUCCESS")
    except Exception as e:
        results["layer_config"] = False
        print(f"❌ Layer configuration: FAILED - {e}")
    
    try:
        # Test raster layer creation
        from pysidemap.layers import create_raster_layer, LayerType
        from pysidemap.utils.types import LayerConfig
        
        config = create_raster_layer(
            name="OpenStreetMap",
            data_source="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        )
        assert config.name == "OpenStreetMap"
        results["raster_layer_creation"] = True
        print("✅ Raster layer creation: SUCCESS")
    except Exception as e:
        results["raster_layer_creation"] = False
        print(f"❌ Raster layer creation: FAILED - {e}")
    
    return results


def test_component_integration() -> Dict[str, bool]:
    """Test that components can work together."""
    results = {}
    
    try:
        # Test CRS transformation integration
        from pysidemap.coordinate_systems import CRSManager, WGS84, WEB_MERCATOR
        from pysidemap.utils.types import Coordinate
        
        crs_manager = CRSManager()
        coord = Coordinate(-74.006, 40.7128, crs=WGS84)  # New York
        
        # This should work without error
        transformed = crs_manager.transform_point(coord, WEB_MERCATOR)
        assert transformed.crs == WEB_MERCATOR
        results["crs_transformation"] = True
        print("✅ CRS transformation: SUCCESS")
    except Exception as e:
        results["crs_transformation"] = False
        print(f"❌ CRS transformation: FAILED - {e}")
    
    try:
        # Test layer lifecycle with CRS manager
        from pysidemap.layers import BaseLayer, RasterLayer, LayerState
        from pysidemap.coordinate_systems import CRSManager
        from pysidemap.utils.types import LayerConfig, LayerType
        
        config = LayerConfig(
            layer_id="integration_test",
            name="Integration Test",
            layer_type=LayerType.RASTER,
            data_source={"type": "xyz_tiles", "url_template": "https://example.com/{z}/{x}/{y}.png"}
        )
        
        crs_manager = CRSManager()
        layer = RasterLayer(config=config, crs_manager=crs_manager)
        
        # Test layer initialization
        assert layer.layer_id == "integration_test"
        assert layer.state == LayerState.READY
        assert layer.crs_manager == crs_manager
        results["layer_crs_integration"] = True
        print("✅ Layer-CRS integration: SUCCESS")
    except Exception as e:
        results["layer_crs_integration"] = False
        print(f"❌ Layer-CRS integration: FAILED - {e}")
    
    try:
        # Test coordinate utilities
        from pysidemap.coordinate_systems import create_coordinate_in_crs, WGS84, WEB_MERCATOR
        
        coord_wgs84 = create_coordinate_in_crs(-74.006, 40.7128, WGS84)
        coord_web_mercator = create_coordinate_in_crs(-8234567, 4966865, WEB_MERCATOR)
        
        assert coord_wgs84.crs == WGS84
        assert coord_web_mercator.crs == WEB_MERCATOR
        results["coordinate_utilities"] = True
        print("✅ Coordinate utilities: SUCCESS")
    except Exception as e:
        results["coordinate_utilities"] = False
        print(f"❌ Coordinate utilities: FAILED - {e}")
    
    return results


def test_widget_instantiation() -> Dict[str, Any]:
    """Test that basic map display widget can be instantiated."""
    results = {}
    
    try:
        # Check if PySide6 is available
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from pysidemap.widgets import GISGraphicsView, create_gis_view
        
        # Test widget creation
        widget = create_gis_view(initial_crs=4326)
        assert widget is not None
        assert widget.layer_count == 0
        results["widget_instantiation"] = True
        results["details"] = "Widget created successfully"
        print("✅ Widget instantiation: SUCCESS")
        
        # Test layer management (basic)
        from pysidemap.layers import create_raster_layer
        
        layer = create_raster_layer(
            name="Test Layer",
            data_source="https://tile.example.com/{z}/{x}/{y}.png"
        )
        
        layer_id = widget.add_layer(layer)
        assert layer_id is not None
        assert widget.layer_count == 1
        
        # Test layer removal
        success = widget.remove_layer(layer_id)
        assert success is True
        assert widget.layer_count == 0
        
        results["layer_management"] = True
        results["details"] = "Widget and layer management working"
        print("✅ Layer management: SUCCESS")
        
    except ImportError:
        results["widget_instantiation"] = "SKIPPED"
        results["details"] = "PySide6 not available"
        print("⚠️  Widget instantiation: SKIPPED (PySide6 not available)")
    except Exception as e:
        results["widget_instantiation"] = False
        results["details"] = str(e)
        print(f"❌ Widget instantiation: FAILED - {e}")
        traceback.print_exc()
    
    return results


def validate_phase2_completion() -> Dict[str, Any]:
    """Main validation function for Phase 2 completion."""
    print("🔍 Starting Phase 2 Validation")
    print("=" * 50)
    
    results = {
        "imports": test_imports(),
        "functionality": test_basic_functionality(),
        "integration": test_component_integration(),
        "widget_instantiation": test_widget_instantiation()
    }
    
    # Calculate success metrics
    total_tests = 0
    passed_tests = 0
    
    for category, tests in results.items():
        if isinstance(tests, dict):
            for test_name, test_result in tests.items():
                if test_result is True:
                    passed_tests += 1
                elif test_result is False:
                    pass  # Don't count failures
                total_tests += 1
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 PHASE 2 VALIDATION RESULTS")
    print("=" * 50)
    
    for category, tests in results.items():
        print(f"\n{category.upper()}:")
        if isinstance(tests, dict):
            for test_name, test_result in tests.items():
                status = "✅ PASS" if test_result is True else ("⏭️  SKIP" if test_result == "SKIPPED" else "❌ FAIL")
                print(f"  {test_name}: {status}")
    
    print(f"\n🎯 SUCCESS RATE: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 Phase 2 validation: PASSED - Ready for User Story 1!")
        return {
            "status": "PASSED",
            "success_rate": success_rate,
            "details": results
        }
    else:
        print("⚠️  Phase 2 validation: NEEDS ATTENTION")
        return {
            "status": "NEEDS_ATTENTION",
            "success_rate": success_rate,
            "details": results
        }


if __name__ == "__main__":
    validation_result = validate_phase2_completion()
    
    if validation_result["status"] == "PASSED":
        print("\n🚀 READY FOR PHASE 3 - USER STORY 1 IMPLEMENTATION")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED - REVIEW COMPONENTS")
        sys.exit(1)