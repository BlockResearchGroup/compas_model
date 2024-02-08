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

__all__ = ["HOME", "DATA", "DOCS", "TEMP"]

__all_plugins__ = [
    # "compas_model.blender.scene",
    "compas_model.rhino.scene",
    "compas_model.scene"
    # "compas_viewer.scene",
]
