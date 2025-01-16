import compas
from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Point
from compas_model.algorithms import BVH
from compas_model.algorithms import OBBNode
from compas_model.geometry import intersection_ray_triangle
from compas_viewer import Viewer
from compas_viewer.config import Config

mesh = Mesh.from_obj(compas.get("tubemesh.obj"))

# =============================================================================
# Build BVH
# =============================================================================

trimesh: Mesh = mesh.copy()
trimesh.quads_to_triangles()

tree = BVH.from_mesh(trimesh, nodetype=OBBNode)

# =============================================================================
# Intersections
# =============================================================================

lines = [Line.from_point_and_vector([2, i * 0.1, 0], [0, 0, 3]) for i in range(60)]

boxes = []
points = []

for line in lines:
    for node in tree.intersect_line(line):
        if node.is_leaf:
            triangle = node.objects[0][2]
            result = intersection_ray_triangle(line, triangle)
            if result:
                boxes.append(node.box)
                points.append(Point(*result))

# =============================================================================
# Viz
# =============================================================================

config = Config()
config.camera.target = [2.3, 1.8, 1.4]
config.camera.position = [5.2, -2.8, 4.4]

viewer = Viewer(config=config)

viewer.scene.add(mesh)
viewer.scene.add(lines, linecolor=Color.blue(), linewidth=2)
viewer.scene.add(boxes, facecolor=Color.green(), opacity=0.25)
viewer.scene.add(points, pointcolor=Color.red(), pointsize=10)

viewer.show()
