from compas.geometry import Polygon
from compas.datastructures import Mesh
from compas_model.elements import Block
from compas_model.model import Model
from compas_model.viewer.viewer_model import ViewerModel


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


if __name__ == "__main__":

    # --------------------------------------------------------------------------
    # Create model.
    # --------------------------------------------------------------------------
    model = Model()

    # --------------------------------------------------------------------------
    # Create plate from two polygons.
    # --------------------------------------------------------------------------
    mesh = mesh_from_polygons()
    block = Block(mesh)
    mesh.copy()

    # --------------------------------------------------------------------------
    # Or test the example file.
    # --------------------------------------------------------------------------
    # block = Block.from_minimal_example()
    model.add_element("my_block", block)

    # --------------------------------------------------------------------------
    # Vizualize model.
    # --------------------------------------------------------------------------
    ViewerModel.run(model, scale_factor=1)
