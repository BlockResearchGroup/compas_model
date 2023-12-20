from compas.geometry import Polygon, Frame, Box, Point, Vector
from compas.datastructures import Mesh
from compas_model.elements import Interface, Block
from compas_model.model import Model
from compas_model.viewer.viewer_model import ViewerModel


if __name__ == "__main__":

    # --------------------------------------------------------------------------
    # Create model.
    # --------------------------------------------------------------------------
    model = Model()

    # --------------------------------------------------------------------------
    # Create plate from two polygons.
    # --------------------------------------------------------------------------
    mesh = Mesh.from_polyhedron(4)
    box0 = Mesh.from_vertices_and_faces(*(Box(2, 2, 2, Frame([-1.5, 0, 0], [1, 0, 0], [0, 1, 0])).to_vertices_and_faces()))
    box1 = Mesh.from_vertices_and_faces(*(Box(2, 2, 2, Frame([1.5, 0, 0], [1, 0, 0], [0, 1, 0])).to_vertices_and_faces()))
    polygon = Polygon([[0, -1, -1], [0, 1, -1], [0, 1, 1], [0, -1, 1]])
    block0 = Block(box0)
    block1 = Block(box1)
    interface = Interface(polygon)
    interface_copy = interface.copy()

    # --------------------------------------------------------------------------
    # Add forces to interface.
    # --------------------------------------------------------------------------
    interface.add_forces("force_resultant", [Point(0, 0, 0)], [Vector(1, 0, 0)], 1, color=[1, 0, 0])
    interface.add_forces("force_vertex", polygon.points, [Vector(-0.25, 0, 0)]*4, 1, color=[0, 0, 1])

    # --------------------------------------------------------------------------
    # Or test the example file.
    # --------------------------------------------------------------------------
    model.add_elements([block0, block1, interface])
    model.add_interaction(block0, interface)
    model.add_interaction(block1, interface)

    # --------------------------------------------------------------------------
    # Vizualize model.
    # --------------------------------------------------------------------------
    ViewerModel.run(model, scale_factor=1)
