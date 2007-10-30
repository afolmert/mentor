#!/bin/env python
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
from utils import log
import release


__version__ = release.version

# TODO
# reading settings from user files
# user-files and system wide files

# TODO
# split to gui and probe settings files ?
#

class Config(object):
    def __init__(self):
        # const settings - don't change
        self.DB_VERSION             = '01'

        # program command-line parameters
        self.DEBUG                  = False
        self.VERBOSE                = False
        self.PRETEND                = False
        self.TEST                   = False

        # language corpus settings
        self.LANG_CORPUS_USED       = 1
        self.LANG_CORPUS_DB         = 'd:/Projects/Mentor/Sources/draft/tools/freq/corpus_en.db'
        self.LANG_CORPUS_IGNORE_LVL = 2

        # window position and sizes
        #self.GUI_POSITION
        #self.GUI_SIZES
        #self.GUI_LAYOUT             = QGuiLayout()

        self.GUI_RECENTFILES_MAX    = 4
        self.GUI_RECENTFILES        = []

        # override them with user settings
        self._settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'Mentor', 'mentor')

        self._load_user_settings()


    def save(self):
        self._save_user_settings()


    def _load_user_settings(self):
        """Loads user settings from user settings file"""

        # load recent files
        self.GUI_RECENTFILES_MAX = self._settings.value('Gui/recent_max', \
                                        QVariant(self.GUI_RECENTFILES_MAX)).toInt()[0]

        list = self._settings.value('Gui/recent', QVariant(self.GUI_RECENTFILES)).toStringList()
        self.GUI_RECENTFILES = [str(fname) for fname in list[:self.GUI_RECENTFILES_MAX]]


    def _save_user_settings(self):
        """Saves user settings to user settings file"""

        # save recent files
        self._settings.setValue('Gui/recent_max', QVariant(self.GUI_RECENTFILES_MAX))
        self._settings.setValue('Gui/recent', QVariant(self.GUI_RECENTFILES))


    # recent file routines
    # TODO is it the right way for these functions?
    def get_most_recent_file(self):
        """Returns most recently used file if valid."""
        if len(self.GUI_RECENTFILES) > 0 and os.path.isfile(self.GUI_RECENTFILES[0]):
            return self.GUI_RECENTFILES[0]
        else:
            return None

    def remove_recent_file(self, fname):
        """Removes given fname from recent files list"""
        try:
            self.GUI_RECENTFILES.remove(fname)
        except:
            pass

    def add_most_recent_file(self, fname):
        """Adds fname to most recently used files"""
        # remove file if already on the list
        try:
            self.GUI_RECENTFILES.remove(fname)
        except:
            pass
        # put it in front of all
        self.GUI_RECENTFILES.insert(0, fname)


config = Config()
