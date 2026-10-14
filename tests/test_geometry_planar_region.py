import pytest

from compas.data import json_dumps
from compas.data import json_loads
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Rotation
from compas.geometry import Translation
from compas.tolerance import TOL
from compas_model.geometry import PlanarRegion
from compas_model.geometry import intersection_planar_region_planar_region


def polygon_xy(points, z=0.0):
    return Polygon([Point(x, y, z) for x, y in points])


def test_planar_region_area_centroid_and_holes():
    exterior = polygon_xy([(0, 0), (4, 0), (4, 4), (0, 4)])
    hole = polygon_xy([(1, 1), (1, 2), (2, 2), (2, 1)])
    region = PlanarRegion(exterior, holes=[hole], frame=Frame.worldXY())

    assert TOL.is_close(region.area, 15.0)
    assert region.centroid == Point(61 / 30, 61 / 30, 0)
    assert region.exterior.normal.dot(region.frame.zaxis) > 0
    assert region.holes[0].normal.dot(region.frame.zaxis) < 0
    assert TOL.is_close(region.to_mesh().area(), region.area)


def test_planar_region_rejects_invalid_boundaries():
    exterior = polygon_xy([(0, 0), (2, 0), (2, 2), (0, 2)])
    outside_hole = polygon_xy([(3, 3), (4, 3), (4, 4), (3, 4)])
    noncoplanar_hole = polygon_xy([(0.5, 0.5), (1, 0.5), (1, 1), (0.5, 1)], z=0.1)

    with pytest.raises(ValueError, match="valid positive-area"):
        PlanarRegion(exterior, holes=[outside_hole], frame=Frame.worldXY())
    with pytest.raises(ValueError, match="coplanar"):
        PlanarRegion(exterior, holes=[noncoplanar_hole], frame=Frame.worldXY())


def test_planar_region_transforms_and_serializes():
    region = PlanarRegion(polygon_xy([(0, 0), (2, 0), (2, 1), (0, 1)]))
    transformation = Translation.from_vector([3, 4, 5]) * Rotation.from_axis_and_angle([1, 0, 0], 0.5)
    region.transform(transformation)
    restored = json_loads(json_dumps(region))

    assert isinstance(restored, PlanarRegion)
    assert TOL.is_close(restored.area, 2.0)
    assert all(abs(region.frame.to_local_coordinates(point).z) <= TOL.absolute for point in region.points)


def test_planar_region_intersection_preserves_holes():
    exterior = polygon_xy([(0, 0), (4, 0), (4, 4), (0, 4)])
    hole = polygon_xy([(1, 1), (1, 3), (3, 3), (3, 1)])
    region = PlanarRegion(exterior, holes=[hole], frame=Frame.worldXY())
    clip = PlanarRegion(polygon_xy([(0, 0), (4, 0), (4, 4), (0, 4)]), frame=Frame.worldXY())

    result = intersection_planar_region_planar_region(region, clip)

    assert len(result) == 1
    assert len(result[0].holes) == 1
    assert TOL.is_close(result[0].area, 12.0)
    assert TOL.is_close(result[0].to_mesh().area(), 12.0)


def test_planar_region_intersection_returns_multiple_components():
    u_shape = PlanarRegion(
        polygon_xy([(0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)]),
        frame=Frame.worldXY(),
    )
    bar = PlanarRegion(polygon_xy([(-1, 2), (4, 2), (4, 2.5), (-1, 2.5)]), frame=Frame.worldXY())

    result = intersection_planar_region_planar_region(u_shape, bar)

    assert len(result) == 2
    assert all(TOL.is_close(region.area, 0.5) for region in result)
    assert result[0].centroid.x < result[1].centroid.x


def test_planar_region_intersection_preserves_first_region_orientation_in_3d():
    region_a = PlanarRegion(polygon_xy([(0, 0), (2, 0), (2, 2), (0, 2)]), frame=Frame.worldXY())
    reversed_polygon = polygon_xy([(1, 1), (1, 3), (3, 3), (3, 1)])
    region_b = PlanarRegion(reversed_polygon, frame=Frame.worldXY())
    transformation = Translation.from_vector([2, 3, 4]) * Rotation.from_axis_and_angle([1, 1, 0], 0.7)
    region_a.transform(transformation)
    region_b.transform(transformation)

    result = intersection_planar_region_planar_region(region_a, region_b)

    assert len(result) == 1
    assert TOL.is_close(result[0].area, 1.0)
    assert result[0].frame.zaxis.dot(region_a.frame.zaxis) > 1 - TOL.relative
    assert all(abs(region_a.frame.to_local_coordinates(point).z) <= TOL.absolute for point in result[0].points)


def test_planar_region_intersection_filters_boundary_and_small_area():
    a = PlanarRegion(polygon_xy([(0, 0), (1, 0), (1, 1), (0, 1)]), frame=Frame.worldXY())
    touching = PlanarRegion(polygon_xy([(1, 0), (2, 0), (2, 1), (1, 1)]), frame=Frame.worldXY())
    overlap = PlanarRegion(polygon_xy([(0.9, 0), (2, 0), (2, 1), (0.9, 1)]), frame=Frame.worldXY())

    assert intersection_planar_region_planar_region(a, touching) == []
    assert intersection_planar_region_planar_region(a, overlap, minimum_area=0.2) == []


def test_planar_region_intersection_rejects_non_coplanar_input_and_invalid_options():
    a = PlanarRegion(polygon_xy([(0, 0), (1, 0), (1, 1), (0, 1)]), frame=Frame.worldXY())
    raised = PlanarRegion(polygon_xy([(0, 0), (1, 0), (1, 1), (0, 1)], z=0.01))

    with pytest.raises(ValueError, match="coplanar"):
        intersection_planar_region_planar_region(a, raised, tolerance=1e-3)
    with pytest.raises(ValueError, match="tolerance"):
        intersection_planar_region_planar_region(a, a, tolerance=-1)
    with pytest.raises(ValueError, match="minimum area"):
        intersection_planar_region_planar_region(a, a, minimum_area=-1)
