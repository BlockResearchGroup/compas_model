********************************************************************************
Elements: Beam
********************************************************************************

A beam is a data structure that represents a **rectangular beam** and a **central axis**. 

It also contains a **target axis**, which is often smaller than the **central axis**.
This is useful for the representation of **fabrication** element - a beam that is a longer geometry compared to a central axis of a **structure**.

.. figure:: /_images/elements_beam.jpg
    :figclass: figure
    :class: figure-img img-fluid


.. literalinclude:: elements_beam.py
    :language: python
