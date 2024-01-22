from compas_model.elements import Element
from compas.geometry import Point
from compas.geometry import Frame
from compas.geometry import Box
from compas.datastructures import Mesh

# ==============================================================================
# Element - one should not initialize this class, because it is only a template.
# Here we just test internal methods, by on purpose initializing private members.
# ==============================================================================
element = Element("element", Frame.worldXY(), geometry=Mesh.from_polyhedron(6), geometry_simplified=Point(0, 0, 0))
element._obb = Box.from_bounding_box(element.geometry.obb())
element._aabb = Box.from_bounding_box(element.geometry.aabb())
element._collision_mesh = element.geometry
