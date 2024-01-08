from compas.scene import GeometryObject
from compas.scene import register
from compas.geometry import Box
from compas.scene import Scene


def fake_clear(self):
    pass


Scene.clear_objects = fake_clear  # overwrite the clear method


class CustomObject(GeometryObject):
    def draw(self):
        return []


box = Box.from_width_height_depth(1, 1, 1)
register(Box, CustomObject, context="Terminal")  # or any name you prefer


scene = Scene(context="Terminal")  # give the same context where you registered

customobj = scene.add(box)
scene.redraw()
