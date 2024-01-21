from compas_model.elements import Block
from compas_model.model import Model
from compas.datastructures import Mesh


def copy_model():
    """Copy a model and all its attributes."""
    # --------------------------------------------------------------------------
    # Create elements and a Node and a ElementTree and a Model.
    # --------------------------------------------------------------------------
    elements = [Block(Mesh.from_polyhedron(4 + i*2)) for i in range(3)]

    model = (
        Model()
    )
    truss1 = model.add_group("truss1")
    truss2 = model.add_group("truss2")

    truss1.add_element(elements[0].name, elements[0])
    truss1.add_element(elements[1].name, elements[1])
    truss2.add_element(elements[2].name, elements[2])

    model.add_interaction(elements[0], elements[2])

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
