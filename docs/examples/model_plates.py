from compas_model.elements import Plate
from compas_model.model import Model
import elements_plate_application_folding as folding

polys0, polys1 = folding.create_folded_mesh()
model = Model()

for i in range(0, len(polys0)):
    plate = Plate.from_two_polygons(polys0[i], polys1[i])
    model.add_element("my_plate"+str(i), plate)

# Add interaction - first wall.
model.add_interaction(0, 1)
model.add_interaction(1, 2)
model.add_interaction(2, 3)
model.add_interaction(3, 4)
model.add_interaction(4, 5)

# Add interactions - second wall.
model.add_interaction(6, 7)
model.add_interaction(7, 8)
model.add_interaction(8, 9)
model.add_interaction(9, 10)
model.add_interaction(10, 11)

# Add interaction - roof.
model.add_interaction(12, 13)
model.add_interaction(13, 14)
model.add_interaction(14, 15)
model.add_interaction(15, 16)
model.add_interaction(16, 17)

# rows
for i in range(6):
    model.add_interaction(i, i+6)
    model.add_interaction(i+6, i+12)

# Print the model structure.
model.print()
