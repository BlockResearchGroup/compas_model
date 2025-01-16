from compas.colors import Color
from compas.geometry import Polygon
from compas_model.geometry import is_collision_poly_poly_xy
from compas_viewer import Viewer
from compas_viewer.config import Config

A = Polygon.from_rectangle([0, 0, 0], 1, 1)
B = Polygon.from_sides_and_radius_xy(5, 1).translated([2.5, 1, 0])

# it should be possible to set this on `viewer.config`
# however, for that to work, some of the attributes of the renderer and camera need to ba lazy-loaded
# (or to pass this to `Viewer(...)` as kwargs)
config = Config()
config.renderer.view = "top"
config.camera.target = [3, 2, 0]
config.camera.position = [3, 2, 5]

viewer = Viewer(config=config)
# this is a hack because otherwise the view of the scene is weird
viewer.renderer.camera.rotation.set(0, 0, 0, False)

# the lines of the object are not properly transformed
# therefore turn lines off
A_obj = viewer.scene.add(A, facecolor=Color.red(), opacity=0.5, show_lines=False)
viewer.scene.add(B, facecolor=Color.blue(), opacity=0.5)

green = Color.green()
red = Color.red()


@viewer.on(interval=20, frames=40)
def update(frame):
    # translate the actual object
    # otherwisr the collision check makes no sense
    A.translate((0.1, 0, 0))

    A_obj.facecolor = green if is_collision_poly_poly_xy(A, B) else red
    A_obj.init()  # otherwise the last transformation is only applied when clicking the window
    A_obj.update()


viewer.show()
