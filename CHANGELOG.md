# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

### Changed

### Removed

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
