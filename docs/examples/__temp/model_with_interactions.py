from compas.datastructures import Mesh
from compas.geometry import Frame
from compas_model.elements import BeamElement
from compas_model.elements import BlockElement
from compas_model.models import Model

model = Model()
my_block = BlockElement(Mesh.from_polyhedron(4 + 0))
my_beam = BeamElement(Frame.worldXY(), 10, 1, 1)
model.add_element(my_block)
model.add_element(my_beam)
model.add_interaction(my_block, my_beam)
model.print()
