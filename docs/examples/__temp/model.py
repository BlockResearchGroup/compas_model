from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Polygon
from compas_model.elements import BeamElement
from compas_model.elements import BlockElement
from compas_model.elements import InterfaceElement
from compas_model.elements import PlateElement
from compas_model.models import Model

model = Model()
model.add_element(BlockElement(Mesh.from_polyhedron(4 + 0)))
model.add_element(BeamElement(Frame.worldXY(), 10, 1, 1))
model.add_element(PlateElement(Polygon([[0, 0, 0], [0, 1, 0], [1, 1, 0]]), 0.5))
model.add_element(InterfaceElement(Polygon([[0, 0, 1], [0, 1, 1], [1, 1, 1]])))
model.print()
