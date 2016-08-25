# coding=utf-8

from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import tempfile
import os
import sqlite3
from xml.etree import ElementTree as ET


class Write(QObject):
    def __init__(self, iface, parent=None):
        ''' Class initialised '''
        QObject.__init__(self)
        self.parent = parent
        self.iface = iface

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

    def run(self):
        ''' Main Method '''
        project = QgsProject.instance()
        if project.isDirty():
            # If the project is dirty
            # create a temporary file and delete it afterwards
            tmpfile = os.path.join(tempfile.gettempdir(), "temp_project.qgs")
            file_info = QFileInfo(tmpfile)
            project.write(file_info)
            project_path = project.fileName()
            xmltree = self.read_project(project_path)
            os.remove(project.fileName())
            project.dirty(True)
        else:
            # Or else the file itself will be used
            project_path = project.fileName()
            xmltree = self.read_project(project_path)
            project.dirty(False)

        # If something is messed up with the file, the Method will stop
        if not xmltree:
            QgsMessageLog.logMessage(self.tr(u"Corrupted project"), 'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", self.tr(u"There are problems with the project file, please check if everything is working."), level=QgsMessageBar.CRITICAL)
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
                            self.iface.messageBar().pushMessage("Error", self.tr(u"The project uses layers from different GeoPackage databases."), level=QgsMessageBar.CRITICAL)
                            return
                if gpkg_found and len(sources) > 1:
                    QgsMessageLog.logMessage(self.tr(u"Some layers aren't in the GeoPackage. It can't be garanteed that all layers will be shown properly."), 'All-In-One Geopackage', QgsMessageLog.WARNING)
                    self.iface.messageBar().pushMessage(self.tr(u"Warning"), self.tr(u"Some layers aren't in the GeoPackage. It can't be garanteed that all layers will be shown properly."), level=QgsMessageBar.WARNING)
                elif not gpkg_found:
                    raise
            else:
                raise
        except:
            QgsMessageLog.logMessage(self.tr(u"There is no GeoPackage layer in the project."), 'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", self.tr(u"There is no GeoPackage layer in the project."), level=QgsMessageBar.CRITICAL)
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
        inserts = (os.path.basename(project.fileName()), ET.tostring(root))
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
