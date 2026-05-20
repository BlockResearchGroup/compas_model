from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Polyhedron


def is_box_box_collision(A: Box, B: Box) -> bool:
    raise NotImplementedError


def is_polyhedron_polyhedron_collision(A: Polyhedron, B: Polyhedron) -> bool:
    raise NotImplementedError


def is_mesh_mesh_collision(A: Mesh, B: Mesh) -> bool:
    raise NotImplementedError


def is_brep_brep_collision(A: Brep, B: Brep) -> bool:
    raise NotImplementedError
