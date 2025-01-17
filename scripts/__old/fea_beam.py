import pathlib

import compas_fea2
from compas.colors import ColorMap
from compas.geometry import Line
from compas.itertools import pairwise
from compas_fea2.model import BeamElement
from compas_fea2.model import DeformablePart
from compas_fea2.model import ElasticIsotropic
from compas_fea2.model import Model
from compas_fea2.model import Node
from compas_fea2.model import RectangularSection
from compas_fea2.problem import FieldOutput
from compas_fea2.problem import LoadCombination
from compas_fea2.units import units
from compas_viewer import Viewer
from compas_viewer.components.renderer.camera import Position

compas_fea2.set_backend("compas_fea2_opensees")

here = pathlib.Path(__file__).parent
temp = here / "temp"
temp.mkdir(exist_ok=True)

units = units("SI_mm")

model = Model()

material = ElasticIsotropic(E=30 * units.GPa, v=0.17, density=2350 * units("kg/m**3"))
section = RectangularSection(w=200 * units.mm, h=400 * units.mm, material=material)

part = DeformablePart()

nodes = []
for x in range(11):
    node = Node([x * 1000, 0, 0])
    nodes.append(node)
part.add_nodes(nodes)

elements = []
for a, b in pairwise(nodes):
    element = BeamElement([a, b], section)
    elements.append(element)
part.add_elements(elements)

model.add_part(part)
model.add_fix_bc(nodes=nodes[:1])

# model.summary()
# model.show(draw_bcs=0.1)

problem = model.add_problem(name="SLS")

step = problem.add_static_step()
step.combination = LoadCombination.SLS()
step.add_gravity_load_pattern([part], g=9.81 * units("m/s**2"), load_case="DL")
step.add_output(FieldOutput(node_outputs=["U", "RF"], element_outputs=["S1D", "SF"]))

model.analyse_and_extract(problems=[problem], path=str(temp), VERBOSE=True)

# disp = problem.displacement_field
# react = problem.reaction_field
# stress = problem.stress_field

step = problem.steps_order[-1]

lines = []
for result in problem.displacement_field.results(step):
    # print(result.u1)
    # print(result.u2)
    # print(result.u3)
    # print(result.vector)
    # print(result.location.point)
    lines.append(Line.from_point_and_vector(result.location.point, result.vector * 10))


viewer = Viewer()
viewer.renderer.camera.near = 1e0
viewer.renderer.camera.far = 1e5
viewer.renderer.camera.pan_delta = 100
viewer.renderer.camera.position = Position((5000, -5000, 5000))
viewer.renderer.camera.target = Position((5000, 2000, 0))
viewer.renderer.config.gridsize = (20000, 20, 20000, 20)

viewer.show()
