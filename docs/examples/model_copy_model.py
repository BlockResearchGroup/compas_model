from compas_model.elements import BlockElement
from compas_model.model import Model
from compas.datastructures import Mesh


def copy_model():
    """Copy a model and all its attributes."""
    # --------------------------------------------------------------------------
    # Create elements and a Node and a ElementTree and a Model.
    # --------------------------------------------------------------------------
    elements = [BlockElement(Mesh.from_polyhedron(4 + i*2)) for i in range(3)]

    model = (
        Model()
    )

    model.add_element(elements[0])
    model.add_element(elements[1])
    model.add_element(elements[2])

    model.add_interaction(elements[0], elements[2])

    print("BEFORE COPY")
    model.print()
    # --------------------------------------------------------------------------
    # Copy the model.
    # --------------------------------------------------------------------------
    print("AFTER COPY")
    model_copy = model.copy()
    model_copy.print()


copy_model()
