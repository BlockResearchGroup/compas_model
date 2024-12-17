from math import pi

from compas.geometry import Box
from compas.geometry import Rotation
from compas.geometry import Translation
from compas_viewer import Viewer

from compas_model.elements import BlockElement
from compas_model.interactions import Interaction
from compas_model.models import Model

# Example file to do the following:
# Create a model with 4 columns, 4 column-heads and 1 plate.
# Compute interactions between the elements. TODO: Add interactions and the base element level when geometry is computed.
# Change one column head and check if the elements are dirty.
# Recompute the modelgeometry.

model = Model(name="slab_units")

column_head_0 = BlockElement(name="column_head", shape=Box.from_width_height_depth(300, 300, 300).to_mesh())
column_head_1 = column_head_0.copy()
column_head_2 = column_head_0.copy()
column_head_3 = column_head_0.copy()
column_0 = BlockElement(name="column", shape=Box.from_width_height_depth(300, 2700, 300).to_mesh())
column_1 = column_0.copy()
column_2 = column_0.copy()
column_3 = column_0.copy()
beam_0 = BlockElement(name="beam", shape=Box.from_width_height_depth(300, 300, 5700).to_mesh())
beam_1 = beam_0.copy()
beam_2 = beam_0.copy()
beam_3 = beam_0.copy()
slab = BlockElement(name="slab", shape=Box.from_width_height_depth(5700, 300, 5700).to_mesh())

column_head_0.transformation = Translation.from_vector([-3000, -3000, 2850])
column_head_1.transformation = Translation.from_vector([-3000, 3000, 2850])
column_head_2.transformation = Translation.from_vector([3000, 3000, 2850])
column_head_3.transformation = Translation.from_vector([3000, -3000, 2850])
column_0.transformation = Translation.from_vector([-3000, -3000, 1350])
column_1.transformation = Translation.from_vector([-3000, 3000, 1350])
column_2.transformation = Translation.from_vector([3000, 3000, 1350])
column_3.transformation = Translation.from_vector([3000, -3000, 1350])
beam_0.transformation = Translation.from_vector([0, -3000, 2850]) * Rotation.from_axis_and_angle([0, 0, 1], pi / 2)
beam_1.transformation = Translation.from_vector([-3000, 0, 2850])
beam_2.transformation = Translation.from_vector([0, 3000, 2850]) * Rotation.from_axis_and_angle([0, 0, 1], pi / 2)
beam_3.transformation = Translation.from_vector([3000, 0, 2850])
slab.transformation = Translation.from_vector([0, 0, 2850])

model.add_element(column_head_0)
model.add_element(column_head_1)
model.add_element(column_head_2)
model.add_element(column_head_3)
model.add_element(column_0)
model.add_element(column_1)
model.add_element(column_2)
model.add_element(column_3)
model.add_element(beam_0)
model.add_element(beam_1)
model.add_element(beam_2)
model.add_element(beam_3)
model.add_element(slab)

model.add_interaction(column_head_0, column_0, interaction=Interaction(name="column_head_0_&_column_0"))
model.add_interaction(column_head_0, beam_0, interaction=Interaction(name="column_head_0_&_beam_0"))
model.add_interaction(column_head_0, beam_1, interaction=Interaction(name="column_head_0_&_beam_1"))
model.add_interaction(column_head_0, slab, interaction=Interaction(name="column_head_0_&_slab"))

model.add_interaction(column_head_1, column_1, interaction=Interaction(name="column_head_1_&_column_1"))
model.add_interaction(column_head_1, beam_1, interaction=Interaction(name="column_head_1_&_beam_1"))
model.add_interaction(column_head_1, beam_2, interaction=Interaction(name="column_head_1_&_beam_2"))
model.add_interaction(column_head_1, slab, interaction=Interaction(name="column_head_1_&_slab"))

model.add_interaction(column_head_2, column_2, interaction=Interaction(name="column_head_2_&_column_2"))
model.add_interaction(column_head_2, beam_2, interaction=Interaction(name="column_head_2_&_beam_2"))
model.add_interaction(column_head_2, beam_3, interaction=Interaction(name="column_head_2_&_beam_3"))
model.add_interaction(column_head_2, slab, interaction=Interaction(name="column_head_2_&_slab"))

model.add_interaction(column_head_3, column_3, interaction=Interaction(name="column_head_3_&_column_3"))
model.add_interaction(column_head_3, beam_3, interaction=Interaction(name="column_head_3_&_beam_3"))
model.add_interaction(column_head_3, beam_0, interaction=Interaction(name="column_head_3_&_beam_0"))
model.add_interaction(column_head_3, slab, interaction=Interaction(name="column_head_3_&_slab"))

for element in model.elements():
    element.modelgeometry

column_head_0.is_dirty = True

for element in model.elements():
    print(element.is_dirty)

viewer = Viewer()
for element in model.elements():
    viewer.scene.add(element.modelgeometry)
viewer.show()
