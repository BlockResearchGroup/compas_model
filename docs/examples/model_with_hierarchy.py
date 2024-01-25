from compas.geometry import Frame
from compas.datastructures import Mesh
from compas_model.elements import Block, Beam
from compas_model.model import Model


model = Model()

group_blocks = model.add_group("blocks")
my_block_0 = Block(Mesh.from_polyhedron(4 + 0))
my_block_1 = Block(Mesh.from_polyhedron(4 + 2))
group_blocks.add_element("my_block_0", my_block_0)
group_blocks.add_element("my_block_1", my_block_1)

group_beams = model.add_group("beams")
my_beam_0 = Beam(Frame.worldXY(), 10, 1, 1)
my_beam_1 = Beam(Frame.worldXY(), 20, 1, 1)
group_beams.add_element("my_beam_0", my_beam_0)
group_beams.add_element("my_beam_1", my_beam_1)

model.print()
