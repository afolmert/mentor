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
"""Release data for the Mentor project.

It is included in other project files to embed vital information about current
release.
"""

from utils import load_stamped_buildno

# Name of the package for release purposes.  This is the name which labels
# the tarballs and RPMs made by distutils, so it's best to lowercase it.
name = 'mentor'

# Version number is built like this: major.minor.revision build: buildno
# Major version happen on big feature introductions and major rewrites
# Minor version include new features
# Revision are usually bugfix releases
#
# Build number is created as yyyymmdd plus six digits of SHA1 of the git head
# It is embedded in the build_stamp.py file and regenerated every time by the
# build.py script
# The build_stamp file is not included in the git repository because it gets
# modified frequently

__major    = '0'
__minor    = '1'
__revision = '0'
__buildno  = load_stamped_buildno()
version    = '%s.%s.%s build: %s' % (__major, __minor, __revision, __buildno)


# more detailed description
description = "An enhanced interactive Python shell."

long_description = \
"""
Mentor is a flashcard program for improving the learning process.

Main features:

 * User-friendly GUI for managing flashcards and performing repetitions

 * Advanced repetition scheduling algorithm

 * Probe markup language for extracting knowledge from articles

 * A set of ready-made flashcard databases on different subjects


 The latest development version is always available at the Mentor git
 repository_.

.. _repository: http://repo.or.cz/r/mentor.git
 """

license = 'GNU GPL 2.0 or later'

authors = {'afolmert' : ('Adam Folmert','afolmert@gmail.com'),
           }

url = 'http://code.google.com/p/mentor'

download_url = 'http://code.google.com/p/mentor'

platforms = ['Linux','Mac OSX','Windows XP/2000/NT','Windows 95/98/ME']

keywords = ['learning','flashcard','repetitions', 'knowledge']


