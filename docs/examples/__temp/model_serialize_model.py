from compas.geometry import Point
from compas.datastructures import Mesh
from compas_model.elements import BlockElement
from compas_model.model import Model


# --------------------------------------------------------------------------
# Create model.
# --------------------------------------------------------------------------
model = Model()

# --------------------------------------------------------------------------
# Create elements. This depends on a specific application.
# --------------------------------------------------------------------------¨
elements = [BlockElement(Mesh.from_polyhedron(4 + i*2)) for i in range(3)]

# --------------------------------------------------------------------------
# Add element nodes - a "special" tree node with a name and element.
# --------------------------------------------------------------------------
spoke1 = model.add_element(elements[0])
spoke2 = model.add_element(elements[1])
spoke3 = model.add_element(elements[2])

# --------------------------------------------------------------------------
# Add interactions.
# --------------------------------------------------------------------------
model.add_interaction(elements[0], elements[1])
model.add_interaction(elements[0], elements[2])
model.add_interaction(elements[1], elements[2])
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
