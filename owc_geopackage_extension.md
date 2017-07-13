# GeoPackage 1.0 Extension

**DRAFT**

Extension follows template from Annex I of the OGC [GeoPackage 1.0 Specification](http://www.geopackage.org/).

## Extension Title

**OWS Context**

## Introduction

The main goal of the extension is to store context and styling of a mapping project as part of a GeoPackage file containing the data it refers to. The extension aims at similar use cases as presented in [The USGS GeoPackage Styling Experiment in Testbed 12](http://docs.opengeospatial.org/per/16-037.html), however the approach is a bit different. 

Approach: Table owc_context stores one or multiple OWS Context files that defines a set of layers on a set of data tables using certain styles. Any data table or style can be referenced by a layer in an OWS Context multiple times. Table owc_style  defines which styles are available. Resources from owc_resources can be referenced from metadata, styles or context, to enable inclusion of images, pdf, fonts etc.

[OWS Context](http://www.owscontext.org/) 1.0 defines the capability to reference layers from OWS services and certain filetypes (gml/kml). In this extension we introduce the capability in OWS context to reference tables local to the Geopackage.

The OWS Context specification is extended with an `offeringtype="gpkg"` and OWS-context is extended to support referencing resources local to the Geopackage by using `#table={table}[&{fieldname}={value}]`.

```xml
<owc:offering code="http://www.opengis.net/spec/owc-atom/1.0/req/gpkg">
  <owc:content type="application/x-sqlite" href="#table=MyPoints" />
  <owc:styleSet>
    <owc:name>simple_point</owc:name>
    <owc:title>Simple point</owc:title>
    <owc:content href="#table=owc_style&amp;name=simplePoint" type="application/sld+xml"/>
  </owc:styleSet>
</owc:offering>
```

OWC offering MUST include a styleSet reference, referencing an external SLD file or an SLD from the owc_style table.


## Extension Author

Paul van Genuchten, Joana Simoes.


## Extension Name or Template

`owc`

## Extension Type

Extension of concepts

## Applicability

This extension applies to additional tables `owc_context`, `owc_resources`, `owc_style`.

## Scope

Read-write

## Requirements

### GeoPackage

#### Extension tables

An Extended GeoPackage with Context support MAY contain the following tables or views:

**owc_context**

| Column | type | Desctiption |
|----|-----|----|
| name | varchar(30) unique | Context name |
| abstract | text | Context abstract |
| author | text | Comma separated list of authors |
| language | text | based on RFC-3066 code|
| mime_type | text NOT NULL | [mime type](http://www.iana.org/assignments/media-types/media-types.xhtml) of context ([application/atom+xml](https://portal.opengeospatial.org/files/?artifact_id=55183) / [application/json](https://github.com/opengeospatial/owscontext/tree/master/json) / [application/vnd.owc+xml](https://portal.opengeospatial.org/files/?artifact_id=55182)) | 
| content | text NOT NULL | Content of OWS_Context encoded as indicated in `mime_type` |

**owc_style**

| Column | type | Desctiption |
|----|-----|----|
| name | varchar(30) unique | |
| abstract | text | |
| mime_type | varchar(30) | The [mime type](http://www.iana.org/assignments/media-types/media-types.xhtml) of the style ( [application/vnd.sld+xml](http://www.opengeospatial.org/standards/sld) / text/css / application/json)  |
| content | text NOT NULL | Content of the style encoded as indicated in `mime_type`  |

**owc_resource**

| Column | type | Desctiption |
|----|-----|----|
| name | varchar(30) unique | Name of resource (file name) |
| mime_type | text NOT NULL | The [mime type](http://www.iana.org/assignments/media-types/media-types.xhtml) of the resource  (image/png, application/pdf, ...) |
| content | blob NOT NULL | Binary content of resource |


### GeoPackage SQLite Configuration

None

### GeoPackage SQLite Extension

None
