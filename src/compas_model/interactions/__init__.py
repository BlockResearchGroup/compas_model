"""This module provides classes for defining the type of interaction that exists between two elements.
The interaction type could determine, for example, how forces are transferred from one element to the other.
The interaction type could also determine whether an interaction is permanent or temporary; for example, for designing construction sequences.
The different types of interactions will have to be interpreted by the context in which the model is used.
"""

from .interaction import Interaction

__all__ = [
    "Interaction",
]
