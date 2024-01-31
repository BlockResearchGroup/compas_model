********************************************************************************
Tutorial
********************************************************************************


Element
=======

Here, we create a simple element using the :class:`Element`. These represent structural elements. In this case, the :class:`Block` is a direct representation of a :class:Mesh from COMPAS. 

>>> from compas.datastructures import Mesh
>>> from compas_model.elements import Block
>>>
>>> element = Block(Mesh.from_polyhedron(4))
>>> print(element)
Block cc7e1583-c083-4b29-92ad-d191a58664dc

Other Types of Elements
=======================

Similarly, we can create other types of elements such as :class:`Beam`, :class:`Plate`, and :class:Interface. The beam is a representation of an axis with a box around it. The plate is a representation of a polygon with a specified thickness. The interface is a representation of a polygon, commonly used for storing the common "touching" faces between flat parts of an element. You can expand this list of Element classes by inheriting from the :class:`Element` class. However, do not use the Element class itself, as it is an abstract class. Instead, use the implementations of the Element class, such as :class:`Block`, :class:`Beam`, :class:`Plate`, and :class:`Interface`.


>>> from compas.geometry import Frame, Polygon
>>> from compas.datastructures import Mesh
>>> from compas_model.elements import Block, Beam, Plate, Interface
>>>
>>> my_block = Block(Mesh.from_polyhedron(4))
>>> my_beam = Beam(Frame.worldXY(), 10, 1, 1)
>>> my_plate = Plate(Polygon([[0, 0, 0], [0, 1, 0], [1, 1, 0]]), 0.5)
>>> my_joint = Interface(Polygon([[0, 0, 1], [0, 1, 1], [1, 1, 1]]))


Create Model
============

"There are several ways to store elements, including lists, dictionaries, sets, and others. The :class:Model class serves as a container to keep track of elements' adjacency (Graph) and hierarchy (Tree). The :class:`Model` class manages these data structures when elements are added, removed, updated, grouped, or when adjacency is changed." We can add elements to the model, and it will automatically create tree nodes and graph nodes for each element.

>>> from compas_model.model import Model
>>> from compas.datastructures import Mesh
>>> from compas_model.elements import Block
>>> 
>>> model = Model()
>>> my_block = Block(Mesh.from_polyhedron(4))
>>> model.add_element("my_block", my_block)
>>> model.print()
────────────────────────────────────────────────────────────────────────────────────────────────────
HIERARCHY
<Model> with 1 elements, 1 children, 0 interactions, 1 nodes
    <ElementNode> my_block, <element> Block 5be9ca8d-7cdf-4cc9-9db9-c25029bc07a0 | Parent: root | Root: model
INTERACTIONS
<Nodes>
    5be9ca8d-7cdf-4cc9-9db9-c25029bc07a0
<Edges>
────────────────────────────────────────────────────────────────────────────────────────────────────

We can also retrieve the nodes of elements, along with the elements themselves. For example, using the node name(s):

.. code-block:: python

    node = model.get_by_name("my_block")
    nodes = model.get_by_names("my_block")
    node = model["my_block"]

The individual elements are stored in the element attribute:

.. code-block:: python

    node_element = model["my_block"].element

Or by the element GUID:

.. code-block:: python

    element = model.elements[my_block.guid]


Add Connectivity
================

Now that we know how to create a Model, we can define connectivity. Connectivity can be established in various ways, such as specifying the elements manually, utilizing provided algorithms, or using third-party algorithms that output element-to-element adjacency.

>>> from compas.geometry import Frame
>>> from compas.datastructures import Mesh
>>> from compas_model.elements import Block, Beam
>>> from compas_model.model import Model
>>> 
>>> 
>>> model = Model()
>>> my_block = Block(Mesh.from_polyhedron(4 + 0))
>>> my_beam = Beam(Frame.worldXY(), 10, 1, 1)
>>> model.add_element("my_block", my_block)
>>> model.add_element("my_beam", my_beam)
>>> model.add_interaction(my_block, my_beam)
>>> model.print()
────────────────────────────────────────────────────────────────────────────────────────────────────
HIERARCHY
<Model> with 2 elements, 2 children, 1 interactions, 2 nodes
    <ElementNode> my_block, <element> Block f89f9ee2-08b4-4f5c-8306-fb17a0a530a2 | Parent: root | Root: model
    <ElementNode> my_beam, <element> Beam 6db4b383-dc05-4b55-a688-d5c9adcabbd0 | Parent: root | Root: model
INTERACTIONS
<Nodes>
    f89f9ee2-08b4-4f5c-8306-fb17a0a530a2
    6db4b383-dc05-4b55-a688-d5c9adcabbd0
<Edges>
    f89f9ee2-08b4-4f5c-8306-fb17a0a530a2 6db4b383-dc05-4b55-a688-d5c9adcabbd0
────────────────────────────────────────────────────────────────────────────────────────────────────

Add Hierarchy
=============

The hierarchy can be defined as a group of nodes. This group of nodes includes an additional Geometry property in case the group needs to be visualized. Now, you can combine methods from the previous connectivity section with grouping to represent more complex models.

>>> from compas.geometry import Frame
>>> from compas.datastructures import Mesh
>>> from compas_model.elements import Block, Beam
>>> from compas_model.model import Model
>>> 
>>> 
>>> model = Model()
>>> 
>>> group_blocks = model.add_group("blocks")
>>> my_block_0 = Block(Mesh.from_polyhedron(4 + 0))
>>> my_block_1 = Block(Mesh.from_polyhedron(4 + 2))
>>> group_blocks.add_element("my_block_0", my_block_0)
>>> group_blocks.add_element("my_block_1", my_block_1)
>>> 
>>> group_beams = model.add_group("beams")
>>> my_beam_0 = Beam(Frame.worldXY(), 10, 1, 1)
>>> my_beam_1 = Beam(Frame.worldXY(), 20, 1, 1)
>>> group_beams.add_element("my_beam_0", my_beam_0)
>>> group_beams.add_element("my_beam_1", my_beam_1)
>>> 
>>> model.print()
────────────────────────────────────────────────────────────────────────────────────────────────────
HIERARCHY
<Model> with 4 elements, 6 children, 0 interactions, 4 nodes
    <GroupNode> blocks, <geometry> None | Parent: root | Root: model
        <ElementNode> my_block_0, <element> Block 467297e0-8a26-4c01-a5a5-cd5b76c76034 | Parent: blocks | Root: model
        <ElementNode> my_block_1, <element> Block 2f589e36-3f5f-4546-b03c-a3e84aef9272 | Parent: blocks | Root: model
    <GroupNode> beams, <geometry> None | Parent: root | Root: model
        <ElementNode> my_beam_0, <element> Beam 37ccb07f-84d2-455f-b1a9-c55e61168819 | Parent: beams | Root: model
        <ElementNode> my_beam_1, <element> Beam 426e6a67-14c5-4754-9374-a611e4ba4e73 | Parent: beams | Root: model
INTERACTIONS
<Nodes>
    467297e0-8a26-4c01-a5a5-cd5b76c76034
    2f589e36-3f5f-4546-b03c-a3e84aef9272
    37ccb07f-84d2-455f-b1a9-c55e61168819
    426e6a67-14c5-4754-9374-a611e4ba4e73
<Edges>
────────────────────────────────────────────────────────────────────────────────────────────────────