# coding=latin-1

import unittest
import sqlite3


class TestGeoPackage(unittest.TestCase):

    def setUp(self):
        ''' Verbindung zur Datenbank wird hergestellt '''
        self.conn = sqlite3.connect('natural_earth.gpkg')
        self.c = self.conn.cursor()

    def test_project(self):
        ''' Es wird überprüft ob das Projekt eingelesen wurde '''
        self.c.execute('SELECT name FROM _qgis')
        self.assertEqual('test_countries.qgs', self.c.fetchone()[0], 'Projekt nicht gefunden')

    def test_image(self):
        ''' Es wird überprüft ob die Bilder eingelesen sind '''
        self.c.execute('SELECT name FROM _img_project')
        self.assertEqual('QGis_Logo', self.c.fetchone()[0], 'Bilder nicht gefunden')

    def test_extension(self):
        ''' Es wird überprüft ob die Erweiterung ordnungsgemäss registriert wurde '''
        self.c.execute("SELECT scope FROM gpkg_extensions WHERE extension_name = 'all_in_one_geopackage'")
        self.assertEqual('read-write', self.c.fetchone()[0], 'Erweiterung nicht angegeben')
