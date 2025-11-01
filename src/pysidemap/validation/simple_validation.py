"""
PySideMap Phase 2 Simple Validation

Tests core Phase 2 components without emoji characters for Windows compatibility.
"""

import sys
import traceback


def test_imports():
    """Test that all Phase 2 components can be imported."""
    results = {}
    
    try:
        import pysidemap
        results["main_package"] = True
        print("SUCCESS: Main package import")
    except Exception as e:
        results["main_package"] = False
        print(f"FAILED: Main package import - {e}")
    
    try:
        from pysidemap.exceptions import PySideMapError, DataLoadError, CRSError, MemoryError
        results["exceptions"] = True
        print("SUCCESS: Exception classes")
    except Exception as e:
        results["exceptions"] = False
        print(f"FAILED: Exception classes - {e}")
    
    try:
        from pysidemap.utils.types import Coordinate, BoundingBox, create_coordinate, create_bounding_box
        results["types"] = True
        print("SUCCESS: Type definitions")
    except Exception as e:
        results["types"] = False
        print(f"FAILED: Type definitions - {e}")
    
    try:
        from pysidemap.coordinate_systems import CRSManager, WGS84, WEB_MERCATOR
        results["coordinate_systems"] = True
        print("SUCCESS: Coordinate systems")
    except Exception as e:
        results["coordinate_systems"] = False
        print(f"FAILED: Coordinate systems - {e}")
    
    try:
        from pysidemap.layers import BaseLayer, RasterLayer, LayerState
        results["layers"] = True
        print("SUCCESS: Layer framework")
    except Exception as e:
        results["layers"] = False
        print(f"FAILED: Layer framework - {e}")
    
    return results


def test_basic_functionality():
    """Test basic functionality."""
    results = {}
    
    try:
        from pysidemap import create_coordinate
        coord = create_coordinate(10.0, 20.0, crs=4326)
        assert coord.x == 10.0 and coord.y == 20.0
        results["coordinate_creation"] = True
        print("SUCCESS: Coordinate creation")
    except Exception as e:
        results["coordinate_creation"] = False
        print(f"FAILED: Coordinate creation - {e}")
    
    try:
        from pysidemap.coordinate_systems import CRSManager
        crs_manager = CRSManager(default_crs=4326)
        assert crs_manager.get_default_crs() == 4326
        results["crs_manager"] = True
        print("SUCCESS: CRS manager")
    except Exception as e:
        results["crs_manager"] = False
        print(f"FAILED: CRS manager - {e}")
    
    try:
        from pysidemap.layers import create_raster_layer
        layer = create_raster_layer("Test", "https://example.com/{z}/{x}/{y}.png")
        assert layer.name == "Test"
        results["raster_layer_creation"] = True
        print("SUCCESS: Raster layer creation")
    except Exception as e:
        results["raster_layer_creation"] = False
        print(f"FAILED: Raster layer creation - {e}")
    
    return results


def test_widget_instantiation():
    """Test widget instantiation if PySide6 is available."""
    results = {}
    
    try:
        from PySide6.QtWidgets import QApplication
        from pysidemap.widgets import create_gis_view
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        widget = create_gis_view(initial_crs=4326)
        assert widget.layer_count == 0
        results["widget_instantiation"] = True
        print("SUCCESS: Widget instantiation")
        return results
        
    except ImportError:
        results["widget_instantiation"] = "SKIPPED"
        print("SKIPPED: Widget instantiation (PySide6 not available)")
        return results
    except Exception as e:
        results["widget_instantiation"] = False
        print(f"FAILED: Widget instantiation - {e}")
        return results


def run_simple_validation():
    """Run simple validation without emojis."""
    print("Starting Phase 2 Simple Validation")
    print("=" * 50)
    
    import_results = test_imports()
    function_results = test_basic_functionality()
    widget_results = test_widget_instantiation()
    
    # Count successes
    total_tests = len(import_results) + len(function_results) + len(widget_results)
    successes = 0
    
    for results in [import_results, function_results, widget_results]:
        for test_name, result in results.items():
            if result is True:
                successes += 1
    
    success_rate = (successes / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "=" * 50)
    print("VALIDATION RESULTS")
    print("=" * 50)
    print(f"Success rate: {successes}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("RESULT: PASSED - Ready for Phase 3!")
        return True
    else:
        print("RESULT: NEEDS ATTENTION")
        return False


if __name__ == "__main__":
    success = run_simple_validation()
    sys.exit(0 if success else 1)