# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

* Added `requirements-dev` added shapely library
* Added `compas_model.model.group_node.GroupNode` create a group node that has an attribute of _my_object that is stored in the node Attributes, check the serialization, there must be a property _my_object that refers to the attribute. Try this class from the compas2 Tree implementation.
* Added `compas_model.model.group_node.ElementNode` same description as for the group_node, but this type the class works with elements only
* Added `compas_model.model.model.Model` bring the code from the assembly
* Added `compas_model.model.element_tree.ElementTree` bring the code from the assembly
* Added tutorials and descriptions in the documentations.
* Added `compas_model.model.algorithms.collider` class for closest object queries.
* Added data-sets of robots and timber beams.

### Changed

* Elements classes are refactored to have as minimal representation as possible.
* Preparation of the repository for pull requests by removing all element classes.
* Contents of `compas_model.elements.Element` is removed.
* Changed all properties are documented following compas format.
* Changed `compas_model.model.element_node.ElementNode` serialization simplified, without using children property
* Changed `compas_model.model.group_node.GroupNode` added `name` public and private properties and removed private properties as much as possible for internal methods
* Changed `compas_model.model.element_tree.ElementTree.` serialization is divided into two parts: a) branch `GroupNode` and b) leaf `ElementNode`, this is information is given `children` property.
* Changed `__eq__` to `GroupNode` by `name` instead of by `guid` for the future `Merge` method, when names of the branches are matched.
* Changed `parent` property from `None` to parent object in the `compas_mode.model.ElemenTree`
* Changed `all` general docstring formatting issues
* Changed `compas_model.model.element_node.ElementNode` property `my_object` is changed to `Element`
* Changed `compas_model.model.group_node.GroupNode` property `my_object` is changed to `geometry`
* Changed `compas_model.model.element_tree.ElementTree.` serialization method `from_data` check if node has not children and creates as a result different node type, instead of `my_object`
* Changed `test_model` function `create_model` by adding more nodes at leaves to really check if the serialization works.
* Changed `test_model` face_polygons are computed from box corners.
* Changed `compas_model.model.algorithms.collider` is defined as methods instead of a static class.
* Changed the folder structure of elements is flatenned.
* Contents of `compas_model.elements.Element` child classes transformation methods changed to handle the scaling of oriented bounding box.

### Removed

* Removed `__eq__` operator in the `ElementNode`, equality must be checked only for `GroupNode`
* Removed `fabrication` and `structure` properties from the `compas_model.elements.Element`
