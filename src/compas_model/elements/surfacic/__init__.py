"""
********************************************************************************
surfacic elements
********************************************************************************

.. currentmodule:: compas_model.elements.surfacic

.. rst-class:: lead

Different implementations of surfacic structural elements.

Classes
=======

.. autosummary::
    :toctree: generated/
    :nosignatures:

    Interface
    Plate
"""

from .interface import Interface
from .plate import Plate

# from .membrane import Membrane
# from .shell import Shell


__all__ = ["Interface", "Plate"]
