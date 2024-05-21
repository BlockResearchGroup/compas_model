==============================================================================
DEM: A Leaning Stack of Blocks
==============================================================================

.. figure:: /_images/examples_dem_000_stack.png

**This example is an adaptation of a similar example in `compas_assembly`.**

Summary
=======

First, we construct a model from a stack of blocks.
Each block is slightly shifted with respect to the previous one, to creating a leaning tower.
Then, we identify the interfaces between the block,
and compute the contact forces at the interfaces that result in static equilibrium with gravitational loads.
Finally, we export the entire model to a JSON file and visualize the results with the "BlockModelViewer".


Equilibrium
===========

Note that the contact forces (in blue) increase towards the bottom of the stack,
due to the increasing weight.

The resultant forces (in green) between blocks 0 and 1, blocks 1 and 2, and blocks 2 and 3
are not contained in the interfaces between those blocks.
As a result, the stack requires equilibriating "glue" forces (in red) at those interfaces.


.. note::

    This example uses ``compas_cra`` for the equilibrium calculations.
    If you don't have ``compas_cra`` installed,
    or simply don't want to compute the contact forces,
    just comment out lines 6 and 51.


Code
====

.. literalinclude:: 100_stack.py
    :language: python
