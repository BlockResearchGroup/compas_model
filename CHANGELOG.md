# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

* Added reference to model `Element.model` to `Element`.
* Added `Element.modelgeometry` as the cached geometry of an element in model coordinates, taking into account the modifying effect of interactions with other elements.
* Added `Element.modeltransformation` as the cached transformation from element to model coordinates.
* Added `Element.compute_elementgeometry()`.
* Added `Element.compute_modelgeometry()` to replace `Element.compute_geometry()`.
* Added `Element.compute_modeltransformation()` to replace `Element.compute_worldtransformation()`.
* Added `Element.is_dirty`.
* Added `compas_model.geometry.minkowski_sum_xy` to compute the Minkowski sum A + B of two convex polygons in the XY plane.
* Added `compas_model.geometry.minkowski_difference_xy` as a convenience method to compute A + -B.
* Added `compas_model.geometry.is_collision_poly_poly_xy` to check for collisions between convex polygons in the XY plane.
* Added `compas_model.geometry.intersection_ray_triangle`.
* Added `compas_model.geometry.intersections_line_aabb`.
* Added `compas_model.geometry.intersections_line_box`.
* Added `compas_model.geometry.intersections_ray_aabb`.
* Added `compas_model.geometry.intersections_ray_box`.
* Added `compas_model.geometry.is_intersection_box_box`.
* Added `compas_model.geometry.is_intersection_line_aabb`.
* Added `compas_model.geometry.is_intersection_line_box`.
* Added `compas_model.geometry.is_intersection_ray_aabb`.
* Added `compas_model.geometry.is_intersection_ray_box`.
* Added `compas_model.geometry.is_intersection_segment_aabb`.
* Added `compas_model.geometry.is_intersection_segment_box`.
* Added `compas_model.geometry.pca_box` for fast OBB calculation.
* Added `compas_model.algorithms.mesh_mesh_contacts`.
* Added `compas_model.datastructures.BVH` extending the base compas tree data structure into a bounding volume hierarchy.
* Added `compas_model.datastructures.AABBNode` representing a node of the BVH using an axis-aligned bounding box.
* Added `compas_model.datastructures.OBBNode` representing a node of the BVH using an oriented bounding box.
* Added `compas_model.datastructures.KDTree` for nearest neighbour search among elements.
* Added `compas_model.models.bvh.ElementBVH`.
* Added `compas_model.models.bvh.ElementAABBNode`.
* Added `compas_model.models.bvh.ElementOBBNode`.
* Added `compas_model.models.Model.collisions` iterator.
* Added `compas_model.models.graph.InteractionGraph.clear_edges`.

### Changed

* Changed `Element.graph_node` to `Element.graphnode`.
* Changed `Element.tree_node` to `Element.treenode`.
* Fixed bug in deserialisation (`element.model` was not set properly).

### Removed

* Removed model reference `ElementTree.model` from `ElementTree`.
* Removed `InterfaceElement` from elements.
* Removed `BlockModel`.
* Removed `BlockElement`.
* Removed `model_interfaces`.
* Removed `model_overlaps`.


## [0.4.5] 2024-12-11

### Added

* Added `compas_model.elements.Element.parent` as alias for `compas_model.elements.Element.tree_node.parent`.
* Added missing graph node reference to elements during deserialisation process.

### Changed

* Moved method parameter to element atribute `compas_model.elements.Element.include_features`.
* Moved method parameter to element atribute `compas_model.elements.Element.inflate_aabb`.
* Moved method parameter to element atribute `compas_model.elements.Element.inflate_obb`.
* Changed `compas_model.elements.Element.compute_worldtransformation` to include frame of model.
* Changed `compas_model.models.elementnode.ElementNode` to include children (previous functionality of `GroupNode`).
* Changed root of element tree to element node instead of group node.
* Changed deserialisation process of model according to removal of group node.

### Removed

* Removed `compas_model.models.groupnode.GroupNode`.


## [0.4.4] 2024-06-13

### Added

### Changed

* Restored backwards compatibility with Python2.7 in core modules.

### Removed


## [0.4.3] 2024-05-15

### Added

* Added scale for blockmodel forces in custom blockmodel viewer.

### Changed

* Changed minimum size of area for interface detection in `blockmodel_interfaces`.

### Removed


## [0.4.2] 2024-05-14

### Added

### Changed

### Removed


## [0.4.1] 2024-05-12

### Added

### Changed

### Removed


## [0.4.0] 2024-05-12

### Added

* Added implementation for `Model.has_interaction`.
* Added property `Model.interactionlist`.
* Added `Model.add_material`.
* Added `Model.assign_material`.
* Added `Model.has_material`.
* Added `Model.elements` iterator.
* Added `Model.materials` iterator.
* Added `Model.interactions` iterator.
* Added read-only `Element.material`.
* Added `compas_model.materials.Material`.
* Added `compas_model.materials.Concrete`.
* Added `compas_model.materials.Timber` (stub imlementation).
* Added `compas_model.interactions.ContactInteraction` based on `compas_assembly.datastructures.Interface`.
* Added `compas_model.algorithms.blockmodel_interfaces` for interface detection of "block models".
* Added `compas_model.elements.block.BlockGeometry` based on `compas_assembly.datastructures.Block`.
* Added `compas_model.analysis.cra_penalty_solve` as wrapper for `compas_cra.equilibrium.cra_penalty_solve`.

### Changed

* Fixed `Model.elementdict` and `Model.elementlist` return `None` after (de)serialization.
* Changed `Model.edge_interaction` to `Model.edge_interactions`.
* Changed `Model.remove_interaction` to accept optional `interaction` parameter (currently raising `NotImplementedError`).
* Fixed bug in serialisation of interaction graph, by converting node element attributes to guid strings on a copy of the node attribute dict instead of the original.
* Changed `compas_model.model` to `compas_model.models`.

### Removed

* Removed reference to `model` in `ElementTree`.
* Removed `Model.elementslist`.
* Removed `Model.materialslist`.
* Removed `Model.elementsdict`.

## [0.3.0] 2024-03-08

### Added

### Changed

### Removed


## [0.2.0] 2024-03-08

### Added

* Added `compas_model.model.Model`.
* Added `compas_model.model.ElementNode`.
* Added `compas_model.model.GroupNode`.
* Added `compas_model.model.ElementTree`.
* Added `compas_model.model.InteractionGraph`.
* Added `compas_model.elements.Element`.
* Added `compas_model.elements.Feature`.
* Added `compas_model.elements.BlockElement`.
* Added `compas_model.elements.BlockFeature`.
* Added `compas_model.elements.InterfaceElement`.
* Added `compas_model.elements.InterfaceFeature`.
* Added `compas_model.elements.PlateElement`.
* Added `compas_model.elements.PlateFeature`.
* Added `compas_model.interactions.Interaction`.
* Added `compas_model.algorithms.collider`.
* Added `compas_model.scene.BlockObject`.
* Added `compas_model.scene.ElementObject`.
* Added `compas_model.scene.ModelObject`.
* Added `compas_model.notebook.scene.ThreeBlockObject`.
* Added `compas_model.notebook.scene.ThreeElementObject`.
* Added `compas_model.notebook.scene.ThreeModelObject`.
* Added `compas_model.elements_connected_by`.
* Added plugin for `installable_rhino_package`.
* Added `PlateElement` and `PlateFeature` to 2nd level imports.

### Changed

* Fixed cannot import `compas_model.elements` in Rhino.

### Removed
