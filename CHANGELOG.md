# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] 2025-09-06

### Added

* Added `Model.has_element_with_name`.
* Added `Model.find_element_with_name`.
* Added `Model.find_element_with_name_or_fail`.
* Added `Model.find_all_elements_of_type`.
* Added `Model.remove_elements_of_type`.
* Added `Model.add_or_get_material`.
* Added lazy-computed `compas_model.elements.Element.surface_mesh` property.
* Added lazy_computed `compas_model.elements.Element.volumetric_mesh` property.
* Added `compas_model.elements.Element.compute_surface_mesh` property.
* Added `compas_model.elements.Element.compute_volumetric_mesh` property.

### Changed

* Changed `compas_model.elements.Element.transform` to apply the new transformation on top of the current one, instead of replacing it.

### Removed

* Removed lazy-computed `compas_model.elements.Element.femesh2` property.
* Removed lazy_computed `compas_model.elements.Element.femesh3` property.
* Removed `compas_model.elements.Element.compute_femesh2` property.
* Removed `compas_model.elements.Element.compute_femesh3` property.

## [0.8.0] 2025-06-04

### Added

* Added back `Group` Element.
* Added `ElementObject` and `ModelElement` for `compas_viewer`.
* Added `compas_model.algorithms.brep_brep_contacts` for calculation of simple, flat contacts between two breps.
* Added `compas_model.models.Model.contacts` iterator.
* Added `brep_brep_contacts` for calculation of contacts between elements with brep geometry.
* Added `compas_model.datastructures.BVHNode.add` to take care of `depth` value.
* Added `compas_model.elements.Element.apply_modifiers`.
* Added `compas_model.elements.Element.material` setter.
* Added lazy-computed `compas_model.elements.Element.femesh2` property.
* Added lazy_computed `compas_model.elements.Element.femesh3` property.
* Added `compas_model.elements.Element.compute_femesh2` property.
* Added `compas_model.elements.Element.compute_femesh3` property.
* Added `compas_model.modifiers`.
* Added `compas_model.modifiers.Modifier`.
* Added `compas_model.models.Model.add_modifier`.

### Changed

* Updated existing `ElementObject` and `ModelElement` for renewed `SceneObject` APIs.
* Changed `compas_model.interactions.Contact` to require only points, and lazy calculate all other attributes only when not explicitly provided.
* Changed `compas_model.models.Model.compute_contacts` to use BVH with OOB nodes for calculation of contact candidates.
* Changed default parmeter value of `inflate` in `compas_model.elements.Element.compute_aabb`.
* Changed default parmeter value of `inflate` in `compas_model.elements.Element.compute_obb`.
* Changed default parmeter value of `inflate` in `compas_model.elements.Element.compute_collision_mesh`.
* Changed default parmeter value of `inflate` in `compas_model.elements.Beam.compute_aabb`.
* Changed default parmeter value of `inflate` in `compas_model.elements.Beam.compute_obb`.
* Changed default parmeter value of `inflate` in `compas_model.elements.Column.compute_aabb`.
* Changed default parmeter value of `inflate` in `compas_model.elements.Column.compute_obb`.
* Changed default parmeter value of `inflate` in `compas_model.elements.Plate.compute_aabb`.
* Changed default parmeter value of `inflate` in `compas_model.elements.Plate.compute_obb`.
* Fixed bug in `compas_model.elements.Beam.compute_aabb`.
* Fixed bug in `compas_model.elements.Beam.compute_obb`.
* Fixed bug in `compas_model.elements.Column.compute_aabb`.
* Fixed bug in `compas_model.elements.Column.compute_obb`.
* Fixed bug in `compas_model.elements.Plate.compute_aabb`.
* Fixed bug in `compas_model.elements.Plate.compute_obb`.
* Changed `compas_model.model.Model.elements` to property.
* Changed `compas_model.model.Model.materials` to property.
* Changed `compas_model.model.Model.contacts` to property.
* Changed `compas_model.model.Element.compute_modelgeometry` to use new modifier implementation.
* Changed BVH to use AABB by default.
* Changed interaction graph to store elements by guid reference.
* Changed root node of element tree to default `TreeNode`.
* Changed `ElementNode` to require `Element`.

### Removed

* Removed modifier methods from `compas_model.elements.Beam`.
* Removed modifier methods from `compas_model.elements.Column`.
* Removed `Shape` from parameter options in `compas_model.elements.Element`.
* Removed `compas_model.interactions.modifiers`.
* Removed `compas_model.models.Model.compute_collisions`.
* Removed `compas_model.models.Model.add_elements`.


## [0.7.0] 2025-03-12

### Added

### Changed

* Changed calculation of element transformation to include transformation of model.
* Changed serialisation to include transformation of model.

### Removed


## [0.6.1] 2025-02-01

### Added

### Changed

* Fixed bug in `compas_model.models.Model.transformation`.
* BVH and KDTree search combination in `compas_model.models.Model.compute_contacts`.
* Clean-up of mesh boolean triangulation in `compas_model.interactions.modifiers.boolean_modifier`.

### Removed


## [0.6.0] 2025-01-30

### Added

### Changed

* Changed `compas_model.elements.Element.compute_modeltransformation` to use only the stack of transformations of its ancestors. Each transformation in the stack defines the change from local to world coordinates of the corresponding element.

### Removed

* Removed `compas_model.models.Model.frame`.


## [0.5.1] 2025-01-22

### Added

### Changed

* Fixed bug in `compas_model.models.Model.compute_contacts` resulting from completely skipping existing edges.
* Fixed bug in import of `boolean_difference_mesh_mesh`.

### Removed


## [0.5.0] 2025-01-21

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
* Added `compas_model.elements.BeamElement`.
* Added `compas_model.elements.ColumnElement`.
* Added `compas_model.elements.PlateElement`.
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
