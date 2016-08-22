import sys
from qgisgpkg.qgpkg import QGpkg


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
