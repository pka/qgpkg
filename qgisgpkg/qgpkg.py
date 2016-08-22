from __future__ import print_function
import sys
import os
import sqlite3
import tempfile
from xml.etree import ElementTree as ET


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
