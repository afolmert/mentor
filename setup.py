#!/bin/env python
from distutils.core import setup
import sys
import py2exe

# hack to import from src
# TODO see how other do it
sys.path.append("src")


setup(version="0.0.1"
      , description="Flash-card application"
      , name="Mentor"
      , windows=["src/mentor.py"]
      , console=["src/probe.py"]
      , zipfile = "lib/shared.zip"
      , options={"py2exe":{"includes":["sip"], "compressed": 1, "bundle_files": 1}}
      )

