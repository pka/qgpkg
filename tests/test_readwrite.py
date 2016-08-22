import sys
import tempfile
import shutil
import os
from qgisgpkg.qgpkg import QGpkg


def test_read_without_qgs():
    gpkg = QGpkg('tests/data/small_world.gpkg')
    gpkg.read('tests/data/small_world.gpkg')
    gpkg.info()
    output = sys.stdout.getvalue().strip()
    info = """gpkg_contents features:
ne_110m_admin_0_countries
gpkg_contents tiles:
small_world"""
    assert output == info


def copy_to_tmp(gpkg, qgs):
    tmp_folder = tempfile.mkdtemp()
    shutil.copy(gpkg, tmp_folder)
    shutil.copy(qgs, tmp_folder)
    return (os.path.join(tmp_folder, os.path.basename(gpkg)),
            os.path.join(tmp_folder, os.path.basename(qgs)))


def test_write():
    # Copy test data
    gpkg_path, qgs_path = copy_to_tmp('tests/data/small_world.gpkg',
                                      'tests/data/small_world.qgs')
    gpkg = QGpkg(gpkg_path)
    gpkg.write(qgs_path)
    gpkg.info()
    output = sys.stdout.getvalue().strip()
    info = """gpkg_contents features:
ne_110m_admin_0_countries
gpkg_contents tiles:
small_world
QGIS projects:
small_world.qgs"""
    assert output == info
