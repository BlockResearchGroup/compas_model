from compas.geometry import Point
from compas_model.elements import Element
from compas_model.model import Model


def create_model_with_interactions():
    """Create a model with a hierarchy of groups and elements and interactions."""

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
    model.add_interaction(spoke1, spoke2, name="unknown")
    model.add_interaction(spoke1, spoke3, name="unknown")
    model.add_interaction(spoke2, spoke3, name="unknown")

    # --------------------------------------------------------------------------
    # Print the model to preview the tree structure.
    # --------------------------------------------------------------------------
    model.print()

    # --------------------------------------------------------------------------
    # Output.
    # --------------------------------------------------------------------------
    return model


model = create_model_with_interactions()
