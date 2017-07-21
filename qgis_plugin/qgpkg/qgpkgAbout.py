# -*- coding: utf-8 -*-

import os

from PyQt4 import QtGui, QtCore
from ui_about_dialog import Ui_qgpkgDlg

class qgpkgAbout(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, None)
        self.setWindowFlags( self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint )

        # Todo: add support for translation
        self._initGui(parent)

    def _initGui(self, parent):
        self.ui = Ui_qgpkgDlg()
        self.ui.setupUi(self)