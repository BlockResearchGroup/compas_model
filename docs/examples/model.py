from compas.geometry import Frame, Polygon
from compas.datastructures import Mesh
from compas_model.elements import Block, Beam, Plate, Interface
from compas_model.model import Model

model = Model()
model.add_element("my_block", Block(Mesh.from_polyhedron(4 + 0)))
model.add_element("my_beam", Beam(Frame.worldXY(), 10, 1, 1))
model.add_element("my_plate", Plate(Polygon([[0, 0, 0], [0, 1, 0], [1, 1, 0]]), 0.5))
model.add_element("my_joint", Interface(Polygon([[0, 0, 1], [0, 1, 1], [1, 1, 1]])))
model.print()

node = model.get_by_name("my_block")
node = model["my_block"]
element = model["my_block"].element
