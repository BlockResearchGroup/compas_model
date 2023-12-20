********************************************************************************
Elements: Plate
********************************************************************************

A plate is a data structure that represents a pair of polygons. 

The frames are oriented outwards. The first polygon is the base.
The meshing is performed by the Ear clipping algorithm without considering the holes.
Nevertheless, it is possible to store holes in the geometry_simplified list attribute.

.. figure:: /_images/elements_plate.jpg
    :figclass: figure
    :class: figure-img img-fluid


.. literalinclude:: elements_plate.py
    :language: python
