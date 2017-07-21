from __future__ import print_function
import sys
import os
import sqlite3
import tempfile
import logging
from qgis.core import QgsProject
from PyQt4.QtCore import QFileInfo

from xml.etree import ElementTree as ET

from qgpkg import QGpkg

logger = logging.getLogger('qgpkg_qgis')

# Debug code for Pycharm: remove as you please
sys.path.append('/home/joana/Downloads/pycharm-2016.3.3/debug-eggs/pycharm-debug.egg')
#import pydevd

#pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)

class QGpkg_qgis(QGpkg):
    """Read and write QGIS mapping information in a GeoPackage database file, using this spec:
    https://github.com/pka/qgpkg/blob/master/qgis_geopackage_extension.md
    """

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
            self.c.execute('CREATE TABLE IF NOT EXISTS qgis_projects (name TEXT, xml TEXT)')
            self.c.execute('INSERT INTO qgis_projects VALUES (?,?)', (project_name, project_xml))

            self.c.execute(
                'CREATE TABLE IF NOT EXISTS gpkg_extensions (table_name TEXT,column_name TEXT,extension_name TEXT NOT NULL,definition TEXT NOT NULL,scope TEXT NOT NULL,CONSTRAINT ge_tce UNIQUE (table_name, column_name, extension_name))')
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
                     (name TEXT, type TEXT, blob BLOB)""")
                for image in images:
                    with open(image, 'rb') as input_file:
                        blob = input_file.read()
                        name, type = os.path.splitext(os.path.basename(image))
                        self.conn.execute(
                            """INSERT INTO qgis_resources \
                            VALUES(?, ?, ?)""", (name, type, sqlite3.Binary(blob)))
                        self.log(logging.DEBUG, u"Image %s was saved" % name)
        self.conn.commit()

    def read(self, gpkg_path):
        ''' Read QGIS project from GeoPackage '''
        # Check if it's a GeoPackage Database
        self.database_connect(gpkg_path)
        if not self.check_gpkg(gpkg_path):
            self.log(logging.ERROR, u"No valid GeoPackage selected.")
            return

        # Read xml from the project in the Database
        try:
            self.c.execute('SELECT name, xml FROM qgis_projects')
        except sqlite3.OperationalError:
            self.log(logging.ERROR, u"There is no Project file "
                                    "in the database.")
            return
        file_name, xml = self.c.fetchone()
        try:
            xml_tree = ET.ElementTree()
            root = ET.fromstring(xml)
        except:
            self.log(logging.ERROR, u"The xml code is corrupted.")
            return
        self.log(logging.DEBUG, u"Xml successfully read.")
        xml_tree._setroot(root)
        projectlayers = root.find("projectlayers")

        # Layerpath in xml adjusted
        tmp_folder = tempfile.mkdtemp()
        project_path = os.path.join(tmp_folder, file_name)
        for layer in projectlayers:
            layer_element = layer.find("datasource")
            layer_info = layer_element.text.split("|")
            layer_path = self.make_path_absolute(gpkg_path, layer_info[0])
            if layer_path.endswith('.gpkg'):
                if len(layer_info) >= 2:
                    for i in range(len(layer_info)):
                        if i == 0:
                            layer_element.text = layer_path
                        else:
                            layer_element.text += "|" + layer_info[i]
                elif len(layer_info) == 1:
                    layer_element.text = layer_path
                self.log(logging.DEBUG,
                         u"Layerpath from layer %s was adjusted." %
                         layer.find("layername").text)

        # Check if an image is available
        composer_list = root.findall("Composer")
        images = []
        for composer in composer_list:
            for comp in composer:
                composer_picture = comp.find("ComposerPicture")
                img = self.make_path_absolute(
                    composer_picture.attrib['file'], project_path)
                # If yes, the path will be adjusted
                composer_picture.set('file', './' + os.path.basename(img))
                self.log(logging.DEBUG,
                         u"External image %s found." % os.path.basename(img))
                images.append(img)

        # and the image will be saved in the same folder as the project
        if images:
            self.c.execute("SELECT name, type, blob FROM qgis_resources")
            images = self.c.fetchall()
            for img in images:
                name, type, blob = img
                img_name = name + type
                img_path = os.path.join(tmp_folder, img_name)
                with open(img_path, 'wb') as file:
                    file.write(blob)
                self.log(logging.DEBUG, u"Image saved: %s" % img_name)

        # Project is saved and started
        xml_tree.write(project_path)
        self.log(logging.DEBUG, u"Temporary project written.")
        #return project_path
        QgsProject.instance().read(QFileInfo(project_path))

    def read_project(self, path):
        ''' Check if it's a file and give ElementTree object back '''
        if not os.path.isfile(path):
            return False

        return ET.parse(path)