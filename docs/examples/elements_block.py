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
block.compute_aabb(0.1)
block.compute_obb(0.1)

block.transform(Transformation.from_frame_to_frame(block.frame, Frame([0, 0, 1], [1, 0, 0], [0, 1, 0.5])))
# --------------------------------------------------------------------------
# Test data.
# --------------------------------------------------------------------------
# block_copy = block.copy()
# block_copy.transform(Transformation.from_frame_to_frame(block_copy.frame, Frame([0, 0, 1], [1, 0, 0], [0, 0.1, 0.5])))
# block_copy.transform(Translation.from_vector([5, 0, 0]))
print(block.dimensions)
print(block.guid)
# print(block_copy.guid)

# --------------------------------------------------------------------------
# Create model.
# -----------------------------------------------------------------§---------
model = Model()
model.add_elements([block])
print("Block belongs to the following ElementNode: ",  block.node)

# --------------------------------------------------------------------------
# Visualize model.
# --------------------------------------------------------------------------
ViewerModel.show(model, scale_factor=1)
