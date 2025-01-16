from compas.colors import Color
from compas.geometry import Polygon
from compas_model.geometry import is_collision_poly_poly_xy
from compas_viewer import Viewer
from compas_viewer.config import Config

A = Polygon.from_rectangle([1, 0, 0], 1, 1)
B = Polygon.from_sides_and_radius_xy(5, 1).translated([2.5, 1, 0])

if is_collision_poly_poly_xy(A, B):
    A_color = Color.green()
    B_color = Color.green()
else:
    A_color = Color.red()
    B_color = Color.blue()

config = Config()
config.renderer.view = "top"
config.camera.target = [3, 2, 0]
config.camera.position = [3, 2, 5]

viewer = Viewer(config=config)
viewer.renderer.camera.rotation.set(0, 0, 0, False)
viewer.scene.add(A, facecolor=A_color, opacity=0.5)
viewer.scene.add(B, facecolor=B_color, opacity=0.5)
viewer.show()
