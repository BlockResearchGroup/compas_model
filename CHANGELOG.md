# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

### Changed

### Removed


## [0.4.5] 2024-12-11

### Added

* Added `compas_model.elements.Element.parent` as alias for `compas_model.elements.Element.tree_node.parent`.
* Added missing graph node reference to elements during deserialisation process.
* Added a base `BlockModel`.
* Added reference to model `Element.model` to `Element`.
* Added `Element.modelgeometry` as the cached geometry of an element in model coordinates, taking into account the modifying effect of interactions with other elements.
* Added `Element.modeltransformation` as the cached transformation from element to model coordinates.
* Added `Element.compute_elementgeometry()`.
* Added `Element.compute_modelgeometry()` to replace `Element.compute_geometry()`.
* Added `Element.compute_modeltransformation()` to replace `Element.compute_worldtransformation()`.
* Added `Element.is_dirty` that is changed together with neighbor elements.  

### Changed

* Moved method parameter to element atribute `compas_model.elements.Element.include_features`.
* Moved method parameter to element atribute `compas_model.elements.Element.inflate_aabb`.
* Moved method parameter to element atribute `compas_model.elements.Element.inflate_obb`.
* Changed `compas_model.elements.Element.compute_worldtransformation` to include frame of model.
* Changed `compas_model.models.elementnode.ElementNode` to include children (previous functionality of `GroupNode`).
* Changed root of element tree to element node instead of group node.
* Changed deserialisation process of model according to removal of group node.\
* Changed `Element.graph_node` to `Element.graphnode`.
* Changed `Element.tree_node` to `Element.treenode`.
* Changed `blockmodel_interfaces` to use the bestfit frame shared by two aligned interfaces instead of the frame of first face of the pair.

### Removed

* Removed `compas_model.models.groupnode.GroupNode`.
* Removed model reference `ElementTree.model` from `ElementTree`.
* Removed `InterfaceElement` from elements.

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
* Added `compas_model.interactions.ContactInterface` based on `compas_assembly.datastructures.Interface`.
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
