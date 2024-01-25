from compas.geometry import Frame
from compas.datastructures import Mesh
from compas_model.elements import Block, Beam
from compas_model.model import Model


model = Model()
my_block = Block(Mesh.from_polyhedron(4 + 0))
my_beam = Beam(Frame.worldXY(), 10, 1, 1)
model.add_element("my_block", my_block)
model.add_element("my_beam", my_beam)
model.add_interaction(my_block, my_beam)
model.print()