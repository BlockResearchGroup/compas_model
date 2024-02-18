import compas

from compas_model.model import Model
from compas_model.elements import Element
from compas_model.interactions import Interaction

from compas.datastructures import Mesh
from compas.geometry import Box

a = Element(geometry=Box(1))
b = Element(geometry=Mesh.from_meshgrid(dx=10, nx=10))
c = Element(geometry=None)

model = Model()

group = model.add_group(name="ab")

model.add_element(a, parent=group)
model.add_element(b, parent=group)
model.add_element(c)

model.add_interaction(a, c, interaction=Interaction())

# model.tree.print_hierarchy()
# model.graph.print_interactions()

s = compas.json_dumps(model)
m: Model = compas.json_loads(s)  # type: ignore

m.print()
