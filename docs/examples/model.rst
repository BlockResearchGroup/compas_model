********************************************************************************
Model
********************************************************************************

Model contains:
    - a dictionary of elements
    - a tree of GroupNode and ElementNode
    - a graph of element connectivity

Create Model with ElementNode (leaf) and GroupNode (branch).

.. literalinclude:: model.py
    :language: python

Create the Model with interactions.

.. literalinclude:: model_with_interactions.py
    :language: python

Copy the Model.

.. literalinclude:: model_copy_model.py
    :language: python

Serialize a model node: GroupNode and ElementNode.

.. literalinclude:: model_serialize_model_node.py
    :language: python

Serialize the ElementTree. Normally this data-structure is hidden from the user.

.. literalinclude:: model_serialize_model_tree.py
    :language: python

Serialize the full Model.

.. literalinclude:: model_serialize_model.py
    :language: python


