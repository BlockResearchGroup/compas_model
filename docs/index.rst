********************************************************************************
Documentation of COMPAS MODEL
********************************************************************************

Model represents:
=================
-  a **Tree**
-  a **Graph**
-  a dictionary of **Elements**

What is for?
============
-  **hierarchy** and **connectivity** of structural elements
-  storage of data for and from **structural analysis** and **fabrication**
-  **serialization** to JSON files

Installation
============

.. code-block:: bash

   pip install compas_model

Create a Model
==============

.. literalinclude:: /examples/model.py
    :language: python

Add Connectivity
================

.. literalinclude:: /examples/model_with_interactions.py
    :language: python

Create Hierarchy
================
.. literalinclude:: /examples/model_with_hierarchy.py
    :language: python


Table of Contents
=================

.. toctree::
   :maxdepth: 3
   :titlesonly:

   Introduction <self>
   installation
   examples
   api
   devguide
   license
   acknowledgements


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`