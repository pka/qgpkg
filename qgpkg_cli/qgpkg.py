#!/usr/bin/env python

import argparse
import sys
from qgisgpkg.qgpkg import QGpkg


def info(args):
    gpkg = QGpkg(args.gpkg)
    gpkg.info()
    return 0


def write(args):
    return 0


def read(args):
    return 0


def main():
    """Returns 0 on success, 1 on error, for sys.exit."""

    parser = argparse.ArgumentParser(
        description="Store QGIS map information in GeoPackages")

    # Commands
    subparsers = parser.add_subparsers(title='commands',
                                       description='valid commands')
    # Common parameters
    gpkgparam = {
        'help': "input datagpkg"
    }
    qgsparam = {
        'nargs': '?',
        'help': "output datagpkg",
        'default': sys.stdout
    }

    subparser = subparsers.add_parser(
        'info', help='GeoPackage content information')
    subparser.add_argument('gpkg', **gpkgparam)
    subparser.set_defaults(func=info)

    subparser = subparsers.add_parser(
        'write', help='Save QGIS project in GeoPackage')
    subparser.add_argument('gpkg', **gpkgparam)
    subparser.add_argument('qgs', **qgsparam)
    subparser.add_argument(
        '--debug', default=False, action='store_true',
        help='Display debugging information')
    subparser.set_defaults(func=write)

    subparser = subparsers.add_parser(
        'read', help='Read QGIS project from GeoPackage')
    subparser.add_argument('gpkg', **gpkgparam)
    subparser.add_argument('qgs', **qgsparam)
    subparser.add_argument(
        '--debug', default=False, action='store_true',
        help='Display debugging information')
    subparser.set_defaults(func=read)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
