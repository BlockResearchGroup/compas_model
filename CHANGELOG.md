# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

### Changed

### Removed

## [0.1.0] 2023-12-20

### Added
* Added empty classes representing different structural elements.
* Minimal implementations for `compas_model.elements.Block`, `compas_model.elements.Beam`, `compas_model.elements.Plate`, `compas_model.elements.Interface`. The goal is to implement the logic from repositories already using the assembly data-structures and create a library of different structural elements.
* Added `get_by_type` and `get_connected_elements` methods for handling the element dictionary and the graph in `compas_model.model.Model` class.
* Added geometry methods in `compas_model.elements.triangulator` class used for meshing the element geometry.
* Added examples files in the documentation for each element type.
* Added `compas_model.viewer.viewer_model` a temporary vizualization file that will be replaced by the Scene mechanism in the future.
* Added `compas_model.elements.element_type` struct like class to be consistant with the naming of elements.

### Changed
* Changed `compas_model.elements.Element` docstring formatting and removing properties with too much specificity. The individual representations of elemements such as Block, Beam, Plate should contain specificity but not the base class.

### Removed
* Changed from `compas_model.elements.Element` EarClipping triangulation methods are moved to `compas_model.elements.Triangulator`. In the future the contents of this class have to be implemented in compas, for the better EarClipping algorithm.

## [0.1.0] 2023-12-08

### Added
* Added `compas_model.model.Model` example
* Added element types (without implementation yet) by three categories: centric, linear, surfacic.

### Changed
* Changed `compas_model.elements.Element` docstring formatting.

### Removed

## [0.1.0] 2023-12-07

### Added

### Changed
* Changed all properties are documented following compas format.
* Changed `compas_model.model.element_node.ElementNode` serialization simplified, without using children property
* Changed `compas_model.model.group_node.GroupNode` added `name` public and private properties and removed private properties as much as possible for internal methods
* Changed `compas_model.model.element_tree.ElementTree.` serialization is divided into two parts: a) branch `GroupNode` and b) leaf `ElementNode`, this is information is given `children` property.
* Changed `__eq__` to `GroupNode` by `name` instead of by `guid` for the future `Merge` method, when names of the branches are matched.
* Changed `parent` property from `None` to parent object in the `compas_mode.model.ElemenTree`

### Removed
* Removed `__eq__` operator in the `ElementNode`, equality must be checked only for `GroupNode`
* Removed `fabrication` and `structure` properties from the `compas_model.elements.Element`

## [0.1.0] 2023-12-06

### Added

### Changed
* Changed `all` general docstring formatting issues
* Changed `compas_model.model.element_node.ElementNode` property `my_object` is changed to `Element`
* Changed `compas_model.model.group_node.GroupNode` property `my_object` is changed to `geometry`
* Changed `compas_model.model.element_tree.ElementTree.` serialization method `from_data` check if node has not children and creates as a result different node type, instead of `my_object`
* Changed `test_model` function `create_model` by adding more nodes at leaves to really check if the serialization works.

### Removed

## [0.1.0] 2023-12-05

### Added

* Added `requirements-dev` added shapely library
* Added `compas_model.model.group_node.GroupNode` create a group node that has an attribute of _my_object that is stored in the node Attributes, check the serialization, there must be a property _my_object that refers to the attribute. Try this class from the compas2 Tree implementation.
* Added `compas_model.model.group_node.ElementNode` same description as for the group_node, but this type the class works with elements only
* Added `compas_model.model.model.Model` bring the code from the assembly
* Added `compas_model.model.element_tree.ElementTree` bring the code from the assembly

### Changed
* Changed `README` remove empty spaces
* Changed `LICENSE` made MIT license

### Removed
