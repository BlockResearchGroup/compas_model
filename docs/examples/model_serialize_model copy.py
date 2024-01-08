from compas.geometry import Point
from compas_model.elements import Element
from compas_model.model import Model


def serialize_model():
    """Serialize a model and its graph and a model_tree and nodes and the elements inside."""

    # --------------------------------------------------------------------------
    # Create model.
    # --------------------------------------------------------------------------
    model = Model()

    # --------------------------------------------------------------------------
    # Add group nodes - a typical tree node with a name and geometry.
    # --------------------------------------------------------------------------
    car = model.add_group(name="car", geometry=None)
    wheel = car.add_group(name="wheel", geometry=Point(0, 0, 0))

    # --------------------------------------------------------------------------
    # Add element nodes - a "special" tree node with a name and element.
    # --------------------------------------------------------------------------
    spoke1 = wheel.add_element(name="spoke1", element=Element.from_box_dimensions(1, 10, 1))
    spoke2 = wheel.add_element(name="spoke2", element=Element.from_box_dimensions(5, 10, 1))
    spoke3 = wheel.add_element(name="spoke3", element=Element.from_box_dimensions(10, 10, 1))

    # --------------------------------------------------------------------------
    # Add interactions.
    # --------------------------------------------------------------------------
    model.add_interaction(spoke1, spoke2)
    model.add_interaction(spoke1, spoke3)
    model.add_interaction(spoke2, spoke3)
    # --------------------------------------------------------------------------
    # Serialize the model_tree.
    # --------------------------------------------------------------------------
    model.to_json("data/my_model.json", pretty=True)

    # --------------------------------------------------------------------------
    # Deserialize the model_tree.
    # --------------------------------------------------------------------------¨
    model_deserialized = Model.from_json("data/my_model.json")

    # --------------------------------------------------------------------------
    # Print the contents of the deserialized model_tree.
    # --------------------------------------------------------------------------
    model.print()
    model_deserialized.print()


serialize_model()
