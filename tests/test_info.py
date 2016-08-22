import sys
from qgisgpkg.qgpkg import QGpkg


def test_info():
    gpkg = QGpkg('tests/data/small_world.gpkg')
    gpkg.info()
    output = sys.stdout.getvalue().strip()
    info = """gpkg_contents features:
ne_110m_admin_0_countries
gpkg_contents tiles:
small_world"""
    assert output == info


def test_wrong_file():
    gpkg = QGpkg('wrong_file_name.gpkg')
    gpkg.info()
    output = sys.stdout.getvalue().strip()
    assert output == ""


def test_no_gpkg():
    gpkg = QGpkg("./tests/test_info.py")
    gpkg.info()
    output = sys.stdout.getvalue().strip()
    assert output == ""
