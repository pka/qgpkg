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
import sqlite3

from qgpkg import QGpkg
from qgpkg_owc import QGpkg_owc
from qgpkg_qgis import QGpkg_qgis

from qgpkgAbout import qgpkgAbout

# Debug code for Pycharm
import sys
sys.path.append('/home/joana/Downloads/pycharm-2017.3/debug-eggs/pycharm-debug.egg')
import pydevd
pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)

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
        self._log = qlog

    def log(self, lvl, msg, *args, **kwargs):
        self._log(lvl, msg, *args, **kwargs)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True,  add_to_toolbar=True, status_tip=None, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        return action

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

        # Create the dialogs (after translation) and keep reference
        self.aboutDlg = qgpkgAbout()

        self.actionWrite = QAction(
            QIcon(":/plugins/QgisGeopackage/write.png"),
            self.tr(u"Write project in GeoPackage"),
            self.iface.mainWindow()
        )
        self.actionWrite.setWhatsThis(self.tr(u"Write project in GeoPackage"))
        self.iface.addPluginToMenu("&Qgis Geopackage", self.actionWrite)
        self.toolbar.addAction(self.actionWrite)
        # self.actionWrite.setEnabled(False)
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


        self.actionAbout = QAction(
            QIcon(":/plugins/QgisGeopackage/about.png"),
            self.tr(u"About"),
            self.iface.mainWindow()
        )
        self.actionAbout.setWhatsThis(self.tr(u"About the Geopackage plugin"))
        self.iface.addPluginToMenu("&Qgis Geopackage", self.actionAbout)
        QObject.connect(self.actionAbout, SIGNAL("triggered()"), self.runAbout)


    def unload(self):
        self.iface.removePluginMenu("&Qgis Geopackage", self.actionWrite)
        self.iface.removePluginMenu("&Qgis Geopackage", self.actionRead)
        self.iface.removeToolBarIcon(self.actionWrite)
        self.iface.removeToolBarIcon(self.actionRead)

    def runAbout(self):
        ' show the dialog'
        self.aboutDlg.show()
        # Run the dialog event loop and See if OK was pressed
        result = self.aboutDlg.exec_()

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

        gpkg = QGpkg_qgis(project_path, qlog)
        gpkg_path = gpkg.write(project_path)

        if tmpfile:
            os.remove(tmpfile)

        if gpkg_path is not None:
            message_bar.pushMessage("Project saved in %s" % gpkg_path)

    def read(self):
        """Reads a geopackage file polymorphically, according to the auto-detected extension """

        gpkg_path = QFileDialog.getOpenFileName(
            self.iface.mainWindow(), self.tr(u"Choose GeoPackage..."),
            None, "GeoPackage (*.gpkg)")
        if gpkg_path:
            gpkg = self.detect_gpkg_extension(gpkg_path, qlog)
            if gpkg is not None:
                project_path = gpkg.read(gpkg_path)
                QgsProject.instance().read(QFileInfo(project_path))
            else:
                self.log(logging.ERROR,
                         u"We were unable to read this geopackage file")
                return

    def detect_gpkg_extension(self, gpkg_path, qlog):
        """Detects which geopackage extension we need to load (if any)
        and instantiates the subclass of qgpkg, according to it.

        Args:
            gpkg_path: The path of the gpkg file.
            qlog: log function
        Returns:
            An handle to the instantiated subclass
        """

        if self.checkIfTableExists("qgis_projects", gpkg_path) is True:
            gpkg = QGpkg_qgis(gpkg_path, qlog)
        elif self.checkIfTableExists("owc_context", gpkg_path) is True:
            gpkg = QGpkg_owc(gpkg_path, qlog)
        else:
            self.log(logging.ERROR,
                     u"Sorry: we did not find a valid geopackage extension whithin this geopackage." +
                     u"\n Supported extensions include owc_geopackage and qgis_geopackage")
            return

        return gpkg

    def checkIfTableExists(self, table_name, gpkg_path):
        """Check if a table with a given name,
        exists in a sqlite3 database

        Args:
            table_name: The table we are looking for.
            gpkg_path: The path of the gpkg file.
        """

        conn = sqlite3.connect(gpkg_path)
        c = conn.cursor()

        try:
            c.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name=?;
            """, (table_name,))
            ret = bool(c.fetchone())
            conn.close()
            return ret

        except sqlite3.OperationalError:
            conn.close()
            self.log(logging.ERROR, u"Table '" + table_name + u"' does not seem to exist in the database.")
