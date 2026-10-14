from dataclasses import dataclass
from importlib import import_module
from math import isfinite
from typing import Any

from numpy import asarray

from compas.datastructures import Mesh


@dataclass(frozen=True)
class PreparedMeshCollision:
    """Prepared native representation of a mesh collision surface."""

    model: Any


def _backend() -> Any:
    try:
        return import_module("coal")
    except ImportError as error:
        raise ImportError(
            "Precise mesh collision detection requires the optional 'coal' backend. Install compas_model with the 'collision' extra or install Coal from conda-forge."
        ) from error


def prepare_mesh_collision(mesh: Mesh) -> PreparedMeshCollision:
    """Prepare a COMPAS mesh for repeated Coal collision queries.

    Parameters
    ----------
    mesh
        The mesh to convert.

    Returns
    -------
    PreparedMeshCollision
        The prepared collision surface containing a Coal ``BVHModelOBBRSS``.

    Raises
    ------
    ValueError
        If the mesh is empty, contains non-finite coordinates, or contains a
        degenerate triangle after triangulation.

    """
    coal = _backend()
    vertices, triangles = mesh.to_vertices_and_faces(triangulated=True)
    if not vertices or not triangles:
        raise ValueError("A mesh requires vertices and faces for precise collision detection.")
    if any(vertex is None for vertex in vertices) or any(triangle is None for triangle in triangles):
        raise ValueError("Mesh vertices and faces should be complete.")
    vertices = [vertex for vertex in vertices if vertex is not None]
    triangles = [triangle for triangle in triangles if triangle is not None]
    if any(not isfinite(coordinate) for vertex in vertices for coordinate in vertex):
        raise ValueError("Mesh vertex coordinates should be finite.")

    coal_vertices = coal.StdVec_Vec3s()
    for vertex in vertices:
        coal_vertices.append(asarray(vertex, dtype=float))

    coal_triangles = coal.StdVec_Triangle()
    for triangle in triangles:
        a, b, c = (vertices[index] for index in triangle)
        ab = [b[index] - a[index] for index in range(3)]
        ac = [c[index] - a[index] for index in range(3)]
        cross = [
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        ]
        if not any(component != 0.0 for component in cross):
            raise ValueError("Degenerate mesh triangles are not supported by the precise collision backend.")
        coal_triangles.append(coal.Triangle(*triangle))

    model = coal.BVHModelOBBRSS()
    if model.beginModel(len(triangles), len(vertices)) != 0:
        raise RuntimeError("Coal failed to begin construction of the mesh BVH.")
    if model.addSubModel(coal_vertices, coal_triangles) != 0:
        raise RuntimeError("Coal failed to add mesh data to the BVH.")
    if model.endModel() != 0:
        raise RuntimeError("Coal failed to complete construction of the mesh BVH.")
    return PreparedMeshCollision(model=model)


def is_prepared_mesh_mesh_collision(
    mesh_a: PreparedMeshCollision,
    mesh_b: PreparedMeshCollision,
    tolerance: float = 0.0,
) -> bool:
    """Test two prepared mesh surfaces for collision with Coal."""
    coal = _backend()
    request = coal.CollisionRequest()
    request.security_margin = tolerance
    result = coal.CollisionResult()
    coal.collide(mesh_a.model, coal.Transform3s(), mesh_b.model, coal.Transform3s(), request, result)
    return result.isCollision()


def is_mesh_mesh_collision_coal(mesh_a: Mesh, mesh_b: Mesh, tolerance: float = 0.0) -> bool:
    """Test two mesh surfaces for collision with Coal."""
    model_a = prepare_mesh_collision(mesh_a)
    model_b = prepare_mesh_collision(mesh_b)
    return is_prepared_mesh_mesh_collision(model_a, model_b, tolerance=tolerance)
