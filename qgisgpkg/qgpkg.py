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

logger = logging.getLogger('qgpkg')


class QGpkg:

    """Read and write QGIS mapping information in a GeoPackage database file"""

    def __init__(self, gpkg, logfunc):
        self._gpkg = gpkg
        self._log = logfunc

    def log(self, lvl, msg, *args, **kwargs):
        self._log(lvl, msg, *args, **kwargs)

    def _connect_read_only(self):
        ''' Connect database with sqlite3 '''
        try:
            conn = sqlite3.connect(self._gpkg)
            # Open in read-only mode needs Python 3.4+
            # conn = sqlite3.connect('file:%s?mode=ro' % self._gpkg, uri=True)
            # Workaround:
            if os.stat(self._gpkg).st_size == 0:
                os.remove(self._gpkg)
                self.log(logging.ERROR,
                         "Couldn't find GeoPackage '%s'" % self._gpkg)
                return None
            conn.row_factory = sqlite3.Row
            return conn.cursor()
        except sqlite3.Error as e:
            self.log(logging.ERROR,
                     "Couldn't connect to GeoPackage: %s" % e.args[0])
        return None

    def info(self):
        ''' Show information about GeoPackage '''
        cur = self._connect_read_only()
        if not cur:
            return
        data_type = None
        try:
            for row in cur.execute('''SELECT * FROM gpkg_contents
                    ORDER BY data_type'''):
                if row['data_type'] != data_type:
                    data_type = row['data_type']
                    print("gpkg_contents %s:" % data_type)
                print(row['table_name'])
        except sqlite3.Error as e:
            self.log(logging.ERROR, "GeoPackage access error: ", e.args[0])

        try:
            rows = list(cur.execute('''SELECT extension_name FROM gpkg_extensions'''))
            if len(rows) > 0:
                print("GPKG extensions:")
                for row in rows:
                    print(row['extension_name'])
        except sqlite3.Error:
            pass

        try:
            rows = list(cur.execute('''SELECT name FROM qgis_projects'''))
            if len(rows) > 0:
                print("QGIS projects:")
                for row in rows:
                    print(row['name'])
        except sqlite3.Error:
            pass

        try:
            rows = list(cur.execute('''SELECT name, type FROM qgis_resources'''))
            if len(rows) > 0:
                print("QGIS recources:")
                for row in rows:
                    print(row['name'] + row['type'])
        except sqlite3.Error:
            pass

    def read_project(self, path):
        ''' Check if it's a file and give ElementTree object back '''
        if not os.path.isfile(path):
            return False

        return ET.parse(path)

    def database_connect(self, path):
        ''' Connect database with sqlite3 '''
        try:
            self.conn = sqlite3.connect(path)
            self.c = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            self.log(logging.ERROR,
                     "Couldn't connect to GeoPackage: %s" % e.args[0])
            return False

    def check_gpkg(self, path):
        ''' Check if file is GeoPackage '''
        try:
            self.c.execute('SELECT * FROM gpkg_contents')
            self.c.fetchone()
            return True
        except:
            return False

    def make_path_absolute(self, path, project_path):
        ''' Make path absolut and handle multiplatform issues '''
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(project_path), path)
        return os.path.normpath(path)

    def write(self, project_path):
        ''' Store QGIS project '''
        xmltree = self.read_project(project_path)
        # If something is messed up with the file, the Method will stop
        if not xmltree:
            self.log(logging.ERROR, u"Couldn't read project (wrong file format)")
            return

        root = xmltree.getroot()
        projectlayers = root.find("projectlayers")

        # Search for layersources
        sources = []
        for layer in projectlayers:
            layer_path = self.make_path_absolute(layer.find(
                "datasource").text.split("|")[0], project_path)
            if layer_path not in sources:
                self.log(logging.DEBUG, u"Found datasource: %s" % layer_path)
                sources.append(layer_path)

        # If there are more than just one different datasource check from where
        # they are from
        gpkg_found = False
        if len(sources) >= 1:
            for path in sources:
                if self.database_connect(path):
                    if self.check_gpkg(path) and not gpkg_found:
                        gpkg_found = True
                        gpkg_path = path
                    elif self.check_gpkg(path) and gpkg_found:
                        # If a project has layer from more than just one
                        #  GeoPackage it can't be written
                        self.log(logging.ERROR, u"The project uses layers "
                            "from different GeoPackage databases.")
                        return
            if gpkg_found and len(sources) > 1:
                self.log(
                    logging.WARNING,
                    u"Some layers aren't in the GeoPackage. It can't be "
                    "garanteed that all layers will be shown properly.")

        if not gpkg_found:
            self.log(logging.ERROR, u"There is no GeoPackage layer "
                "in the project.")
            return

        self.database_connect(gpkg_path)

        # Check for images in the composer of the project
        composer_list = root.findall("Composer")
        images = []
        for composer in composer_list:
            for comp in composer:
                img = self.make_path_absolute(
                    comp.find("ComposerPicture").attrib['file'], project_path)
                if img not in images:
                    self.log(logging.DEBUG, u"Image found: %s" % img)
                    images.append(img)

        # Write data in database
        project_name = os.path.basename(project_path)
        project_xml = ET.tostring(root)
        extensions = (None, None, 'qgis',
                      'http://github.com/pka/qgpkg/blob/master/'
                      'qgis_geopackage_extension.md',
                      'read-write')

        try:
            # If a project is already inserted, overwrite it
            self.c.execute('SELECT name FROM qgis_projects')
            self.c.execute('UPDATE qgis_projects SET name=?, xml=?',
                           (project_name, project_xml))  # DELETE gives locking problems
            self.log(logging.INFO, u"Project overwritten.")
        except sqlite3.OperationalError:
            self.c.execute('CREATE TABLE IF NOT EXISTS qgis_projects (name text, xml text)')
            self.c.execute('INSERT INTO qgis_projects VALUES (?,?)', (project_name, project_xml))

            self.c.execute('CREATE TABLE IF NOT EXISTS gpkg_extensions (table_name TEXT,column_name TEXT,extension_name TEXT NOT NULL,definition TEXT NOT NULL,scope TEXT NOT NULL,CONSTRAINT ge_tce UNIQUE (table_name, column_name, extension_name))')
            self.c.execute(
                'INSERT INTO gpkg_extensions VALUES (?,?,?,?,?)', extensions)

            self.log(logging.DEBUG, u"Project %s saved." % project_name)



        if images:
            # If available, the images will be written in the database
            try:
                self.c.execute('SELECT name FROM qgis_resources')
                # If it's already in there, check for answer for overwriting
                if reply:
                    self.c.execute('DROP TABLE qgis_resources')
                    raise sqlite3.OperationalError
            except sqlite3.OperationalError:
                self.c.execute(
                    """CREATE TABLE IF NOT EXISTS qgis_resources
                     (name text, type text, blob blob)""")
                for image in images:
                    with open(image, 'rb') as input_file:
                        blob = input_file.read()
                        name, type = os.path.splitext(os.path.basename(image))
                        self.conn.execute(
                            """INSERT INTO qgis_resources \
                            VALUES(?, ?, ?)""", (name, type, sqlite3.Binary(blob)))
                        self.log(logging.DEBUG, u"Image %s was saved" % name)
        self.conn.commit()

    #Load layers from gpkg
    def loadLayers(self, gpkg_path):
        return iface.addVectorLayer(gpkg_path, "", "ogr")

    #Load named style from table
    def loadStyle(self, style_name, table_name, given_name):

        try:
            self.c.execute("SELECT content FROM ows_style where name like'" + style_name +"'")
        except sqlite3.OperationalError:
            self.log(logging.ERROR,  u"Could not find style "
                 + style_name )
            return
        styles= self.c.fetchone()

        if styles is None:
            self.log(logging.ERROR,  u"Could not find any styles "
                u"named " + style_name )
            return

        style=styles[0]

        layerList = QgsMapLayerRegistry.instance().mapLayersByName(given_name)

        if layerList is None:
                self.log(logging.ERROR,  u"We could not find a loaded layer "
                    "called " + given_name + ". Something is not right!" )

        layer=layerList[0]

        f=QTemporaryFile()
        if f.open():
            f.write(style)
            f.close()
            ret=layer.loadSldStyle(f.fileName())

            if ret:
                self.log(logging.DEBUG, "Style '" + style_name +"' loaded")
            else:
                self.log(logging.ERROR, "Style not loaded: " + errorMsg)

            f.remove()

        else:
            self.log(logging.ERROR,  u"Although there was a reference to style "
                 + style_name + ", we could not find it in table ows_style. Something is not right!")
            return

    def loadContext(self, context, dictLayers):
        dictProperties=self.parseContext(context)
        if not dictProperties:
            self.log(logging.ERROR, u"Could not parse OWC.")
            return

        if not dictLayers:
            return

        QgsProject.instance().setTitle(dictProperties["title"])

        bbox=dictProperties["bbox"].split()
        extent = QgsRectangle(float(bbox[0]),float(bbox[1]),float(bbox[4]),float(bbox[5]))
        iface.mapCanvas().setExtent( extent )
        iface.mapCanvas().refresh()

        #We only load metadata for layers which are loaded
        for key, value in dictLayers.iteritems():
            lLayerProps=dictProperties["entries"][key]

            layers=QgsMapLayerRegistry.instance().mapLayersByName(value)
            if (len(layers)!=1):
                self.log(logging.ERROR, u"Could not match layer entry for " + key)
                return

            layer=layers[0]
            layer.setTitle(key)
            layer.setShortName(key)
            layer.setAbstract(dictProperties["entries"][key][0])
            layer.setAttribution(dictProperties["entries"][key][1])

            #layer.setScaleBasedVisibility(True)
            layer.setMinimumScale(float(dictProperties["entries"][key][2]))
            layer.setMaximumScale(float(dictProperties["entries"][key][3]))

            layer.setKeywordList(dictProperties["entries"][key][4])

    def parseContext(self, context):
        dictProperties={}

        it = ET.iterparse(StringIO(context))
        for _, el in it:
            if '}' in el.tag:
                el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
        root = it.root

        #Parse project title
        title_elem = root.find("title")
        if title_elem is None:
            self.log(logging.ERROR, u"Could not parse project title.")
            return

        dictProperties["title"]=title_elem.text

        #TODO: maybe if the OWS server is enabled, we can go on and fill the service capabilities values

        #Parse bbox
        where_elem = root.find("where")
        if where_elem is None:
            self.log(logging.ERROR, u"Could not parse project bbox.")
            return

        pos_poly = where_elem.find("Polygon")
        if pos_poly is None:
            self.log(logging.ERROR, u"Could not parse bbox polygon.")
            return

        pos_ext = pos_poly.find("exterior")
        if pos_ext is None:
            self.log(logging.ERROR, u"Could not parse bbox exterior.")
            return

        pos_ring = pos_ext.find("LinearRing")
        if pos_ring is None:
            self.log(logging.ERROR, u"Could not parse bbox Linear Ring.")
            return

        pos_elem = pos_ring.find("posList")
        if pos_elem is None:
            self.log(logging.ERROR, u"Could not parse bbox coordinates.")
            return

        dictProperties["bbox"]=pos_elem.text

        entry_elems = root.findall("entry")
        if entry_elems is None:
            self.log(logging.ERROR, u"Could not parse project layers.")
            return

        dictProperties["entries"]={} # hash to store the layer entries
        for entry_elem in entry_elems:
            lLayerProps=[] #[abstract, author, min_scale, max_scale, term]
            # Read layer title
            title_elem = entry_elem.find("title")
            if title_elem is None:
                self.log(logging.ERROR, u"Could not parse layer title.")
                return

            # Read layer abstract
            abstract_elem = entry_elem.find("abstract")
            if abstract_elem is None:
                self.log(logging.ERROR, u"Could not parse layer abstract.")
                return

            lLayerProps.append(abstract_elem.text)

            # Read layer author
            author_elem = entry_elem.find("author")
            if author_elem is None:
                self.log(logging.ERROR, u"Could not parse layer author.")
                return

            name_elem = author_elem.find("name")
            if name_elem is None:
                self.log(logging.ERROR, u"Could not parse layer author name.")
                return

            lLayerProps.append(name_elem.text)

            # Read min and max scale
            min_elem = entry_elem.find("minScaleDenominator")
            if min_elem is None:
                self.log(logging.ERROR, u"Could not parse min scale denominator.")
                return

            max_elem = entry_elem.find("maxScaleDenominator")
            if max_elem is None:
                self.log(logging.ERROR, u"Could not parse max scale denominator.")
                return

            lLayerProps.append(min_elem.text)
            lLayerProps.append(max_elem.text)

            # Read keyword
            cat_elem = entry_elem.find("category")
            if cat_elem is None:
                self.log(logging.ERROR, u"Could not parse category.")
                return
            term=cat_elem.get("term")
            if term is None:
                self.log(logging.ERROR, u"Could not parse term.")
                return

            self.log(logging.DEBUG, term)
            lLayerProps.append(term)

            dictProperties["entries"][title_elem.text]=lLayerProps

        return dictProperties

    def read(self, gpkg_path):

        iface.newProject(True) # Clear project, before opening

        ''' Read QGIS project from GeoPackage '''
        # Check if it's a GeoPackage Database
        self.database_connect(gpkg_path)
        if not self.check_gpkg(gpkg_path):
            self.log(logging.ERROR, u"No valid GeoPackage selected.")
            return

        try:
            self.c.execute('SELECT table_name FROM gpkg_contents')
        except sqlite3.OperationalError:
            self.log(logging.ERROR,  u"Unable to read table Name.")
            return

        table_names = self.c.fetchall()

        #Load Layers
        layers=self.loadLayers(gpkg_path)

        db_name=QFileInfo(gpkg_path).baseName()

        #Iterate over loaded layers
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        dictLayers={}
        for layer in layers:
            for row in table_names:
                layer_name=row[0]
                if layer.name()==layer_name or layer.name()== db_name + " " + layer_name:
                    self.log(logging.DEBUG,  u"Layer found: " + layer_name + " for " + layer.name())
                    dictLayers[layer_name]=layer.name()

        #Find and apply Styles
        for key, value in dictLayers.iteritems():
            try:
                self.c.execute("SELECT style_name FROM ows_style_reference where table_name like '" + key + "'")
            except sqlite3.OperationalError:
                self.log(logging.ERROR,  u"Could not find style "
                    "for layer " + value )
                return
            styles= self.c.fetchone()

            if styles is None:
                self.log(logging.ERROR,  u"No style found "
                    "for layer " + value )
                return

            style_name = styles[0]
            self.loadStyle(style_name, key, value)

        #Load OWS Context
        try:
            self.c.execute('SELECT content FROM ows_context')
        except sqlite3.OperationalError:
            self.log(logging.ERROR,  u"Unable to read table ows_context.")
            return

        context = self.c.fetchone()

        if context is None:
            self.log(logging.ERROR,  u"No record found on table ows_context!.")
            return

        self.loadContext(context[0],dictLayers)
