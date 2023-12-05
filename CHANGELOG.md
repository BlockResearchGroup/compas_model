# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

### Changed

### Removed


## [0.1.0] 2023-12-05

### Added

* TEST_PULL_REQUESTS(LICENSE) change to MIT license
* TEST_PULL_REQUESTS(requirements-dev.txt) added shapely library
* TEST_PULL_REQUESTS(readme.md) remove emtpy spaces

* DATA_STRUCTURE_MODEL(src\compas_model\model\group_node.py) create a group node that has an attribute of _my_object that is stored in the node Attributes, check the serialization, there must be a property _my_object that refers to the attribute. Try this class from the compas2 Tree implementation.
* DATA_STRUCTURE_MODEL(src\compas_model\model\element_node.py) same description as for the group_node, but this type the class works with elements only
* DATA_STRUCTURE_MODEL(src\compas_model\model\model.py) bring the code from the assembly
* DATA_STRUCTURE_MODEL(src\compas_model\model\element_tree.py) bring the code from the assembly
* DATA_STRUCTURE_MODEL(src\compas_model\model\tree_util.py) bring the composition functionality
* DATA_STRUCTURE_MODEL(all) remove all the additional methods
* DATA_STRUCTURE_MODEL(all) add the rest of the methods to work with data trees.


### Changed

### Removed
