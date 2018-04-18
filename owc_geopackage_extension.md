# GeoPackage-OWC

QGPKG offers read support for the GeoPackage-OWC extension. Goal of the extension is to store context and styling of a mapping project in a standardised way as part of a GeoPackage file. The specification is maintained at [this repository](https://github.com/GeoCat/geopackage-owc-spec).

The extension introduces 3 tables;
- owc_context; which stores the project context (layer order)
- owc_style; which store the layer styling
- owc_resource; stores additional resources (thumbnails, fonts, documentation)

A GeoPackage-OWC example is provided [here](examples/multiple_layers.gpkg)
