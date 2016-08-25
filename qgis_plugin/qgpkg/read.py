# coding=utf-8

import tempfile
import sqlite3
import os
from qgis.core import *
from qgis.gui import *
from PyQt4.QtCore import *
from xml.etree import ElementTree as ET


class Read(QObject):

    def __init__(self, iface, parent=None):
        ''' Class initialised '''
        QObject.__init__(self)
        self.parent = parent
        self.iface = iface

    def database_connect(self, path):
        ''' Connect database with sqlite3 '''
        try:
            self.conn = sqlite3.connect(path)
            self.c = self.conn.cursor()
            return True
        except:
            return False

    def check_gpkg(self, path):
        ''' Check if the file is a GeoPackage '''
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

    def run(self, gpkg_path):
        ''' Main Method '''
        # Check if it's a GeoPackage Database
        self.database_connect(gpkg_path)
        if not self.check_gpkg(gpkg_path):
            QgsMessageLog.logMessage(self.tr(
                u"No GeoPackage selected."),
                'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", self.tr(
                u"Please choose a GeoPackage."), level=QgsMessageBar.CRITICAL)
            return

        # Read xml from the project in the Database
        try:
            self.c.execute('SELECT name, xml FROM _qgis')
        except sqlite3.OperationalError:
            QgsMessageLog.logMessage(self.tr(
                u"There is no Project file in the database."),
                'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", self.tr(
                u"There is no Project file in the database."),
                level=QgsMessageBar.CRITICAL)
            return
        file_name, xml = self.c.fetchone()
        try:
            xml_tree = ET.ElementTree()
            root = ET.fromstring(xml)
        except:
            QgsMessageLog.logMessage(self.tr(
                u"The xml code is corrupted."),
                'All-In-One Geopackage', QgsMessageLog.CRITICAL)
            self.iface.messageBar().pushMessage("Error", self.tr(
                u"The xml code is corrupted, please check the database."),
                level=QgsMessageBar.CRITICAL)
            return
        QgsMessageLog.logMessage(
            self.tr(u"Xml successfully read."),
            'All-In-One Geopackage', QgsMessageLog.INFO)
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
                QgsMessageLog.logMessage(self.tr(
                    u"Layerpath from layer ") + layer.find("layername").text +
                    self.tr(u" was adjusted."),
                    'All-In-One Geopackage', QgsMessageLog.INFO)

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
                QgsMessageLog.logMessage(self.tr(
                    u"External image ") + os.path.basename(img) +
                    self.tr(u" found."),
                    'All-In-One Geopackage', QgsMessageLog.INFO)
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
                QgsMessageLog.logMessage(self.tr(
                    u"Image saved: ") + img_name,
                    'All-In-One Geopackage', QgsMessageLog.INFO)

        # Project is saved and started
        xml_tree.write(project_path)
        QgsProject.instance().read(QFileInfo(project_path))
        QgsMessageLog.logMessage(
            self.tr(u"Project started."),
            'All-In-One Geopackage', QgsMessageLog.INFO)
