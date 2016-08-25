# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AllInOneGeopackage
                                 A QGIS plugin
 This Plugin writes and reads Project files in Geopackages.
                             -------------------
        begin                : 2016-03-31
        copyright            : (C) 2016 by Cédric Christen
        email                : cch@sourcepole.ch
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load AllInOneGeopackage class from file AllInOneGeopackage.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .all_in_one import AllInOneGeopackage
    return AllInOneGeopackage(iface)
