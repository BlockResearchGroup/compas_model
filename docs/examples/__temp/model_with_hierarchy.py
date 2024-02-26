from compas.geometry import Frame
from compas.datastructures import Mesh
from compas_model.elements import BlockElement, BeamElement
from compas_model.model import Model


model = Model()

group_blocks = model.add_element(BlockElement(Mesh(), name="blocks"))
my_block_0 = BlockElement(Mesh.from_polyhedron(4 + 0))
my_block_1 = BlockElement(Mesh.from_polyhedron(4 + 2))
group_blocks.add_element(my_block_0)
group_blocks.add_element(my_block_1)

group_beams = model.add_element(BeamElement(Frame.worldXY(), 10, 1, 1, name="beams"))
my_beam_0 = BeamElement(Frame.worldXY(), 10, 1, 1)
my_beam_1 = BeamElement(Frame.worldXY(), 20, 1, 1)
group_beams.add_element(my_beam_0)
group_beams.add_element(my_beam_1)

model.print()
