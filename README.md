# PySideMap - PySide6 GIS Visualization Widget

A production-ready PySide6 GIS visualization widget for seamless integration with PySide6 applications.

## Features

- Multi-layer geospatial data visualization
- Support for raster and vector data formats
- Coordinate reference system transformations
- Interactive map operations (zoom, pan, selection)
- Performance optimized with spatial indexing
- Asynchronous data loading

## Installation

```bash
pip install pysidemap
```

## Quick Start

```python
import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from pysidemap import GISGraphicsView

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Basic GIS Map")
        self.setGeometry(100, 100, 800, 600)
        
        # Create GIS widget
        self.gis_widget = GISGraphicsView(self)
        self.setCentralWidget(self.gis_widget)
        
        # Add a basic base layer
        self.gis_widget.add_xyz_layer(
            name="OpenStreetMap",
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            max_zoom=19
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapWindow()
    window.show()
    sys.exit(app.exec())
```

## Supported Data Formats

- **Vector**: Shapefile, GeoJSON, KML, GPX
- **Raster**: GeoTIFF, XYZ tiles, WMS services
- **Database**: PostGIS, GeoPackage
- **Web Services**: WMS, WFS

## Development

### Requirements

- Python 3.8+
- PySide6, pyproj, shapely, fiona, rasterio

### Setup

1. Clone repository
2. Install development dependencies: `pip install -e .[dev]`
3. Run tests: `pytest`
4. Run linting: `ruff check .`

## License

MIT License