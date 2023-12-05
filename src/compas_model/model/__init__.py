"""
********************************************************************************
model
********************************************************************************

.. currentmodule:: compas_model.model

.. rst-class:: lead

Model data structure for representing a hierarchy of nodes with interactions.

Classes
=======

.. autosummary::
    :toctree: generated/
    :nosignatures:

    ElementNode
    GroupNode
    ElementTree
    Model
"""

from .element_node import ElementNode
from .group_node import GroupNode
from .element_tree import ElementTree
from .model import Model


__all__ = ["ElementNode", "GroupNode", "ElementTree", "Model"]
