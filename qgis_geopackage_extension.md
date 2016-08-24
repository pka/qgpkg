# GeoPackage 1.0 Extension

Extension follows template from Annex I of the OGC [GeoPackage 1.0 Specification](http://www.geopackage.org/).

## Extension Title

QGIS map information

## Introduction

Store QGIS projects with their resources like images in print templates in a GeoPackage file.

## Extension Author

Pirmin Kalberer

## Extension Name or Template

```sql
INSERT INTO gpkg_extensions
  (table_name, column_name, extension_name, definition, scope)
VALUES
  (
    NULL,
    NULL,
    'qgis',
    'http://github.com/pka/qgpkg/blob/master/qgis_geopackage_extension.md',
    'read-write'
  );
```

## Extension Type

Extension of Existing Requirement in Clause 2.

## Applicability

This extension applies to additional tables `qgis_projects`, `qgis_resources` 
and `qgis_layer_styles`.

## Scope

Read-write

## Requirements

Definition of extension and interdependencies with other extensions if
any.

### GeoPackage

#### Extension tables

An Extended GeoPackage with QGIS support MAY contain the following tables or views:

**qgis_projects**

| Column | type | Desctiption |
| --- | --- | --- | --- |
| name | text NOT NULL | Project name (file name) |
| xml | text NOT NULL | Project file content (.qgs) in XML format |

**qgis_resources**

| Column | type | Desctiption |
| --- | --- | --- | --- |
| name | text NOT NULL | Name of resource (file name) |
| type | text NOT NULL | image|svg |
| blob | blob NOT NULL | Binary content of file |

**qgis_layer_styles**

| Column | type | Desctiption |
| --- | --- | --- | --- |
| id | INTEGER | PRIMARY KEY |
| f_table_catalog | varchar(256) | |
| f_table_schema | varchar(256) | |
| f_table_name | varchar(256) | |
| f_geometry_column | varchar(256) | |
| styleName | varchar(30) | |
| styleQML | text | |
| styleSLD | text | |
| useAsDefault | boolean | |
| description | text | |
| owner | varchar(30) | |
| ui | text | |
| update_time | timestamp | |

### GeoPackage SQLite Configuration

None

### GeoPackage SQLite Extension

None

## Abstract Test Suite

N/A

## Examples (Informative)

N/A
