#!/usr/bin/env python
# -*- coding: iso-8859-2 -*-
#
# Copyright (C) 2007 Adam Folmert <afolmert@gmail.com>
#
# This file is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
#

"""Here are misc python utilities for PyQt development.

They are collected from different sources and some are written from scratch by
me.
"""


# TODO change import only necessary widgets
import release
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *

__version__ = release.version





#
#----------------------------------------------------------
# Misc routines


def tr(text):
    return qApp.tr(text)



#
#----------------------------------------------------------
# dialog boxes
# shortcut for displaying message box


def msgbox(aMesg, parent = None):
    QMessageBox.information( parent
                            , "Info"
                            , aMesg )


def show_info(message, parent=None):
    class InfoWidget(QDialog):
        def __init__(self, parent=None):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Information')
            self.setGeometry(400, 300, 200, 200)
            self.lbl = QLabel()
            self.btn = QPushButton('OK')
            self.btn.setStyle(Styles.windowsStyle())
            layout = QVBoxLayout()
            layout.addWidget(self.lbl)
            layout.addWidget(self.btn)
            self.setLayout(layout)
            self.connect(self.btn, SIGNAL("clicked()"), SLOT("accept()"))

    widget = InfoWidget(parent)
    widget.lbl.setText(message)
    widget.exec_()

#
#----------------------------------------------------------
# styles classes and routines

class Styles(object):
    """Singleton object for retrieving styles."""

    _windowsStyle   =  None
    _cdeStyle       =  None
    _motifStyle     =  None
    _plastiqueStyle =  None

    @staticmethod
    def windowsStyle():
        if Styles._windowsStyle is None:
            Styles._windowsStyle = QStyleFactory.create('Windows')
        return Styles._windowsStyle

    @staticmethod
    def cdeStyle():
        if Styles._cdeStyle is None:
            Styles._cdeStyle = QStyleFactory.create('Cde')
        return Styles._cdeStyle

    @staticmethod
    def motifStyle():
        if Styles._motifStyle is None:
            Styles._motifStyle = QStyleFactory.create('Motif')
        return Styles._motifStyle

    @staticmethod
    def plastiqueStyle():
        if Styles._plastiqueStyle is None:
            Styles._plastiqueStyle = QStyleFactory.create('Plastique')
        return Styles._plastiqueStyle



#
#----------------------------------------------------------
# border layout




class ItemWrapper(object):
    def __init__(self, i, p):
        self.item = i
        self.position = p


class BorderLayout(QLayout):
    West, North, South, East, Center = range(5)
    MinimumSize, SizeHint = range(2)

    def __init__(self, parent=None, margin=0, spacing=-1):
        QLayout.__init__(self, parent)

        self.setMargin(margin)
        self.setSpacing(spacing)
        self.list = []

    def __del__(self):
        l = self.takeAt(0)
        while l:
            l = self.takeAt(0)

    def addItem(self, item):
        self.add(item, BorderLayout.West)

    def addWidget(self, widget, position):
        self.add(QWidgetItem(widget), position)

    def expandingDirections(self):
        return Qt.Horizontal | Qt.Vertical

    def hasHeightForWidth(self):
        return False

    def count(self):
        return len(self.list)

    def itemAt(self, index):
        if index < len(self.list):
            return self.list[index].item

        return None

    def minimumSize(self):
        return self.calculateSize(BorderLayout.MinimumSize)

    def setGeometry(self, rect):
        center = 0
        eastWidth = 0
        westWidth = 0
        northHeight = 0
        southHeight = 0
        centerHeight = 0

        QLayout.setGeometry(self, rect)

        for wrapper in self.list:
            item = wrapper.item
            position = wrapper.position

            if position == BorderLayout.North:
                item.setGeometry(QRect(rect.x(), northHeight, rect.width(), item.sizeHint().height()))

                northHeight += item.geometry().height() + self.spacing()
            elif position == BorderLayout.South:
                item.setGeometry(QRect(item.geometry().x(), item.geometry().y(), rect.width(), item.sizeHint().height()))

                southHeight += item.geometry().height() + self.spacing()

                item.setGeometry(QRect(rect.x(), rect.y() + rect.height() - southHeight + self.spacing(), item.geometry().width(), item.geometry().height()))
            elif position == BorderLayout.Center:
                center = wrapper

        centerHeight = rect.height() - northHeight - southHeight

        for wrapper in self.list:
            item = wrapper.item
            position = wrapper.position

            if position == BorderLayout.West:
                item.setGeometry(QRect(rect.x() + westWidth, northHeight, item.sizeHint().width(), centerHeight))

                westWidth += item.geometry().width() + self.spacing()
            elif position == BorderLayout.East:
                item.setGeometry(QRect(item.geometry().x(), item.geometry().y(), item.sizeHint().width(), centerHeight))

                eastWidth += item.geometry().width() + self.spacing()

                item.setGeometry(QRect(rect.x() + rect.width() - eastWidth + self.spacing(), northHeight, item.geometry().width(), item.geometry().height()))

        if center:
            center.item.setGeometry(QRect(westWidth, northHeight, rect.width() - eastWidth - westWidth, centerHeight))

    def sizeHint(self):
        return self.calculateSize(BorderLayout.SizeHint)

    def takeAt(self, index):
        if index >= 0 and index < len(self.list):
            layoutStruct = self.list.pop(index)
            return layoutStruct.item

        return None

    def add(self, item, position):
        self.list.append(ItemWrapper(item, position))

    def calculateSize(self, sizeType):
        totalSize = QSize()

        for wrapper in self.list:
            position = wrapper.position
            itemSize = QSize()

            if sizeType == BorderLayout.MinimumSize:
                itemSize = wrapper.item.minimumSize()
            else: # sizeType == BorderLayout.SizeHint
                itemSize = wrapper.item.sizeHint()

            if position == BorderLayout.North or position == BorderLayout.South or position == BorderLayout.Center:
                totalSize.setHeight(totalSize.height() + itemSize.height())

            if position == BorderLayout.West or position == BorderLayout.East or position == BorderLayout.Center:
                totalSize.setWidth(totalSize.width() + itemSize.width())

        return totalSize


def demoBorderLayout():
    class Window(QWidget):
        def __init__(self, parent=None):
                QWidget.__init__(self, parent)

                centralWidget = QTextBrowser()
                centralWidget.setPlainText(self.tr("Central widget"))

                layout = BorderLayout()
                layout.addWidget(centralWidget, BorderLayout.Center)

                # Qt takes ownership of the widgets in the layout when setLayout() is
                # called.  Therefore we keep a local reference to each label to prevent
                # it being garbage collected until the call to setLayout().
                label_n = self.createLabel("North")
                layout.addWidget(label_n, BorderLayout.North)

                label_w = self.createLabel("West")
                layout.addWidget(label_w, BorderLayout.West)

                label_e1 = self.createLabel("East 1")
                layout.addWidget(label_e1, BorderLayout.East)

                label_e2 = self.createLabel("East 2")
                layout.addWidget(label_e2, BorderLayout.East)

                label_s = self.createLabel("South")
                layout.addWidget(label_s, BorderLayout.South)

                self.setLayout(layout)

                self.setWindowTitle(self.tr("Border Layout"))

        def createLabel(self, text):
                label = QLabel(text)
                label.setFrameStyle(QFrame.Box | QFrame.Raised)
                return label


    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())




#
#----------------------------------------------------------
# flow layout




class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        QLayout.__init__(self, parent)

        if parent is not None:
            self.setMargin(margin)
        self.setSpacing(spacing)

        self.itemList = []

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        QLayout.setGeometry(self, rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2 * self.margin(), 2 * self.margin())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            nextX = x + item.sizeHint().width() + self.spacing()
            if nextX - self.spacing() > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + self.spacing()
                nextX = x + item.sizeHint().width() + self.spacing()
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()



def demoFlowLayout():
    class Window(QWidget):
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)

            flowLayout = FlowLayout()
            flowLayout.addWidget(QPushButton(self.tr("Short")))
            flowLayout.addWidget(QPushButton(self.tr("Longer")))
            flowLayout.addWidget(QPushButton(self.tr("Different text")))
            flowLayout.addWidget(QPushButton(self.tr("More text")))
            flowLayout.addWidget(QPushButton(self.tr("Even longer button text")))
            self.setLayout(flowLayout)

            self.setWindowTitle(self.tr("Flow Layout"))


    app = QApplication(sys.argv)
    mainWin = Window()
    mainWin.show()
    sys.exit(app.exec_())




#---------------------------------------------------
# This is hackish workaround for smoother displaying dialog boxes and windows in qt
# Basically it delays showing of a window until it is fully drawn.


class MyDesktopFragment(QWidget):
    """This is widget which displays fragment of desktop screen.

    It can grab the screen contents and then display it on itself. It may be
    useful if we want to simulate buffered dialogs which are initially hidden.
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._label = QLabel(self)
        self._borderWidth = 0
        self._initialPalette = self.palette()
        self._borderPalette = QPalette(QColor(255, 0, 0))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def resizeEvent(self, event):
        b = self._borderWidth
        self._label.setGeometry(b, b, self.width() - b * 2, self.height() - b * 2)


    def setBorderEnabled(self, enabled=True):
        """This enabled or disables widget border for debugging purposes."""
        if enabled:
            self.setAutoFillBackground(True)
            self.setPalette(self._borderPalette)
            self._borderWidth = 1
        else:
            self.setAutoFillBackground(False)
            self.setPalette(self._initialPalette)
            self._borderWidth = 0

    def grabDesktop(self, rect):
        """Grabs desktop fragment which should be displayed."""
        p = QPixmap.grabWindow(QApplication.desktop().winId(), rect.x(), rect.y(), rect.width(), rect.height())
        self._label.setPixmap(p)




class LazyWidget(object):
    """Widget proxy which delays window showing until it is fully initialized."""

    DelayTime = 100

    def __init__(self):
        self._widget = None
        self._savedPos = QPoint(0, 0)
        self._desktopFragment = MyDesktopFragment()

    def setWidget(self, widget):
        self._widget = widget

    def _checkWidget(self):
        assert isinstance(self._widget, QWidget), "Invalid widget set!"

    def show(self):
        self._checkWidget()

        self._desktopFragment.grabDesktop(QRect(1000, 700, 1010, 710))
        self._desktopFragment.setGeometry(QRect(1000, 700, 1010, 710))
        self._desktopFragment.show()

        self._moveOffScreen()
        self._widget.show()

        QTimer.singleShot(LazyWidget.DelayTime, self._moveOnScreen)


    def _moveOffScreen(self):
        """Moves widget off screen, so it can initialize without flicker."""
        self._checkWidget()
        self._savedPos = QPoint(self._widget.x(), self._widget.y())
        self._widget.move(1019, 716)


    def _moveOnScreen(self):
        """Moves widget on screen, after it has initialized."""
        self._checkWidget()

        self._widget.move(self._savedPos.x(), self._savedPos.y())
        self._desktopFragment.hide()


_lazyWidget = None

def lazyshow(widget):
    """Convenience function for showing windows fully initialized."""
    # must initialize here, because QApplication must be constructed first

    # this works only for not maximized windows
    if widget.isMaximized():
        widget.show()
    else:
        global _lazyWidget
        if _lazyWidget is None:
            _lazyWidget = LazyWidget()
        _lazyWidget.setWidget(widget)
        _lazyWidget.show()



