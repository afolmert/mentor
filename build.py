#!/usr/bin/env python

#
# version.py of releases is embedded somewhere
# it is used
#
# WARNING!
# files from utils/misc must be included in this directory if I want a redistributable
# project
#
#
# This is a general script for building distribution of mentor project
# the following options are available:
# build.py website - builds html pages for output to sourceforge repository
#                    using rest2html (restructuredText)
#                   from website and doc directories
# build.py egg - builds an egg out of python to be installed by setuptools
#
#
# build.py source - builds source distribution Releases/source.zip and Releases/source.tar.gz
#                     for building manually under windows and linux
#                     instructions and prerequisites for building are detailed in INSTALL file
# build.py windows - builds windows binary and nsis/nullsoft installer
#                     only one exe needed
# build.py deb - creates a debian deb file for automatic debian/ubuntu package installation
# build.py rpm  - creates a rpm file for automatic fedora/redhat/opensuse installation
# build.py all - all of the above are built automatically
#
# build.py tests - run all unittests and doctests for source files
#
#

#
# TODO
# add current version number to releases
# TODO
# add NSIS installer

import subprocess
import shutil
import os
from src.utils import save_stamped_buildno


print "Generating new version number..."
save_stamped_buildno()

print "Preparing..."

def removetree(dirname):
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)


removetree("build")
removetree("dist")

print "Building exe file..."
subprocess.call("python.exe setup.py py2exe")

print "Building doc file..."
subprocess.call("c:/Programs/MiKTeX/miktex/bin/latex.exe -output-directory=dist doc/mentor.tex")
subprocess.call("c:/Programs/MiKTeX/miktex/bin/dvipdfm.exe -o dist/mentor.pdf dist/mentor.dvi")
os.remove("dist/mentor.aux")
os.remove("dist/mentor.dvi")
os.remove("dist/mentor.log")



print "Clearing temp files..."
removetree("../../Releases/current/dist")
removetree("build")

print "Moving dist to Releases..."
removetree("../../Releases/current")
shutil.move("dist", "../../Releases/current")


print "Done."


