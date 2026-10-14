from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from typing import Literal
from typing import Protocol
from typing import cast

import numpy as np
from numpy.typing import NDArray

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Polyline
from compas_model.geometry import triangulate_polygon_earcut

RenderRepresentation = Literal["mesh", "brep"]


class _ViewMeshBrep(Protocol):
    def to_viewmesh(
        self,
        linear_deflection: float | None = None,
        angular_deflection: float | None = None,
    ) -> tuple[Mesh, list[Polyline]]: ...


@dataclass(frozen=True, slots=True)
class RenderGeometry:
    """Backend-neutral, precomputed geometry for interactive rendering.

    Filled faces and visible lines are intentionally stored separately.
    Therefore, face-triangulation diagonals do not become displayed edges.

    Parameters
    ----------
    vertices
        Face vertices with shape ``(n, 3)``.
    triangles
        Triangle indices into ``vertices`` with shape ``(m, 3)``.
    line_vertices
        Explicit line-segment endpoints with shape ``(2k, 3)``.
    point_vertices
        Optional displayed points with shape ``(p, 3)``.
    representation
        Source geometry representation.

    """

    vertices: NDArray[np.float64]
    triangles: NDArray[np.int32]
    line_vertices: NDArray[np.float64]
    point_vertices: NDArray[np.float64]
    representation: RenderRepresentation

    def __post_init__(self) -> None:
        _validate_array(self.vertices, "vertices", columns=3)
        _validate_array(self.triangles, "triangles", columns=3)
        _validate_array(self.line_vertices, "line_vertices", columns=3)
        _validate_array(self.point_vertices, "point_vertices", columns=3)
        if len(self.line_vertices) % 2:
            raise ValueError("Line vertices should contain pairs of segment endpoints.")
        if self.triangles.size and (self.triangles.min() < 0 or self.triangles.max() >= len(self.vertices)):
            raise ValueError("Triangle indices should reference render vertices.")

    @property
    def face_vertices(self) -> NDArray[np.float64]:
        """NDArray[np.float64]: Triangle vertices expanded for GPU buffers."""
        return self.vertices[self.triangles].reshape((-1, 3))

    @property
    def backface_vertices(self) -> NDArray[np.float64]:
        """NDArray[np.float64]: Reversed triangle vertices for back faces."""
        return self.vertices[self.triangles[:, ::-1]].reshape((-1, 3))


def render_geometry_from_mesh(mesh: Mesh, tolerance: float = 1e-9) -> RenderGeometry:
    """Create render geometry from a mesh without displaying triangulation edges.

    Parameters
    ----------
    mesh
        Source mesh. It is not modified.
    tolerance
        Cleanup and validation tolerance used by polygon ear clipping.

    Returns
    -------
    RenderGeometry
        Triangulated faces and original mesh edges in separate buffers.

    """
    vertices: list[list[float]] = []
    triangles: list[tuple[int, int, int]] = []
    for face in mesh.faces():
        points = [_mesh_vertex_coordinates(mesh, vertex) for vertex in cast(Iterable[Any], mesh.face_vertices(face))]
        result = triangulate_polygon_earcut(points, tolerance=tolerance)
        offset = len(vertices)
        vertices.extend([list(point) for point in result.vertices])
        triangles.extend((a + offset, b + offset, c + offset) for a, b, c in result.triangles)

    line_vertices = [_mesh_vertex_coordinates(mesh, vertex) for edge in cast(Iterable[tuple[Any, Any]], mesh.edges()) for vertex in edge]
    point_vertices = [_mesh_vertex_coordinates(mesh, vertex) for vertex in cast(Iterable[Any], mesh.vertices())]
    return RenderGeometry(
        vertices=_float_array(vertices),
        triangles=_index_array(triangles),
        line_vertices=_float_array(line_vertices),
        point_vertices=_float_array(point_vertices),
        representation="mesh",
    )


def render_geometry_from_brep(
    brep: Brep,
    linear_deflection: float | None = None,
    angular_deflection: float | None = None,
) -> RenderGeometry:
    """Create render geometry from a BRep's native view-mesh infrastructure.

    Parameters
    ----------
    brep
        BRep providing a view mesh and sampled topological boundaries.
    linear_deflection
        Maximum linear tessellation deviation supported by the backend.
    angular_deflection
        Maximum angular tessellation deviation supported by the backend.

    Returns
    -------
    RenderGeometry
        Backend triangles and separately sampled BRep boundaries.

    Raises
    ------
    TypeError
        If the backend does not return a mesh and boundary polylines.

    """
    viewmesh, boundaries = cast(_ViewMeshBrep, brep).to_viewmesh(
        linear_deflection=linear_deflection,
        angular_deflection=angular_deflection,
    )
    if not isinstance(viewmesh, Mesh) or not all(isinstance(boundary, Polyline) for boundary in boundaries):
        raise TypeError("BRep.to_viewmesh() should return a Mesh and a list of boundary polylines.")

    raw_vertices, raw_triangles = viewmesh.to_vertices_and_faces(triangulated=True)
    vertices = [[float(coordinate) for coordinate in vertex] for vertex in cast(Iterable[Sequence[float]], raw_vertices)]
    triangles = [(int(face[0]), int(face[1]), int(face[2])) for face in raw_triangles]
    line_vertices = [list(point) for boundary in boundaries for line in boundary.lines for point in (line.start, line.end)]

    return RenderGeometry(
        vertices=_float_array(vertices),
        triangles=_index_array(triangles),
        line_vertices=_float_array(line_vertices),
        point_vertices=_float_array([list(point) for point in brep.points or []]),
        representation="brep",
    )


def _mesh_vertex_coordinates(mesh: Mesh, vertex: Any) -> list[float]:
    coordinates = mesh.vertex_coordinates(vertex)
    if coordinates is None:
        raise ValueError(f"Mesh vertex {vertex!r} has no coordinates.")
    return [float(coordinate) for coordinate in coordinates]


def _float_array(values: Iterable[Sequence[float]]) -> NDArray[np.float64]:
    return np.asarray(values, dtype=np.float64).reshape((-1, 3))


def _index_array(values: list[tuple[int, int, int]] | list[list[int]]) -> NDArray[np.int32]:
    return np.asarray(values, dtype=np.int32).reshape((-1, 3))


def _validate_array(array: NDArray[np.generic], name: str, columns: int) -> None:
    if array.ndim != 2 or array.shape[1] != columns:
        raise ValueError(f"Render geometry {name} should have shape (n, {columns}).")
