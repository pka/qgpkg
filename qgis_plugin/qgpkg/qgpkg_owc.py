from __future__ import print_function
import sys
import os
import sqlite3
import tempfile
import logging
from xml.etree import ElementTree as ET
from qgis.core import *
from qgis.utils import *
from PyQt4.QtXml import *
from PyQt4.QtCore import *
from StringIO import StringIO
from urlparse import urlparse
import sys

from qgpkg import QGpkg

logger = logging.getLogger('qgpkg')

# Debug code for Pycharm: remove as you please
sys.path.append('/home/joana/Downloads/pycharm-2016.3.3/debug-eggs/pycharm-debug.egg')
#import pydevd

#pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)


class QGpkg_owc (QGpkg):
    """Read and write QGIS mapping information in a GeoPackage database file, using this spec:
    https://github.com/pka/qgpkg/blob/master/ows_geopackage_extension.md
    """

    def write(self, project_path):
        self.log(logging.ERROR, u"Sorry, but it appears that writing into this geopackage extension was not implemented yet!")
        return

    def read(self, gpkg_path):

        iface.newProject(True)  # Clear project, before opening

        ''' Read QGIS project from GeoPackage '''
        # Check if it's a GeoPackage Database
        self.database_connect(gpkg_path)
        if not self.check_gpkg(gpkg_path):
            self.log(logging.ERROR, u"No valid GeoPackage selected.")
            return

        try:
            self.c.execute('SELECT table_name FROM gpkg_contents')
        except sqlite3.OperationalError:
            self.log(logging.ERROR, u"Unable to read table Name.")
            return

        table_names = self.c.fetchall()

        db_name = QFileInfo(gpkg_path).baseName()

        # Load OWS Context
        try:
            self.c.execute('SELECT content FROM owc_context')
        except sqlite3.OperationalError:
            self.log(logging.ERROR, u"Unable to read table owc_context.")
            return

        context = self.c.fetchone()

        if context is None:
            self.log(logging.ERROR, u"No record found on table owc_context!")
            return

        # Everything is read from the context
        self.loadContext(context[0], gpkg_path)

        # TODO: read resources

    def loadContext(self, context, gpkg_path):
        """Parses and applies the information on OWC_context.

        Args:
            context: The contents of owc_context table.
            gpkg_path: The path of the gpkg file.
        """
        it = ET.iterparse(StringIO(context))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        root = it.root

        # Missing mandatory elements
        # spec reference
        spec_elem = root.find("specReference")
        # if spec_elem is None:
        #    self.log(logging.ERROR, u"Could not parse project spec feference.")
        #    return
        # Language
        lang_elem = root.find("language")
        # if lang_elem is None:
        #    self.log(logging.ERROR, u"Could not parse project language.")
        #    return

        # Parse project id (mandatory)
        id_elem = root.find("id")
        if id_elem is None:
            self.log(logging.ERROR, u"Could not parse project id.")
            return

        # Parse project title (mandatory)
        title_elem = root.find("title")
        if title_elem is None:
            self.log(logging.ERROR, u"Could not parse project title.")
            return

        QgsProject.instance().setTitle(title_elem.text)

        # Parse bbox, if it exists (not owc)
        where_elem = root.find("where")
        if where_elem is not None:
            self.loadBBbox(where_elem)

        # OWC (optional) elements
        # Parse abstract (optional)
        abstract_elem = root.find("abstract")

        # Parse update date (updateDate?) (optional)
        update_elem = root.find("update")

        # Parse author (optional)
        author_elem = root.find("author")
        # TODO: parse comma separated list

        # Parse publisher (optional)
        publisher_elem = root.find("publisher")

        # Parse creator (optional)
        creator_elem = root.find("creator")

        # Parse rights (optional)
        rights_elem = root.find("rights")

        # Parse area of interest (optional)
        aio_elem = root.find("areaOfInterest")
        # TODO: parse GM_Envelope

        # Parse time interval of interest (optional)
        time_elem = root.find("timeIntervalOfInterest")

        # Parse keyword (optional)
        keyword_elem = root.find("keyword")

        # Parse context metadata (optional)
        metadata_elem = root.find("contextMetadata")

        entry_elems = root.findall("entry")  # owc:resource?
        if entry_elems is not None:

            entry_elems.reverse()
            # Load every entry
            for entry_elem in entry_elems:
                self.loadOWCLayer(gpkg_path, entry_elem)

    def loadOWCLayer(self, gpkg_path, entry_elem):
        """Parses layer information from an entry, on OWC_context, and uses it to load and style the layer.

        Args:
            gpkg_path: The geopackage path.
            entry_elem: The entry xml node.
        """

        # Id: is it called code?
        id_elem = entry_elem.find("id")
        if id_elem is None:
            self.log(logging.ERROR, u"Could not parse layer uri.")
            return

        # Parse RFC and check if there is a valid schema
        parsed_url = urlparse(id_elem.text)
        if (parsed_url.scheme) is None:
            self.log(logging.ERROR, u"Invalid layer uri.")
            return

        # Mandatory
        title_elem = entry_elem.find("title")
        if title_elem is None:
            self.log(logging.ERROR, u"Could not parse layer title.")
            return

        # TODO: make offering more general, to support other types of data formats (e.g.: wms)
        offering_elem = entry_elem.find("offering")
        if offering_elem is not None:
            # Mandatory
            content_elem = offering_elem.find("content")
            if content_elem is None:
                self.log(logging.ERROR, u"Failed to content '" + name + "' layer!")
                return;
            href = content_elem.get("href")
            name = self.find_between(href, "#table=")
            if name is None:
                self._log(logging.ERROR, u"Could not parse table name.")
                return

            layer = self.loadLayer(gpkg_path, name, title_elem.text)
            if layer is None or not layer.isValid():
                self.log(logging.ERROR, u"Layer '" + name + "' failed to load!")
                return;

            # layer.setShortName(name)

            # Check visibility (mandatory)
            visibility = entry_elem.find("category").get("term")
            if visibility is None:
                self.log(logging.ERROR, u"Failed to read visibility for '" + name + "' layer!")
                return;

            iface.legendInterface().setLayerVisible(layer, visibility.lower() == 'true')

            # Read style (optional)
            style_elem = offering_elem.find("styleSet")
            if style_elem is not None:
                self.loadOWCStyle(style_elem, title_elem.text)

        # Read other OWC (optional) elements ##################

        # Parse abstract (optional)
        abstract_elem = entry_elem.find("abstract")
        if abstract_elem is not None:
            layer.setAbstract(abstract_elem.text)

        # Parse update date (optional): shouldn't this be OWC:updateDate ?
        date_elem = entry_elem.find("updated")

        # Parse author (optional)
        author_elem = entry_elem.find("author")
        if author_elem is not None:
            layer.setAttribution(author_elem.text)

        # Parse publisher (optional)
        publisher_elem = entry_elem.find("publisher")

        # Parse rights (optional)
        rights_elem = entry_elem.find("rights")

        # Parse geospatial extent (optional)
        ext_elem = entry_elem.find("geospatialExtent")
        # TODO: parse GM_envelope

        # Parse temporal extent (optional)
        temp_elem = entry_elem.find("temporalExtent")
        # TODO: parse TM_GeometricPrimitive

        # Parse content description (optional)
        desc_elem = entry_elem.find("contentDescription")

        # Parse preview (optional)
        prev_elem = entry_elem.find("preview")
        # TODO: validate uri

        # Parse content reference (optional)
        ref_elem = entry_elem.find("contentByRef")
        # TODO: validate uri

        # Parse status (optional)
        active_elem = entry_elem.find("active")
        # TODO: validate boolean

        # Parse keyword (optional)
        keyword_elem = entry_elem.find("keyword")
        if keyword_elem is not None:
            keywords = [keyword_elem.text]
            layer.setKeywordList(keywords)

        # Parse minimum scale denominator (optional)
        minScale_elem = entry_elem.find("minScaleDenominator")
        if minScale_elem is not None:
            layer.setMinimumScale(float(minScale_elem.text))

        # Parse maximum scale denominator (optional)
        maxScale_elem = entry_elem.find("maxScaleDenominator")
        if maxScale_elem is not None:
            layer.setMaximumScale(float(maxScale_elem.text))

        # Parse resource metadata (optional)
        metadata_elem = entry_elem.find("resourceMetadata")

        # Parse folder (optional)
        folder_elem = entry_elem.find("folder")

    def loadOWCStyle(self, style_elem, layer_title):
        """Parses and applies style information from a styleSet, on OWC_context.

        Args:
            style_elem: The styleSet xml node.
            layer_title: The title of the layer to which we want to apply the style.
        """

        # Mandatory: given name
        stylename_elem = style_elem.find("name")
        if stylename_elem is None:
            self.log(logging.ERROR, u"Could not parse style name.")
            return

        # parse title (optional)
        title_elem = style_elem.find("title")

        # parse content (mandatory)
        href = style_elem.find("content").get("href")
        pref1 = "#table="
        pref2 = "&name="
        style_table = self.find_between(href, pref1, pref2)

        stylename = self.find_between(href, pref2)
        if stylename is None or stylename != stylename_elem.text:
            self._log(logging.ERROR, u"Could not parse style name.")
            return

        type = style_elem.find("content").get("type")
        if type != "application/sld+xml":
            self._log(logging.ERROR, u"Currently we only support styles in sld/xml format.")
            return

        self.loadStyle(stylename, style_table, layer_title)

    # Load layers from gpkg
    def loadLayer(self, gpkg_path, layername, title):
        """Loads a layer from a geopackage, and it sets its title.

        Args:
            gpkg_path: The gpkg path.
            layername: The layer name, within the geopackage.
            title: The title to be given to the layer.

        Returns:
            An handle to the loaded layer.
        """
        return iface.addVectorLayer(gpkg_path + "|layername=" + layername, title, "ogr")

    def loadStyle(self, style_name, table_name, given_name):
        """Load named style from a table.

        Args:
            style_name: The style name, as it is referenced in the style table.
            table_name: The name of the table where the style is stored (shouldn't it be a convention?).
            given_name: The layer title.
        """
        try:
            self.c.execute("SELECT content FROM owc_style where name like'" + style_name + "'")
        except sqlite3.OperationalError:
            self.log(logging.ERROR, u"Could not find style "
                     + style_name)
            return
        styles = self.c.fetchone()

        if styles is None:
            self.log(logging.ERROR, u"Could not find any styles "
                                    u"named " + style_name)
            return

        style = styles[0]

        layerList = QgsMapLayerRegistry.instance().mapLayersByName(given_name)

        if layerList is None:
            self.log(logging.ERROR, u"We could not find a loaded layer "
                                    "called " + given_name + ". Something is not right!")

        layer = layerList[0]

        f = QTemporaryFile()
        if f.open():
            f.write(style)
            f.close()
            ret = layer.loadSldStyle(f.fileName())
            # TODO: add style to default styles?

            if ret[1] is True:
                self.log(logging.DEBUG, "Style '" + style_name + "' loaded")
            else:
                self.log(logging.ERROR, "Style '" + style_name + "' not loaded: " + ret[0])

            f.remove()

        else:
            self.log(logging.ERROR, u"Although there was a reference to style "
                     + style_name + ", we could not find it in table owc_style. Something is not right!")
            return

    def loadBBbox(self, where_elem):
        """Parses and applies bbox.

        Args:
            where_elem: The where xml node.
        """
        env_elem = where_elem.find("Envelope")
        if env_elem is None:
            self.log(logging.ERROR, u"Could not parse envelope.")
            return

        lower_elem = env_elem.find("lowerCorner")
        if lower_elem is None:
            self.log(logging.ERROR, u"Could not parse lower corner.")
            return
        lc = lower_elem.text.split()
        if (len(lc) != 2):
            self.log(logging.ERROR, u"Wrong number of entries in lower corner.")
            return

        upper_elem = env_elem.find("upperCorner")
        if upper_elem is None:
            self.log(logging.ERROR, u"Could not parse lower corner.")
            return
        uc = upper_elem.text.split()
        if (len(uc) != 2):
            self.log(logging.ERROR, u"Wrong number of entries in upper corner.")
            return

        # TODO: review this implementation
        # str = (self.find_between(context, "<georss:where>", "</georss:where>")).replace('\n', '').encode('ascii',
        #                                                                                                 'ignore')
        # d = QDomDocument()
        # d.setContent("< ?xml version = \"1.0\" encoding = \"utf-8\"? >" + str.)
        # docElem = d.documentElement()
        # extent = QgsOgcUtils.rectangleFromGMLEnvelope(docElem.firstChild())

        # TODO: what happens to srs and dimension?
        extent = QgsRectangle(float(lc[0]), float(lc[1]), float(uc[0]), float(uc[1]))

        iface.mapCanvas().setExtent(extent)
        iface.mapCanvas().refresh()

    def find_between(self, s, first, last=None):
        """Extracts a substring from a string, between one, or two substrings.
        If the last parameter is empty, it will extract everything after the first substring.

        Args:
            s: The string we want to parse.
            first: The first substring.
            last: The last substring (optional).

        Returns:
            The extracted substring.
        """
        try:
            start = s.index(first) + len(first)
            if last is None:
                end = len(s)
            else:
                end = s.index(last, start)

            return s[start:end]

        except ValueError:
            return ""





