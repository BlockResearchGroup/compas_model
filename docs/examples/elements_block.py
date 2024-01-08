from compas.geometry import Polygon, Frame, Transformation
from compas.datastructures import Mesh
from compas_model.elements import Block
from compas_model.model import Model
from compas_model.viewer import ViewerModel


def mesh_from_polygons():
    polygons = [
        Polygon([[2, -2, 0], [2, 2, 0], [2, 2, 4], [2, 0, 4], [2, -2, 2]]),
        Polygon([[-2, -2, 0], [2, -2, 0], [2, -2, 2], [0, -2, 4], [-2, -2, 4]]),
        Polygon([[2, -2, 2], [2, 0, 4], [0, -2, 4]]),
        Polygon([[-2, -2, 4], [0, -2, 4], [2, 0, 4], [2, 2, 4], [-2, 2, 4]]),
        Polygon([[2, 2, 0], [-2, 2, 0], [-2, 2, 4], [2, 2, 4]]),
        Polygon([[-2, 2, 0], [-2, -2, 0], [-2, -2, 4], [-2, 2, 4]]),
        Polygon([[-2, -2, 0], [-2, 2, 0], [2, 2, 0], [2, -2, 0]])
    ]

    mesh = Mesh.from_polygons(polygons)
    return mesh


# --------------------------------------------------------------------------
# Create plate from two polygons.
# --------------------------------------------------------------------------
mesh = mesh_from_polygons()
block = Block(mesh)
block.transform(Transformation.from_frame_to_frame(block.frame, Frame([0, 0, 1], [1, 0, 0], [0, 1, 0.5])))

# --------------------------------------------------------------------------
# Test data.
# --------------------------------------------------------------------------
block = block.copy()

# --------------------------------------------------------------------------
# Create model.
# --------------------------------------------------------------------------
model = Model()
model.add_element("my_block", block)

# --------------------------------------------------------------------------
# Vizualize model.
# --------------------------------------------------------------------------
ViewerModel.show(model, scale_factor=1)
