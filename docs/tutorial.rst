********************************************************************************
Tutorial
********************************************************************************


Element
=======

Here, we create a simple element using the :class:`Element`. These represent structural elements. In this case, the :class:`BlockElement` is a direct representation of a :class:Mesh from COMPAS. 

.. code-block:: python

    from compas.datastructures import Mesh
    from compas_model.elements import BlockElement
    
    element = BlockElement(Mesh.from_polyhedron(4))
    print(element)


Other Types of Elements
=======================

Similarly, we can create other types of elements such as :class:`BeamElement`, :class:`PlateElement`, and :class:InterfaceElement. The beam is a representation of an axis with a box around it. The plate is a representation of a polygon with a specified thickness. The interface is a representation of a polygon, commonly used for storing the common "touching" faces between flat parts of an element. You can expand this list of Element classes by inheriting from the :class:`Element` class. However, do not use the Element class itself, as it is an abstract class. Instead, use the implementations of the Element class, such as :class:`BlockElement`, :class:`BeamElement`, :class:`PlateElement`, and :class:`InterfaceElement`.

.. code-block:: python

    from compas.geometry import Frame, Polygon
    from compas.datastructures import Mesh
    from compas_model.elements import BlockElement, BeamElement, PlateElement, InterfaceElement
    
    my_block = BlockElement(Mesh.from_polyhedron(4))
    my_beam = BeamElement(Frame.worldXY(), 10, 1, 1)
    my_plate = PlateElement(Polygon([[0, 0, 0], [0, 1, 0], [1, 1, 0]]), 0.5)
    my_joint = InterfaceElement(Polygon([[0, 0, 1], [0, 1, 1], [1, 1, 1]]))


Create Model
============

"There are several ways to store elements, including lists, dictionaries, sets, and others. The :class:Model class serves as a container to keep track of elements' adjacency (Graph) and hierarchy (Tree). The :class:`Model` class manages these data structures when elements are added, removed, updated, grouped, or when adjacency is changed." We can add elements to the model, and it will automatically create tree nodes and graph nodes for each element.

.. code-block:: python

    from compas_model.model import Model
    from compas.datastructures import Mesh
    from compas_model.elements import BlockElement
    
    model = Model()
    my_block = BlockElement(Mesh.from_polyhedron(4))
    model.add_element(my_block)
    model.print()


Add Connectivity
================

Now that we know how to create a Model, we can define connectivity. Connectivity can be established in various ways, such as specifying the elements manually, utilizing provided algorithms, or using third-party algorithms that output element-to-element adjacency.

.. code-block:: python

    from compas.geometry import Frame
    from compas.datastructures import Mesh
    from compas_model.elements import BlockElement, BeamElement
    from compas_model.model import Model
    
    model = Model()
    my_block = BlockElement(Mesh.from_polyhedron(4))
    my_beam = BeamElement(Frame.worldXY(), 10, 1, 1)

Create model and elements.

.. code-block:: python

    model.add_element(my_block)
    model.add_element(my_beam)

Add elements to the model.

.. code-block:: python

    model.add_interaction(my_block, my_beam)
    model.add_interaction_by_index(0, 1)

Add interaction between elements (edge in a Graph).

.. code-block:: python

    model.print()

Print to the data-structure in the console.


Add Hierarchy
=============

The hierarchy can be defined as a group of nodes. This group of nodes includes an additional Geometry property in case the group needs to be visualized. Now, you can combine methods from the previous connectivity section with grouping to represent more complex models.

.. code-block:: python

    from compas.geometry import Frame
    from compas.datastructures import Mesh
    from compas_model.elements import BlockElement, BeamElement
    from compas_model.model import Model
    
    model = Model()
    
    group_blocks = model.add_element(BlockElement(Mesh()))
    group_beams = model.add_element(BeamElement(Frame.worldXY(), 10, 1, 1))

Create model with two groups named blocks and beams.

.. code-block:: python

    my_block_0 = BlockElement(Mesh.from_polyhedron(4))
    my_block_1 = BlockElement(Mesh.from_polyhedron(6))
    my_beam_0 = BeamElement(Frame.worldXY(), 10, 1, 1)
    my_beam_1 = BeamElement(Frame.worldXY(), 20, 1, 1)
Crate elements.

.. code-block:: python

    group_blocks.add_element(my_block_0)
    group_blocks.add_element(my_block_1)
    group_beams.add_element(my_beam_0)
    group_beams.add_element(my_beam_1)

Add elements to groups.

.. code-block:: python

    model.print()

Print to the data-structure in the console.


Traverse Hierarchy
==================

When elements are added to the model, the node property of the element is automatically set to the corresponding node in the model. This allows us to traverse the hierarchy of the model. For example, we can get the parent of an element:

.. code-block:: python

    from compas.geometry import Frame
    from compas.datastructures import Mesh
    from compas_model.elements import BlockElement
    from compas_model.model import Model
    
    model = Model()
    my_block = BlockElement(Mesh.from_polyhedron(4))
    model.add_element(my_block)

Create model and add elements.

.. code-block:: python

    my_block.tree_node
    my_block.graph_node

Using this property you can traverse backwards the hierarchy backwards.

.. code-block:: python

    model.tree
    model.graph

Otherwise you can traverse forwards using recusion from the root node of the model.
