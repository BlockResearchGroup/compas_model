import elements_plate_application_folding as folding
from compas_model.elements import PlateElement
from compas_model.models import Model

polys0, polys1 = folding.create_folded_mesh()
model = Model()

for i in range(0, len(polys0)):
    plate = PlateElement.from_two_polygons(polys0[i], polys1[i])
    model.add_element(plate)

# Add interaction - first wall.
model.add_interaction_by_index(0, 1)
model.add_interaction_by_index(1, 2)
model.add_interaction_by_index(2, 3)
model.add_interaction_by_index(3, 4)
model.add_interaction_by_index(4, 5)

# Add interactions - second wall.
model.add_interaction_by_index(6, 7)
model.add_interaction_by_index(7, 8)
model.add_interaction_by_index(8, 9)
model.add_interaction_by_index(9, 10)
model.add_interaction_by_index(10, 11)

# Add interaction - roof.
model.add_interaction_by_index(12, 13)
model.add_interaction_by_index(13, 14)
model.add_interaction_by_index(14, 15)
model.add_interaction_by_index(15, 16)
model.add_interaction_by_index(16, 17)

# rows
for i in range(6):
    model.add_interaction_by_index(i, i + 6)
    model.add_interaction_by_index(i + 6, i + 12)

# Print the model structure.
model.print()
