from nose.tools import assert_equals
import sys
import tempfile
import shutil
import os
from qgisgpkg.qgpkg import QGpkg
import sqlite3
from . import nolog


def test_read_without_qgs():
    gpkg = QGpkg('tests/data/small_world.gpkg', nolog)
    gpkg.read('tests/data/small_world.gpkg')
    gpkg.info()
    output = sys.stdout.getvalue().strip()
    info = """gpkg_contents features:
ne_110m_admin_0_countries
gpkg_contents tiles:
small_world
GPKG extensions:
gpkg_rtree_index"""
    assert output == info


def copy_to_tmp(srcdir):
    tmp_folder = tempfile.mkdtemp()
    for fn in os.listdir(srcdir):
        shutil.copy(os.path.join(srcdir, fn), tmp_folder)
    return tmp_folder


def test_write():
    # Copy test data
    tmp_folder = copy_to_tmp('tests/data')
    gpkg_path = os.path.join(tmp_folder, 'small_world.gpkg')
    qgs_path = os.path.join(tmp_folder, 'small_world.qgs')
    gpkg = QGpkg(gpkg_path, nolog)
    gpkg.write(qgs_path)
    gpkg.info()
    output = sys.stdout.getvalue().strip()
    info = """gpkg_contents features:
ne_110m_admin_0_countries
gpkg_contents tiles:
small_world
GPKG extensions:
qgis
gpkg_rtree_index
QGIS projects:
small_world.qgs
QGIS recources:
qgis.png"""
    assert output == info

    conn = sqlite3.connect(gpkg_path)
    curs = conn.cursor()

    curs.execute('SELECT name FROM qgis_projects')
    assert_equals('small_world.qgs', curs.fetchone()[0], 'small_world.qgs not found')

    curs.execute('SELECT name FROM qgis_resources')
    assert_equals('qgis', curs.fetchone()[0], 'Image not found')

    curs.execute("SELECT scope FROM gpkg_extensions WHERE extension_name = 'qgis'")
    assert_equals('read-write', curs.fetchone()[0], 'Extension registration missing')
