from compas_model.elements import Plate
from compas_model.model import Model
import elements_plate_application_folding as folding
from compas_model.viewer import ViewerModel

top_polygons, bottom_polygons = folding.create_folded_mesh()
model = Model()

plates = []
for idx, polygon in enumerate(bottom_polygons):
    plate = Plate.from_two_polygons(
        polygon0=polygon,
        polygon1=top_polygons[idx],
    )
    plates.append(plate)
    model.add_element("my_plate"+str(idx), plate)

# Add interaction - first wall.
model.add_interaction(plates[0], plates[1])
model.add_interaction(plates[1], plates[2])
model.add_interaction(plates[2], plates[3])
model.add_interaction(plates[3], plates[4])
model.add_interaction(plates[4], plates[5])

# Add interactions - second wall.
model.add_interaction(plates[6], plates[7])
model.add_interaction(plates[7], plates[8])
model.add_interaction(plates[8], plates[9])
model.add_interaction(plates[9], plates[10])
model.add_interaction(plates[10], plates[11])

# Add interaction - roof.
model.add_interaction(plates[12], plates[13])
model.add_interaction(plates[13], plates[14])
model.add_interaction(plates[14], plates[15])
model.add_interaction(plates[15], plates[16])
model.add_interaction(plates[16], plates[17])

# rows
for i in range(6):
    model.add_interaction(plates[i], plates[i+6])
    model.add_interaction(plates[i+6], plates[i+12])

# Print the model structure.
model.print()

# Vizualize the geometry via compas_view:
# ViewerModel.show(model, scale_factor=1, geometry=model.get_interactions_lines())
