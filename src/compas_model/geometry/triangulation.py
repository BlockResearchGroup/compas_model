from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from math import sqrt

import mapbox_earcut
import numpy as np
from shapely.geometry import Polygon as ShapelyPolygon

from compas.geometry import Point


@dataclass(frozen=True, slots=True)
class EarcutResult:
    """Result of tolerance-aware polygon ear clipping.

    Parameters
    ----------
    vertices
        Cleaned three-dimensional polygon vertices. Exterior vertices are
        followed by the vertices of every hole.
    triangles
        Triangle indices into ``vertices``.
    ring_ends
        Exclusive end index of each ring in ``vertices``.

    """

    vertices: tuple[Point, ...]
    triangles: tuple[tuple[int, int, int], ...]
    ring_ends: tuple[int, ...]


def triangulate_polygon_earcut(
    exterior: Iterable[Sequence[float]],
    holes: Iterable[Iterable[Sequence[float]]] | None = None,
    tolerance: float = 1e-9,
) -> EarcutResult:
    """Triangulate a planar polygon with optional holes using Mapbox Earcut.

    Parameters
    ----------
    exterior
        Exterior polygon ring in three-dimensional coordinates.
    holes
        Optional interior polygon rings.
    tolerance
        Distance used to remove consecutive duplicate and collinear vertices
        before triangulation.

    Returns
    -------
    EarcutResult
        Cleaned vertices, triangle indices, and ring end indices.

    Raises
    ------
    ValueError
        If the tolerance is negative, a ring is degenerate, the projected
        polygon is invalid, or triangulation does not cover its area.

    Notes
    -----
    The rings are projected along the dominant component of the exterior's
    Newell normal. Mapbox Earcut accepts either winding direction. Its output
    is verified against the area of the projected Shapely polygon because
    Earcut prioritises practical robustness over guaranteed correctness for
    arbitrary invalid input.

    """
    if tolerance < 0:
        raise ValueError("The triangulation tolerance should be greater than or equal to zero.")

    rings = [_clean_ring(exterior, tolerance)]
    rings.extend(_clean_ring(hole, tolerance) for hole in holes or [])
    normal = _newell_normal(rings[0])
    normal_length = sqrt(sum(component * component for component in normal))
    if normal_length <= tolerance:
        raise ValueError("The polygon exterior is degenerate and has no stable projection plane.")

    drop_axis = max(range(3), key=lambda axis: abs(normal[axis]))
    projected_rings = [[_project(point, drop_axis) for point in ring] for ring in rings]
    polygon = ShapelyPolygon(projected_rings[0], holes=projected_rings[1:])
    if polygon.is_empty or not polygon.is_valid or polygon.area <= tolerance * tolerance:
        raise ValueError("The projected polygon should be valid and have positive area.")

    vertices = tuple(point for ring in rings for point in ring)
    projected = np.asarray([coordinates for ring in projected_rings for coordinates in ring], dtype=np.float64)
    ring_ends = tuple(_cumulative_lengths(rings))
    indices = mapbox_earcut.triangulate_float64(projected, np.asarray(ring_ends, dtype=np.uint32))
    triangles = tuple((int(indices[offset]), int(indices[offset + 1]), int(indices[offset + 2])) for offset in range(0, len(indices), 3))

    exterior_area = _signed_area(projected_rings[0])
    triangulation_area = sum(_signed_area([projected[a], projected[b], projected[c]]) for a, b, c in triangles)
    if exterior_area * triangulation_area < 0:
        triangles = tuple((a, c, b) for a, b, c in triangles)

    triangle_area = sum(abs(_signed_area([projected[a], projected[b], projected[c]])) for a, b, c in triangles)
    area_tolerance = max(tolerance * tolerance, polygon.area * 1e-9)
    if not triangles or abs(triangle_area - polygon.area) > area_tolerance:
        raise ValueError("Ear clipping did not produce a complete triangulation of the polygon.")

    return EarcutResult(vertices=vertices, triangles=triangles, ring_ends=ring_ends)


def _clean_ring(points: Iterable[Sequence[float]], tolerance: float) -> list[Point]:
    ring = [Point(*point[:3]) for point in points]
    if len(ring) > 1 and ring[0].distance_to_point(ring[-1]) <= tolerance:
        ring.pop()

    cleaned: list[Point] = []
    for point in ring:
        if not cleaned or point.distance_to_point(cleaned[-1]) > tolerance:
            cleaned.append(point)
    if len(cleaned) > 1 and cleaned[0].distance_to_point(cleaned[-1]) <= tolerance:
        cleaned.pop()

    changed = True
    while changed and len(cleaned) > 3:
        changed = False
        for index, point in enumerate(cleaned):
            previous = cleaned[index - 1]
            following = cleaned[(index + 1) % len(cleaned)]
            a = point - previous
            b = following - point
            cross_length = a.cross(b).length
            scale = max(a.length * b.length, 1.0)
            if cross_length <= tolerance * scale:
                del cleaned[index]
                changed = True
                break

    if len(cleaned) < 3:
        raise ValueError("Every polygon ring should contain at least three distinct non-collinear points.")
    return cleaned


def _newell_normal(points: Sequence[Point]) -> tuple[float, float, float]:
    x = y = z = 0.0
    for current, following in zip(points, [*points[1:], points[0]]):
        x += (current.y - following.y) * (current.z + following.z)
        y += (current.z - following.z) * (current.x + following.x)
        z += (current.x - following.x) * (current.y + following.y)
    return x, y, z


def _project(point: Point, drop_axis: int) -> tuple[float, float]:
    coordinates = [point.x, point.y, point.z]
    return tuple(coordinate for axis, coordinate in enumerate(coordinates) if axis != drop_axis)  # type: ignore[return-value]


def _cumulative_lengths(rings: Sequence[Sequence[Point]]) -> Iterable[int]:
    total = 0
    for ring in rings:
        total += len(ring)
        yield total


def _signed_area(points: Sequence[Sequence[float]]) -> float:
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, [*points[1:], points[0]]))
