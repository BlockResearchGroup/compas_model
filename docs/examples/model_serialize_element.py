from compas.geometry import Point
from compas_model.elements import Element
from compas.datastructures import Mesh


def serialize_element():
    """Serialize an element to a JSON file."""
    # --------------------------------------------------------------------------
    # Create elements and a Node.
    # --------------------------------------------------------------------------
    e = Element(
        name="beam",
        geometry_simplified=Point(0, 0, 0),
        geometry=Mesh.from_polyhedron(6),
    )
    # --------------------------------------------------------------------------
    # Serialize the model_node.
    # --------------------------------------------------------------------------
    print(e)
    e.to_json("data/my_element.json", pretty=True)
    Element.from_json("data/my_element.json")
    print(e)


serialize_element()
