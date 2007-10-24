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
import release

__version__ = release.version

# TODO
# reading settings from user files
# user-files and system wide files

class Config(object):
    def __init__(self):
        # program running settings
        self.DEBUG                  = False
        self.VERBOSE                = False
        self.PRETEND                = False
        self.TEST                   = False
        # language corpus settings
        self.LANG_CORPUS_USED       = 1
        self.LANG_CORPUS_DB         = 'd:/Projects/Mentor/Sources/draft/tools/freq/corpus_en.db'
        self.LANG_CORPUS_IGNORE_LVL = 2
        # database version
        self.DB_VERSION             = '01'



config = Config()
