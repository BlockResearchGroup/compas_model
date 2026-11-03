# Models

The models package contains the central model data structure, its element-node
specialization, collections, and spatial index. Models reuse the standard
COMPAS `Tree` and `Graph` datastructures for runtime hierarchy and interaction
indexes.

## Element ownership and hierarchy

An element belongs to at most one model and appears exactly once in that
model's hierarchy and interaction graph. A hierarchy parent must belong to the
same model. Use `Model.reparent_element` to move an existing subtree; direct
tree mutation bypasses ownership checks and geometry-cache invalidation.

Element removal is deliberately conservative. `Model.remove_element` accepts
only leaves. Reparent or remove all children before their parent. Successful
removal also clears the element's model, tree-node, and graph-node links so the
element can subsequently be added to another model. Bulk removal by type works
leaf-first and is rejected before mutation if a matching parent contains a
non-matching child.

- [Model](models/model.md)
- [Collections](models/collection.md)
- [Element nodes](models/elementtree.md)
- [Element BVH](models/bvh.md)
