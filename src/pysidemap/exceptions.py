"""
PySideMap Exception Classes

Base exception classes for comprehensive error handling across the GIS widget.
All exceptions provide context-specific information for debugging and user feedback.
"""

from typing import Optional, Dict, Any, Union
import traceback


class PySideMapError(Exception):
    """Base exception for all PySideMap errors."""
    
    def __init__(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause
        self.traceback_str = traceback.format_exc() if cause else None
    
    def __str__(self) -> str:
        """Return formatted error message with context."""
        base_msg = super().__str__()
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base_msg} (context: {context_str})"
        return base_msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
            "traceback": self.traceback_str
        }


class DataLoadError(PySideMapError):
    """Raised when spatial data cannot be loaded or is invalid.
    
    This exception covers failures in:
    - File format parsing (Shapefile, GeoJSON, KML, etc.)
    - Database connection failures
    - Web service request failures
    - Data validation errors
    - Corrupted or inaccessible data sources
    
    Attributes:
        data_source: Path, URL, or identifier of the failed data source
        data_format: Expected or detected data format
        file_size: Size of the data file if applicable
        validation_errors: List of specific validation failures
    """
    
    def __init__(
        self, 
        message: str, 
        data_source: Optional[str] = None,
        data_format: Optional[str] = None,
        file_size: Optional[int] = None,
        validation_errors: Optional[list] = None,
        **kwargs
    ):
        context = {
            "data_source": data_source,
            "data_format": data_format,
            "file_size": file_size,
            "validation_errors": validation_errors or []
        }
        context.update(kwargs)
        super().__init__(message, context)
        self.data_source = data_source
        self.data_format = data_format
        self.file_size = file_size
        self.validation_errors = validation_errors or []


class CRSError(PySideMapError):
    """Raised when coordinate reference system operations fail.
    
    This exception covers failures in:
    - CRS definition parsing
    - Coordinate transformations
    - CRS compatibility checks
    - PROJ projection errors
    - Coordinate bounds violations
    
    Attributes:
        source_crs: Source coordinate reference system
        target_crs: Target coordinate reference system  
        coordinates: Coordinates that caused the error
        transformation_method: Method used for transformation
    """
    
    def __init__(
        self, 
        message: str, 
        source_crs: Optional[Union[str, int]] = None,
        target_crs: Optional[Union[str, int]] = None,
        coordinates: Optional[tuple] = None,
        transformation_method: Optional[str] = None,
        **kwargs
    ):
        context = {
            "source_crs": source_crs,
            "target_crs": target_crs,
            "coordinates": coordinates,
            "transformation_method": transformation_method
        }
        context.update(kwargs)
        super().__init__(message, context)
        self.source_crs = source_crs
        self.target_crs = target_crs
        self.coordinates = coordinates
        self.transformation_method = transformation_method


class MemoryError(PySideMapError):
    """Raised when memory constraints are exceeded.
    
    This exception covers:
    - Dataset too large for available memory
    - Memory allocation failures during processing
    - Cache size exceeded
    - Memory leak detection
    
    Attributes:
        requested_mb: Memory requested in megabytes
        available_mb: Memory available in megabytes
        operation: Operation that triggered the error
        dataset_size: Size of the dataset being processed
    """
    
    def __init__(
        self, 
        message: str, 
        requested_mb: Optional[float] = None,
        available_mb: Optional[float] = None,
        operation: Optional[str] = None,
        dataset_size: Optional[int] = None,
        **kwargs
    ):
        context = {
            "requested_mb": requested_mb,
            "available_mb": available_mb,
            "operation": operation,
            "dataset_size": dataset_size
        }
        context.update(kwargs)
        super().__init__(message, context)
        self.requested_mb = requested_mb
        self.available_mb = available_mb
        self.operation = operation
        self.dataset_size = dataset_size


class NetworkError(PySideMapError):
    """Raised when network operations fail.
    
    This exception covers:
    - Web service connection failures
    - HTTP request timeouts
    - DNS resolution failures
    - SSL/TLS certificate errors
    - Rate limiting responses
    
    Attributes:
        url: The URL that failed
        http_status: HTTP status code if available
        response_time: Time taken before failure
        request_method: HTTP method used
        headers: Request headers sent
    """
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        http_status: Optional[int] = None,
        response_time: Optional[float] = None,
        request_method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        context = {
            "url": url,
            "http_status": http_status,
            "response_time": response_time,
            "request_method": request_method,
            "headers": headers or {}
        }
        context.update(kwargs)
        super().__init__(message, context)
        self.url = url
        self.http_status = http_status
        self.response_time = response_time
        self.request_method = request_method
        self.headers = headers or {}


class ValidationError(PySideMapError):
    """Raised when data validation fails.
    
    This exception covers:
    - Geometry validation failures
    - Attribute schema violations
    - Coordinate bounds violations
    - Data integrity check failures
    - Business rule violations
    
    Attributes:
        validation_type: Type of validation that failed
        invalid_value: The value that failed validation
        expected_type: Expected data type or format
        field_name: Name of the field that failed validation
    """
    
    def __init__(
        self, 
        message: str, 
        validation_type: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        field_name: Optional[str] = None,
        **kwargs
    ):
        context = {
            "validation_type": validation_type,
            "invalid_value": invalid_value,
            "expected_type": expected_type,
            "field_name": field_name
        }
        context.update(kwargs)
        super().__init__(message, context)
        self.validation_type = validation_type
        self.invalid_value = invalid_value
        self.expected_type = expected_type
        self.field_name = field_name


class InitializationError(PySideMapError):
    """Raised when widget initialization fails.
    
    This exception covers:
    - Graphics system initialization failures
    - Missing dependencies
    - Configuration errors
    - System capability limitations
    
    Attributes:
        component: Component that failed to initialize
        system_info: System information relevant to the error
        dependency_version: Version of missing or incompatible dependency
    """
    
    def __init__(
        self, 
        message: str, 
        component: Optional[str] = None,
        system_info: Optional[Dict[str, Any]] = None,
        dependency_version: Optional[str] = None,
        **kwargs
    ):
        context = {
            "component": component,
            "system_info": system_info or {},
            "dependency_version": dependency_version
        }
        context.update(kwargs)
        super().__init__(message, context)
        self.component = component
        self.system_info = system_info or {}
        self.dependency_version = dependency_version


class PerformanceError(PySideMapError):
    """Raised when performance targets cannot be met.
    
    This exception covers:
    - Rendering performance below target
    - Query response timeouts
    - Transformation performance issues
    - Memory usage above limits
    
    Attributes:
        operation: Operation that failed performance target
        actual_time: Actual time taken
        target_time: Target time requirement
        resource_usage: Resource usage at time of failure
    """
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        actual_time: Optional[float] = None,
        target_time: Optional[float] = None,
        resource_usage: Optional[Dict[str, float]] = None,
        **kwargs
    ):
        context = {
            "operation": operation,
            "actual_time": actual_time,
            "target_time": target_time,
            "resource_usage": resource_usage or {}
        }
        context.update(kwargs)
        super().__init__(message, context)
        self.operation = operation
        self.actual_time = actual_time
        self.target_time = target_time
        self.resource_usage = resource_usage or {}


# Exception mapping for error handling utilities
EXCEPTION_CATEGORIES = {
    "data_loading": DataLoadError,
    "coordinate_systems": CRSError,
    "memory": MemoryError,
    "network": NetworkError,
    "validation": ValidationError,
    "initialization": InitializationError,
    "performance": PerformanceError,
    "general": PySideMapError
}


def create_exception(category: str, *args, **kwargs) -> PySideMapError:
    """Factory function to create appropriate exception by category.
    
    Args:
        category: Exception category (data_loading, coordinate_systems, etc.)
        *args: Arguments passed to exception constructor
        **kwargs: Keyword arguments passed to exception constructor
    
    Returns:
        Instantiated exception of appropriate type
    
    Raises:
        ValueError: If category is not recognized
    """
    if category not in EXCEPTION_CATEGORIES:
        raise ValueError(f"Unknown exception category: {category}")
    
    exception_class = EXCEPTION_CATEGORIES[category]
    return exception_class(*args, **kwargs)