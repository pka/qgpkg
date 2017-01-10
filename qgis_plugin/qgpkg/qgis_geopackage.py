# coding=utf-8
"""
/***************************************************************************
 QgisGeopackage
                                 A QGIS plugin
 This Plugin writes and reads Project files in Geopackages.
                              -------------------
        begin                : 2016-03-31
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Cédric Christen
        email                : cch@sourcepole.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import QgsProject, QgsMessageLog
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import resources
import os
import tempfile
import logging

from qgpkg import QGpkg


message_bar = None

def qlog(lvl, msg, *args, **kwargs):
    msg_level = 2  # TODO:
    # QgsMessageBar.INFO  = 0
    # QgsMessageBar.WARNING   = 1
    # QgsMessageBar.CRITICAL  = 2
    # QgsMessageBar.SUCCESS   = 3
    QgsMessageLog.logMessage(
        msg, 'QGIS Geopackage', msg_level)
    if lvl >= logging.WARNING:
        message_bar.pushMessage(
            msg, level=msg_level)


class QgisGeopackage(QObject):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        global message_bar
        QObject.__init__(self)
        self.iface = iface
        self.toolbar = self.iface.addToolBar(u'Qgis Geopackage')
        self.toolbar.setObjectName(u'Qgis Geopackage')
        message_bar = self.iface.messageBar()

    def initGui(self):
        pluginPath = QFileInfo(os.path.realpath(__file__)).path()
        locale = QSettings().value("locale/userLocale", type=str)[0:2]
        if QFileInfo(pluginPath).exists():
            localePath = pluginPath + "/i18n/qgis_geopackage" + locale + ".qm"
        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actionWrite = QAction(
            QIcon(":/plugins/QgisGeopackage/write.png"),
            self.tr(u"Write project in GeoPackage"),
            self.iface.mainWindow()
        )
        self.actionWrite.setWhatsThis(self.tr(u"Write project in GeoPackage"))
        self.iface.addPluginToMenu("&Qgis Geopackage", self.actionWrite)
        self.toolbar.addAction(self.actionWrite)
        QObject.connect(self.actionWrite, SIGNAL("triggered()"), self.write)

        self.actionRead = QAction(
            QIcon(":/plugins/QgisGeopackage/read.png"),
            self.tr(u"Read project from GeoPackage"),
            self.iface.mainWindow()
        )
        self.actionRead.setWhatsThis(self.tr(u"Read project from GeoPackage"))
        self.iface.addPluginToMenu("&Qgis Geopackage", self.actionRead)
        self.toolbar.addAction(self.actionRead)
        QObject.connect(self.actionRead, SIGNAL("triggered()"), self.read)

    def unload(self):
        self.iface.removePluginMenu("&Qgis Geopackage", self.actionWrite)
        self.iface.removePluginMenu("&Qgis Geopackage", self.actionRead)
        self.iface.removeToolBarIcon(self.actionWrite)
        self.iface.removeToolBarIcon(self.actionRead)

    def write(self):
        project = QgsProject.instance()
        tmpfile = None
        if project.isDirty():
            # If the project is dirty
            # create a temporary file and delete it afterwards
            tmpfile = os.path.join(tempfile.gettempdir(), "qgpkg.qgs")
            file_info = QFileInfo(tmpfile)
            project.write(file_info)
            project_path = project.fileName()
            project.dirty(True)
        else:
            project_path = project.fileName()

        gpkg = QGpkg(project_path, qlog)
        gpkg.write(project_path)

        if tmpfile:
            os.remove(tmpfile)

    def read(self):
        gpkg_path = QFileDialog.getOpenFileName(
            self.iface.mainWindow(), self.tr(u"Choose GeoPackage..."),
            None, "GeoPackage (*.gpkg)")
        if gpkg_path:
            gpkg = QGpkg(gpkg_path, qlog)
            project_path = gpkg.read(gpkg_path)
            #QgsProject.instance().read(QFileInfo(project_path))
