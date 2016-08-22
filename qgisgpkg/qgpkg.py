from __future__ import print_function
import sys
import os
import sqlite3
import tempfile
from xml.etree import ElementTree as ET

from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class QGpkg:

    """Load models of Interlis transfer files"""

    def __init__(self, gpkg):
        self._gpkg = gpkg

    def _connect_read_only(self):
        ''' Connect database with sqlite3 '''
        try:
            conn = sqlite3.connect(self._gpkg)
            # Open in read-only mode needs Python 3.4+
            # conn = sqlite3.connect('file:%s?mode=ro' % self._gpkg, uri=True)
            # Workaround:
            if os.stat(self._gpkg).st_size == 0:
                os.remove(self._gpkg)
                eprint("Couldn't find GeoPackage '%s'" % self._gpkg)
                return None
            conn.row_factory = sqlite3.Row
            return conn.cursor()
        except sqlite3.Error as e:
            eprint("Couldn't connect to GeoPackage: ", e.args[0])
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
            eprint("GeoPackage access error: ", e.args[0])

    def tr(self, sourceText, disambiguation=None, n=-1):
        qobj = QObject()
        return qobj.tr(sourceText, disambiguation, n)

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
        except:
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
            QgsMessageLog.logMessage(self.tr(u"Corrupted project"), 'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            # self.iface.messageBar().pushMessage("Error", self.tr(u"There are problems with the project file, please check if everything is working."), level=QgsMessageBar.CRITICAL)
            return

        QgsMessageLog.logMessage(self.tr(u"Xml successfully read"), 'All-In-One Geopackage', QgsMessageLog.INFO)
        root = xmltree.getroot()
        projectlayers = root.find("projectlayers")

        # Search for layersources
        sources = []
        for layer in projectlayers:
            layer_path = self.make_path_absolute(layer.find("datasource").text.split("|")[0], project_path)
            if layer_path not in sources:
                QgsMessageLog.logMessage(self.tr(u"Found datasource: ") + layer_path, 'All-In-One Geopackage', QgsMessageLog.INFO)
                sources.append(layer_path)

        # If there are more than just one different datasource check from where they are from
        try:
            if len(sources) >= 1:
                gpkg_found = False
                for path in sources:
                    if self.database_connect(path):
                        if self.check_gpkg(path) and not gpkg_found:
                            gpkg_found = True
                            gpkg_path = path
                        elif self.check_gpkg(path) and gpkg_found:
                            # If a project has layer from more than just one GeoPackage
                            # it can't be written
                            QgsMessageLog.logMessage(self.tr(u"The project uses layers from different GeoPackage databases."), 'All-In-One Geopackage', QgsMessageLog.CRITICAL)
                            # self.iface.messageBar().pushMessage("Error", self.tr(u"The project uses layers from different GeoPackage databases."), level=QgsMessageBar.CRITICAL)
                            return
                if gpkg_found and len(sources) > 1:
                    QgsMessageLog.logMessage(self.tr(u"Some layers aren't in the GeoPackage. It can't be garanteed that all layers will be shown properly."), 'All-In-One Geopackage', QgsMessageLog.WARNING)
                    # self.iface.messageBar().pushMessage(self.tr(u"Warning"), self.tr(u"Some layers aren't in the GeoPackage. It can't be garanteed that all layers will be shown properly."), level=QgsMessageBar.WARNING)
                elif not gpkg_found:
                    raise
            else:
                raise
        except:
            QgsMessageLog.logMessage(self.tr(u"There is no GeoPackage layer in the project."), 'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            # self.iface.messageBar().pushMessage("Error", self.tr(u"There is no GeoPackage layer in the project."), level=QgsMessageBar.CRITICAL)
            return

        self.database_connect(gpkg_path)

        # Check for images in the composer of the project
        composer_list = root.findall("Composer")
        images = []
        for composer in composer_list:
            for comp in composer:
                img = self.make_path_absolute(comp.find("ComposerPicture").attrib['file'], project_path)
                if img not in images:
                    QgsMessageLog.logMessage(self.tr(u"Image found: ") + img, 'All-In-One Geopackage', QgsMessageLog.INFO)
                    images.append(img)

        # Write data in database
        inserts = (os.path.basename(project_path), ET.tostring(root))
        extensions = (None, None, 'all_in_one_geopackage', 'Insert and read a QGIS Project file into the GeoPackage database.', 'read-write')

        try:
            # If a project is already inserted, ask if the user wants to overwrite it
            self.c.execute('SELECT name FROM _qgis')
            reply = QMessageBox.question(self.parent, self.tr(u"Warning"), self.tr(u"There is already a project in the GeoPackage, \nDo you want to overwrite it?"), QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
            if reply:
                self.c.execute('UPDATE _qgis SET name=?, xml=?', inserts)
                QgsMessageLog.logMessage(self.tr(u"Project overwritten."), 'All-In-One Geopackage', QgsMessageLog.INFO)
            else:
                QgsMessageLog.logMessage(self.tr(u"Aborted."), 'All-In-One Geopackage', QgsMessageLog.INFO)
        except sqlite3.OperationalError:
            self.c.execute('CREATE TABLE _qgis (name text, xml text)')
            self.c.execute('INSERT INTO _qgis VALUES (?,?)', inserts)
            self.c.execute('INSERT INTO gpkg_extensions VALUES (?,?,?,?,?)', extensions)
            QgsMessageLog.logMessage(self.tr(u"Project ") + inserts[0] + self.tr(u" was saved."), 'All-In-One Geopackage', QgsMessageLog.INFO)

        if images:
            # If available, the images will be written in the database
            try:
                self.c.execute('SELECT name FROM _img_project')
                # If it's already in there, check for answer for overwriting
                if reply:
                    self.c.execute('DROP TABLE _img_project')
                    raise sqlite3.OperationalError
            except sqlite3.OperationalError:
                self.c.execute('CREATE TABLE _img_project (name text, type text, blob blob)')
                for image in images:
                    with open(image, 'rb') as input_file:
                        blob = input_file.read()
                        name, type = os.path.splitext(os.path.basename(image))
                        inserts = (name, type, sqlite3.Binary(blob))
                        self.conn.execute('INSERT INTO _img_project VALUES(?, ?, ?)', inserts)
                        QgsMessageLog.logMessage(self.tr(u"Image ") + name + self.tr(u" was saved"), 'All-In-One Geopackage', QgsMessageLog.INFO)
        self.conn.commit()

    def read(self, gpkg_path):
        ''' Read QGIS project from GeoPackage '''
        # Check if it's a GeoPackage Database
        self.database_connect(gpkg_path)
        if not self.check_gpkg(gpkg_path):
            QgsMessageLog.logMessage(self.tr(u"No GeoPackage selected."), 'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            # self.iface.messageBar().pushMessage("Error", self.tr(u"Please choose a GeoPackage."), level=QgsMessageBar.CRITICAL)
            return

        # Read xml from the project in the Database
        try:
            self.c.execute('SELECT name, xml FROM _qgis')
        except sqlite3.OperationalError:
            QgsMessageLog.logMessage(self.tr(u"There is no Project file in the database."), 'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            # self.iface.messageBar().pushMessage("Error", self.tr(u"There is no Project file in the database."), level=QgsMessageBar.CRITICAL)
            return
        file_name, xml = self.c.fetchone()
        try:
            xml_tree = ET.ElementTree()
            root = ET.fromstring(xml)
        except:
            QgsMessageLog.logMessage(self.tr(u"The xml code is corrupted."), 'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            # self.iface.messageBar().pushMessage("Error", self.tr(u"The xml code is corrupted, please check the database."), level=QgsMessageBar.CRITICAL)
            return
        QgsMessageLog.logMessage(self.tr(u"Xml successfully read."), 'All-In-One Geopackage', QgsMessageLog.INFO)
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
                QgsMessageLog.logMessage(self.tr(u"Layerpath from layer ") + layer.find("layername").text + self.tr(u" was adjusted."), 'All-In-One Geopackage', QgsMessageLog.INFO)

        # Check if an image is available
        composer_list = root.findall("Composer")
        images = []
        for composer in composer_list:
            for comp in composer:
                composer_picture = comp.find("ComposerPicture")
                img = self.make_path_absolute(composer_picture.attrib['file'], project_path)
                # If yes, the path will be adjusted
                composer_picture.set('file', './' + os.path.basename(img))
                QgsMessageLog.logMessage(self.tr(u"External image ") + os.path.basename(img) + self.tr(u" found."), 'All-In-One Geopackage', QgsMessageLog.INFO)
                images.append(img)

        # and the image will be saved in the same folder as the project
        if images:
            self.c.execute("SELECT name, type, blob FROM _img_project")
            images = self.c.fetchall()
            for img in images:
                name, type, blob = img
                img_name = name + type
                img_path = os.path.join(tmp_folder, img_name)
                with open(img_path, 'wb') as file:
                    file.write(blob)
                QgsMessageLog.logMessage(self.tr(u"Image saved: ") + img_name, 'All-In-One Geopackage', QgsMessageLog.INFO)

        # Project is saved and started
        xml_tree.write(project_path)
        QgsProject.instance().read(QFileInfo(project_path))
        QgsMessageLog.logMessage(self.tr(u"Project started."), 'All-In-One Geopackage', QgsMessageLog.INFO)
