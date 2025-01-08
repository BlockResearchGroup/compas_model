==============================================================================
Line-Mesh intersections using a BVH with AABB volumes
==============================================================================

.. figure:: /_images/bvh_aabb_intersections.png

.. rst-class:: lead

this example computes the intersections between a list of rays/lines and a mesh,
using a Bounding Volume Hierarchy (BVH) with axis-aligned bounding boxes (AABBs) as bounding volumes for the tree nodes.
AABBs typically provide a better fit of the geometry of the mesh and its primitives than oriented bounding boxes.
However, they are (slightly) more expensive to compute.

* Load a quad mesh from an OBJ file.
* Convert the quads of the mesh to triangles for accurate intersections.
* Build a BVH with AABB nodes.
* Construct a list of intersection lines.
* Traverse the tree to find the intersection of each line, if one exist.
* Keep track of the boxes of the leaf nodes of the tree for visualisation.
* Visualize the mesh, the lines, the boxes, and the intersections.


.. literalinclude:: bvh_aabb_intersections.py
    :language: python
