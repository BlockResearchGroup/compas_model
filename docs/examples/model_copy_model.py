from compas.geometry import Point
from compas_model.elements import Element
from compas_model.model import Model
from compas.datastructures import Mesh


def copy_model():
    """Copy a model and all its attributes."""
    # --------------------------------------------------------------------------
    # Create elements and a Node and a ElementTree and a Model.
    # --------------------------------------------------------------------------
    e0 = Element(
        name="beam",
        geometry_simplified=Point(0, 0, 0),
        geometry=Mesh.from_polyhedron(6),
    )
    e1 = Element(
        name="beam",
        geometry_simplified=Point(0, 5, 0),
        geometry=Mesh.from_polyhedron(6),
    )
    e2 = Element(
        name="block",
        geometry_simplified=Point(0, 0, 0),
        geometry=Mesh.from_polyhedron(6),
    )
    e3 = Element(
        name="block",
        geometry_simplified=Point(0, 5, 0),
        geometry=Mesh.from_polyhedron(6),
    )

    model = (
        Model()
    )
    truss1 = model.add_group("truss1")
    truss2 = model.add_group("truss2")
    truss1.add_element(e0.name, e0)
    truss1.add_element(e1.name, e1)
    truss2.add_element(e2.name, e2)
    truss2.add_element(e3.name, e3)

    model.add_interaction(e0, e1)

    print("BEFORE COPY")
    model.print()
    model.print_interactions()
    # --------------------------------------------------------------------------
    # Copy the model.
    # --------------------------------------------------------------------------
    print("AFTER COPY")
    model_copy = model.copy()
    model_copy.print()
    model_copy.print_interactions()


copy_model()
