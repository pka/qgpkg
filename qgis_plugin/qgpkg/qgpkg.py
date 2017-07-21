from abc import ABCMeta, abstractmethod
import os
import sqlite3
import logging

logger = logging.getLogger('qgpkg')

class QGpkg:
    """Abstract class which suports read/write QGIS mapping information from a GeoPackage database file"""

    __metaclass__ = ABCMeta

    @abstractmethod
    def read(self, gpkg_path): pass
    """Abstract method to read a QGIS project from geopackage.

    Args:
        gpkg_path: The geopackage path on disk.
    """

    @abstractmethod
    def write(self, project_path): pass
    """Abstract method to write a QGIS project into a geopackage.

    Args:
        gpkg_path: The geopackage path on disk.
    """


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