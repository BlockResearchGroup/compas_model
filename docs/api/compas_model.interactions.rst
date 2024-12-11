********************************************************************************
compas_model.interactions
********************************************************************************

.. currentmodule:: compas_model.interactions

This module provides classes for defining the type of interaction that exists between two elements.
The interaction type could determine, for example, how forces are transferred from one element to the other.
The interaction type could also determine whether an interaction is permanent or temporary;
for example, for designing construction sequences.
The different types of interactions will have to be interpreted by the context in which the model is used.

Interactions do not define the geometry of a joint or interface, but rather how the elements are connected.
In the case of a wood joint, for example, an interaction could define whether the joinery is dry, glued, or mechanical,
and what the properties of this connection are.


Classes
=======

.. autosummary::
    :toctree: generated/
    :nosignatures:

    Interaction
    ContactInterface