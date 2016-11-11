# GeoPackage 1.0 Extension

**DRAFT**

Extension follows template from Annex I of the OGC [GeoPackage 1.0 Specification](http://www.geopackage.org/).

## Extension Title

OWS Context

## Introduction

Goal: Store context of a mapping project including styling and resources in a single GeoPackage file.

Approach: introducing an OWS-context that defines a set of layers on a set of data tables using certain styles. Any data table can be referenced by the OWS context multiple times, table ows_style and ows_style-reference define which styles are available for that layer. Resources from ows_resources can be referenced to from metadata, styles and context, to enable inclusion of images, pdf, etc.

OWS-context 1.0 defines the capability to reference layers from OWS services and certain filetypes (gml/kml). In this scenario we introduce the capability to reference tables local to the Geopackage.

The ows-context specification is extended with an offeringtype="gpkg" and OWS-context is extended to support referencing resources local to the Geopackage by using #table={table}[&{fieldname}={value}].

```
<owc:offering
 code="http://www.opengis.net/spec/owc-atom/1.0/req/gpkg">
 <owc:content type="application/x-sqlite" href="#table=MyPoints" />
 <owc:styleSet>
 <owc:name>simple_point</owc:name>
 <owc:title>Simple point</owc:title>
 <owc:content href="#table=ows_style&name=simplePoint" type="application/sld+xml"/>
</owc:styleSet>
</owc:offering>
```



## Extension Author

Pirmin Kalberer, author_name `pka`.
Paul van Genuchten, author_name `pvgenuchten`.

## Extension Name or Template

`ows`

## Extension Type

Extension of Existing Requirement in Clause 2.

## Applicability

This extension applies to additional tables `ows_context`, `ows_resources`, `ows_style` and  `ows_style_reference`.

## Scope

Read-write

## Requirements

### GeoPackage

#### Extension tables

An Extended GeoPackage with OWS support MAY contain the following tables or views:

**ows_context**

| Column | type | Desctiption |
| --- | --- | --- | --- |
| name | varchar(30) unique | Context name |
| abstract | text | Context abstract |
| author | text | Comma separated list of authors |
| timestamp | datetime |  |
| language | text | based on RFC-3066 code|
| mime_type | text NOT NULL | [mime type](http://www.iana.org/assignments/media-types/media-types.xhtml) of context (application/atom+xml or application/json) | 
| content | text NOT NULL | Content of OWS_Context encoded as indicated in `encoding` |

**ows_resources**

| Column | type | Desctiption |
| --- | --- | --- | --- |
| name | varchar(30) unique | Name of resource (file name) |
| mime_type | text NOT NULL | The [mime type](http://www.iana.org/assignments/media-types/media-types.xhtml) of the resource  (image/png, application/pdf, ...) |
| content | blob NOT NULL | Binary content of resource |

**ows_style**

| Column | type | Desctiption |
| --- | --- | --- | --- |
| name | varchar(30) unique | |
| abstract | text | |
| mime_type | varchar(30) | The [mime type](http://www.iana.org/assignments/media-types/media-types.xhtml) of the style (application/vnd.sld+xml)  |
| content | text NOT NuLL | Content of the style encoded as indicated in `mime_type`  |
| timestamp | datetime | |

**ows_style_reference**

| Column | type | Desctiption |
| --- | --- | --- | --- |
| table_name | varchar(256) | |
| style_name | integer | Name of the style to apply for this layer |
| default | boolean | If the OWS context does not provide a style reference, then use this style as default for the layer |


### GeoPackage SQLite Configuration

None

### GeoPackage SQLite Extension

None
