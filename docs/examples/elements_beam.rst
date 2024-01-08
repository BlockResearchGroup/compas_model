********************************************************************************
Elements: Beam
********************************************************************************

A beam is a data structure that represents a **rectangular beam** with a **central axis**. 

It also contains a **target axis**, which is often smaller than the **central axis**.
This is useful for the representation of a fabrication element - a beam that is longer than than the central axis of the structure

.. figure:: /_images/elements_beam.jpg
    :figclass: figure
    :class: figure-img img-fluid


.. literalinclude:: elements_beam.py
    :language: python
