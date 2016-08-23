#!/usr/bin/env python

import argparse
import sys
import logging
from qgisgpkg.qgpkg import QGpkg


logger = logging.getLogger('qgpkg')
logger.addHandler(logging.StreamHandler())


def log(lvl, msg, *args, **kwargs):
    logger.log(lvl, msg, *args, **kwargs)


def info(args):
    gpkg = QGpkg(args.gpkg, log)
    gpkg.info()
    return 0


def write(args):
    gpkg = QGpkg(args.gpkg, log)
    gpkg.write(args.qgs)
    return 0


def read(args):
    gpkg = QGpkg(args.gpkg, log)
    gpkg.read(args.gpkg)
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
    parser.add_argument(
        '--debug', default=False, action='store_true',
        help='Display debugging information')

    subparser = subparsers.add_parser(
        'info', help='GeoPackage content information')
    subparser.add_argument('gpkg', **gpkgparam)
    subparser.set_defaults(func=info)

    subparser = subparsers.add_parser(
        'write', help='Save QGIS project in GeoPackage')
    subparser.add_argument('gpkg', **gpkgparam)
    subparser.add_argument('qgs', **qgsparam)
    subparser.set_defaults(func=write)

    subparser = subparsers.add_parser(
        'read', help='Read QGIS project from GeoPackage')
    subparser.add_argument('gpkg', **gpkgparam)
    subparser.set_defaults(func=read)

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
