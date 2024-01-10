"""
********************************************************************************
compas_model
********************************************************************************

.. currentmodule:: compas_model

.. toctree::
    :maxdepth: 1

    compas_model.elements
    compas_model.model

"""

from __future__ import print_function

import os


__author__ = ["petras vestartas"]
__copyright__ = "Block Research Group - ETH Zurich"
__license__ = "MIT License"
__email__ = "petrasvestartas@gmail.com"
__version__ = "0.1.0"

HERE = os.path.dirname(__file__)

HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))

__all_plugins__ = []

__all__ = ["HOME", "DATA", "DOCS", "TEMP"]
