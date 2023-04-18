# tiff-inspector

**Tiff-Inspector** is a Python package that allows you to easily inspect the content and metadata of TIFF (Tagged Image File Format) files. The package provides an easy-to-use interface to view and analyze the hierarchical structure, series, levels, and tags of TIFF files.

## Features

* Inspect hierarchical structure of TIFF files.
* View metadata for series, levels, and individual pages.
* Extract and display image descriptions.
* Display metadata and tag values in a human-readable format.
* Supports XML and plain text descriptions.

## Installation

You can install Tiff-Inspector using pip:

```bash
pip install tiffinspector
```

## Dependencies

* tifffile
* xmltodict
* IPython


## Usage

To use the Tiff-Inspector package, simply import the TiffInspector class and create an instance with the path to the TIFF file.

```py
from tiffinspector import TiffInspector

# Instantiate the TiffInspector with the path to the TIFF file
tiff_inspector = TiffInspector("path/to/tiff/file.tif")

# Display the report
tiff_inspector.display_report(expanded=False, levels=None, max_text_length=None)
```

You can customize the display of the report by modifying the parameters:

* `expanded`: If set to True, it will expand the JSON structures in the report.
* `levels`: Set the number of tree levels to display. If set to None, it will display the entire tree.
* `max_text_length`: Set the maximum length of text values in the report. If set to None, it will display the entire text.

## Documentation

For more detailed information on the package and its functions, please refer to the source code and comments within the package.

## License

This package is released under the __MIT License__.