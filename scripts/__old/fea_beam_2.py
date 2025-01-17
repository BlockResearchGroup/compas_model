import pathlib

import compas_fea2
from compas.colors import ColorMap
from compas.geometry import Box
from compas_fea2.model import DeformablePart
from compas_fea2.model import ElasticIsotropic
from compas_fea2.model import Model
from compas_fea2.model import SolidSection
from compas_fea2.problem import FieldOutput
from compas_fea2.problem import LoadCombination
from compas_fea2.units import units
from compas_gmsh.models import MeshModel

here = pathlib.Path(__file__).parent
temp = here / "temp"
temp.mkdir(exist_ok=True)

compas_fea2.set_backend("compas_fea2_opensees")
units = units("SI_mm")

model = Model()

material = ElasticIsotropic(E=30 * units.GPa, v=0.17, density=2350 * units("kg/m**3"))
section = SolidSection(material)

beam = Box(xsize=6000, ysize=200, zsize=400).to_mesh()
beam.translate([3000, 0, 0])

meshmodel: MeshModel = MeshModel.from_mesh(beam)
meshmodel.options.mesh.meshsize_max = 400
meshmodel.generate_mesh(3)

part = DeformablePart.from_gmsh(meshmodel, section=section)

nodes = []
for node in part.nodes:
    if node.x == 0:
        nodes.append(node)

model.add_part(part)
model.add_fix_bc(nodes=nodes)

# model.summary()
# model.show(draw_bcs=0.1, draw_nodes=False)

problem = model.add_problem(name="SLS")

step = problem.add_static_step()
step.combination = LoadCombination.SLS()
step.add_gravity_load_pattern([part], g=9.81 * units("m/s**2"), load_case="DL")
step.add_output(FieldOutput(node_outputs=["U", "RF"], element_outputs=["S3D"]))

model.analyse_and_extract(problems=[problem], path=str(temp), VERBOSE=True)

disp = problem.displacement_field
react = problem.reaction_field
stress = problem.stress_field

cmap = ColorMap.from_palette("davos")

problem.show_nodes_field_contour(disp, component=3, draw_reactions=0.01, draw_loads=0.1, draw_bcs=0.1, cmap=cmap)
# problem.show_nodes_field_vector(disp, component=3, scale_factor=1000, draw_bcs=0.1, draw_loads=0.1)
problem.show_deformed(scale_factor=10, draw_bcs=0.1, draw_loads=0.1)
problem.show_stress_contours(stress_type="von_mises_stress", side="top", draw_reactions=0.01, draw_loads=0.1, draw_bcs=0.1, cmap=cmap, bounds=[0, 0.5])
problem.show_elements_field_vector(stress, vector_sf=50, draw_bcs=0.1)
