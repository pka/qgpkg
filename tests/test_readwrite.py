import sys
import tempfile
import shutil
import os
from qgisgpkg.qgpkg import QGpkg
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
