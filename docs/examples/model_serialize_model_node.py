from compas.geometry import Point
from compas_model.elements import Element
from compas_model.model import ElementNode
from compas_model.model import GroupNode


def serialize_model_node():
    """Serialize a model_node and the elements inside."""
    # --------------------------------------------------------------------------
    # Create elements and a Node.
    # --------------------------------------------------------------------------
    group_node = GroupNode(name="timber1", geometry=Point(0, 0, 0))

    # --------------------------------------------------------------------------
    # Serialize the model_node.
    # --------------------------------------------------------------------------
    group_node.to_json("data/my_model_node.json", pretty=True)

    # --------------------------------------------------------------------------
    # Deserialize the model_node.
    # --------------------------------------------------------------------------
    group_node_deserialized = GroupNode.from_json("data/my_model_node.json")

    # --------------------------------------------------------------------------
    # Print the contents of the deserialized model_node.
    # --------------------------------------------------------------------------
    print("model_node:              ", group_node)
    print("model_node_deserialized: ", group_node_deserialized)

    # --------------------------------------------------------------------------
    # Create elements and a Node.
    # --------------------------------------------------------------------------
    element_node = ElementNode(name="spoke1", element=Element.from_box_dimensions(1, 10, 1))

    # --------------------------------------------------------------------------
    # Serialize the model_node.
    # --------------------------------------------------------------------------
    element_node.to_json("data/my_model_node.json", pretty=True)

    # --------------------------------------------------------------------------
    # Deserialize the model_node.
    # --------------------------------------------------------------------------
    element_node_deserialized = ElementNode.from_json("data/my_model_node.json")

    # --------------------------------------------------------------------------
    # Print the contents of the deserialized model_node.
    # --------------------------------------------------------------------------
    print("element_node:              ", element_node, element_node.element.geometry)
    print(
        "element_node_deserialized: ",
        element_node_deserialized,
        element_node_deserialized.element.geometry,
    )


serialize_model_node()
