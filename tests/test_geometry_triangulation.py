import pytest

from compas_model.geometry import triangulate_polygon_earcut


def triangle_area(vertices, triangle):
    a, b, c = [vertices[index] for index in triangle]
    return 0.5 * (b - a).cross(c - a).length


def test_earcut_triangulates_concave_polygon_with_either_winding():
    points = [(0, 0, 0), (3, 0, 0), (3, 3, 0), (2, 3, 0), (2, 1, 0), (1, 1, 0), (1, 3, 0), (0, 3, 0)]

    forward = triangulate_polygon_earcut(points)
    reverse = triangulate_polygon_earcut(reversed(points))

    assert sum(triangle_area(forward.vertices, triangle) for triangle in forward.triangles) == pytest.approx(7.0)
    assert sum(triangle_area(reverse.vertices, triangle) for triangle in reverse.triangles) == pytest.approx(7.0)
    assert all((forward.vertices[b] - forward.vertices[a]).cross(forward.vertices[c] - forward.vertices[a]).z > 0 for a, b, c in forward.triangles)
    assert all((reverse.vertices[b] - reverse.vertices[a]).cross(reverse.vertices[c] - reverse.vertices[a]).z < 0 for a, b, c in reverse.triangles)


def test_earcut_preserves_hole():
    result = triangulate_polygon_earcut(
        [(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)],
        holes=[[(-1, -1, 0), (-1, 1, 0), (1, 1, 0), (1, -1, 0)]],
    )

    assert result.ring_ends == (4, 8)
    assert sum(triangle_area(result.vertices, triangle) for triangle in result.triangles) == pytest.approx(12.0)


def test_earcut_removes_duplicate_and_collinear_points():
    result = triangulate_polygon_earcut([(0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0), (0, 1, 0), (0, 0, 0)])

    assert len(result.vertices) == 4
    assert len(result.triangles) == 2


@pytest.mark.parametrize(
    "points",
    [
        [],
        [(0, 0, 0), (1, 0, 0)],
        [(0, 0, 0), (1, 0, 0), (2, 0, 0)],
        [(0, 0, 0), (1, 1, 0), (0, 1, 0), (1, 0, 0)],
    ],
)
def test_earcut_rejects_degenerate_and_self_intersecting_polygons(points):
    with pytest.raises(ValueError):
        triangulate_polygon_earcut(points)


def test_earcut_rejects_negative_tolerance():
    with pytest.raises(ValueError, match="tolerance"):
        triangulate_polygon_earcut([(0, 0, 0), (1, 0, 0), (0, 1, 0)], tolerance=-1)
