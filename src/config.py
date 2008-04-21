#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
"""
This is the configuration module for Mentor.
It manages settings applied by command-line, user settings and system-wide
settings.
It uses PyQt settings module class as a back-end for
managing the settings.

"""
import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from utils import log
import release


__version__ = release.version


class Config(object):
    def __init__(self):
        self._settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'Mentor', 'mentor')

        # const settings - don't change
        self.DB_VERSION             = '01'

        # program command-line parameters
        self.DEBUG                  = False
        self.VERBOSE                = False



    def load(self):
        """Loads user settings from user settings file"""
        self.DEBUG = self._settings.value('debug', QVariant(self.DEBUG)).toBool()
        self.VERBOSE = self._settings.value('verbose', QVariant(self.VERBOSE)).toBool()


    def save(self):
        """Saves user settings to user settings file"""
        self._settings.setValue('debug', QVariant(self.DEBUG))
        self._settings.setValue('verbose', QVariant(self.VERBOSE))



        # override them with user settings
        self._settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'Mentor', 'mentor')



class GuiConfig(Config):
    """This class stores GUI specific settings"""
    def __init__(self):
        Config.__init__(self)

        self.GUI_RECENTFILES_MAX    = 4
        self.GUI_RECENTFILES        = []

        self.GUI_GEOMETRY           = QRect(100, 100, 700, 500)
        self.GUI_MAXIMIZED          = False

        self.GUI_LAZY_SHOW          = False

        self.GUI_FONT               = QFont("Fixed", 8)



    def load(self):
        Config.load(self)
        # load recent files
        self.GUI_RECENTFILES_MAX = self._settings.value('Gui/recent_max', \
                                        QVariant(self.GUI_RECENTFILES_MAX)).toInt()[0]

        list = self._settings.value('Gui/recent', QVariant(self.GUI_RECENTFILES)).toStringList()
        self.GUI_RECENTFILES = [str(fname) for fname in list[:self.GUI_RECENTFILES_MAX]]

        # geometry'
        self.GUI_GEOMETRY = self._settings.value('Gui/geometry', QVariant(self.GUI_GEOMETRY)).toRect()
        self.GUI_MAXIMIZED = self._settings.value('Gui/maximized', QVariant(self.GUI_MAXIMIZED)).toBool()


    def save(self):
        Config.save(self)

        # save recent files
        self._settings.setValue('Gui/recent_max', QVariant(self.GUI_RECENTFILES_MAX))
        self._settings.setValue('Gui/recent', QVariant(self.GUI_RECENTFILES))

        # geometry
        self._settings.setValue('Gui/geometry', QVariant(self.GUI_GEOMETRY))
        self._settings.setValue('Gui/maximized', QVariant(self.GUI_MAXIMIZED))


class ProbeConfig(Config):
    """This class stores Probe specific settings"""
    def __init__(self):
        Config.__init__(self)

        # language corpus settings
        self.LANG_CORPUS_USED       = True
        self.LANG_CORPUS_DB         = 'data/corpus_en.db'
        self.LANG_CORPUS_IGNORE_LVL = 2

    def load(self):
        Config.load(self)

        # lang corpus settings
        self.LANG_CORPUS_USED = self._settings.value('Probe/lang_corpus_used', \
            QVariant(self.LANG_CORPUS_USED)).toBool()
        self.LANG_CORPUS_DB = self._settings.value('Probe/lang_corpus_db', \
            QVariant(self.LANG_CORPUS_DB)).toString()
        self.LANG_CORPUS_IGNORE_LVL = self._settings.value('Probe/lang_corpus_ignore_lvl',
            QVariant(self.LANG_CORPUS_IGNORE_LVL)).toInt()[0]


    def save(self):
        Config.save(self)

        # lang corpus settings
        self._settings.setValue('Probe/lang_corpus_used', \
            QVariant(self.LANG_CORPUS_USED))
        self._settings.setValue('Probe/lang_corpus_db', \
            QVariant(self.LANG_CORPUS_DB))
        self._settings.setValue('Probe/lang_corpus_ignore_lvl', \
            QVariant(self.LANG_CORPUS_IGNORE_LVL))






gui_config = GuiConfig()
probe_config = ProbeConfig()
