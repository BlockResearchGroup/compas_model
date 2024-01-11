from compas.geometry import Point, Line, Frame
from compas.datastructures import Mesh
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
    # Create elements. This depends on a specific application.
    # --------------------------------------------------------------------------
    elements = [
        Element(
            name="unknown",
            frame=Frame.worldXY(),
            geometry_simplified=[Line(Point(-1, 0, 0), Point(1, 0, 0))],
            geometry=[Mesh.from_polyhedron(4 + i*2)],
        )
        for i in range(3)
    ]

    # --------------------------------------------------------------------------
    # Add element nodes - a "special" tree node with a name and element.
    # --------------------------------------------------------------------------
    spoke1 = wheel.add_element(name="spoke1", element=elements[0])
    spoke2 = wheel.add_element(name="spoke2", element=elements[1])
    spoke3 = wheel.add_element(name="spoke3", element=elements[2])

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
