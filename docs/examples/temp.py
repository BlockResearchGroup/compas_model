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

model.add_interaction("my_interaction", plates[0], plates[1])

# model.print()
ViewerModel.show(model, scale_factor=1)
