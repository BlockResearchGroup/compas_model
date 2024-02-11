from compas.geometry import Frame, Polygon
from compas.datastructures import Mesh
from compas_model.elements import BlockElement, BeamElement, PlateElement, InterfaceElement
from compas_model.model import Model

model = Model()
model.add_element(BlockElement(Mesh.from_polyhedron(4 + 0)))
model.add_element(BeamElement(Frame.worldXY(), 10, 1, 1))
model.add_element(PlateElement(Polygon([[0, 0, 0], [0, 1, 0], [1, 1, 0]]), 0.5))
model.add_element(InterfaceElement(Polygon([[0, 0, 1], [0, 1, 1], [1, 1, 1]])))
model.print()
