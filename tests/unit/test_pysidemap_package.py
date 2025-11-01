"""Basic test to verify pytest setup works."""

import pytest


def test_pysidemap_import():
    """Test that the package can be imported successfully."""
    try:
        import pysidemap
        assert pysidemap.__version__ == "0.1.0"
    except ImportError:
        pytest.fail("Failed to import pysidemap package")


def test_package_structure():
    """Test that expected modules exist in the package."""
    import pysidemap
    
    # Check main classes exist
    expected_classes = [
        "GISGraphicsView",
        "BaseLayer",
        "RasterLayer", 
        "VectorLayer",
        "CRSManager"
    ]
    
    for class_name in expected_classes:
        assert hasattr(pysidemap, class_name), f"Missing class: {class_name}"


def test_exception_classes():
    """Test that exception classes are available."""
    import pysidemap
    
    expected_exceptions = [
        "DataLoadError",
        "CRSError",
        "MemoryError", 
        "NetworkError",
        "ValidationError"
    ]
    
    for exc_name in expected_exceptions:
        assert hasattr(pysidemap, exc_name), f"Missing exception: {exc_name}"