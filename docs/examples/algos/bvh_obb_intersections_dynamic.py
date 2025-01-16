import compas
from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Point
from compas_model.datastructures import BVH
from compas_model.datastructures import OBBNode
from compas_model.geometry import intersection_ray_triangle
from compas_viewer import Viewer

mesh = Mesh.from_obj(compas.get("tubemesh.obj"))

trimesh: Mesh = mesh.copy()
trimesh.quads_to_triangles()

tree = BVH.from_mesh(trimesh, nodetype=OBBNode)

line = Line.from_point_and_vector([2, 0, 0], [0, 0, 3])

# =============================================================================
# Viz
# =============================================================================

viewer = Viewer()
viewer.renderer.camera.target = [2.3, 1.8, 1.4]
viewer.renderer.camera.position = [5.2, -2.8, 4.4]

viewer.scene.add(mesh)
line_obj = viewer.scene.add(line, linecolor=Color.blue(), linewidth=2)


@viewer.on(interval=100, frames=60)
def update(frame):
    line.translate((0, 0.1, 0))

    for node in tree.intersect_line(line):
        if node.is_leaf:
            triangle = node.objects[0][2]
            result = intersection_ray_triangle(line, triangle)
            if result:
                o1 = viewer.scene.add(node.box, facecolor=Color.green(), opacity=0.5)
                o2 = viewer.scene.add(Point(*result), pointcolor=Color.red())
                o1.init()
                o2.init()

    line_obj.init()  # otherwise the last transformation is only applied when clicking the window
    line_obj.update()


viewer.show()
