from collections.abc import Iterable
from typing import Optional

from shapely import constrained_delaunay_triangles
from shapely.geometry import GeometryCollection as ShapelyGeometryCollection
from shapely.geometry import MultiPolygon as ShapelyMultiPolygon
from shapely.geometry import Polygon as ShapelyPolygon

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Geometry
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import bestfit_frame_numpy
from compas.geometry import transform_points
from compas.tolerance import TOL

from .bbox import aabb_from_points
from .bbox import pca_box


class NonCoplanarRegionsError(ValueError):
    """Error raised when planar-region operands do not share a plane."""


class PlanarRegion(Geometry):
    """A connected planar region with an exterior boundary and optional holes.

    Parameters
    ----------
    exterior
        The exterior boundary of the region.
    holes
        The interior boundaries of the region.
    frame
        The oriented plane of the region. If omitted, a best-fit frame is
        computed and aligned with the exterior polygon normal.
    name
        A human-readable name.

    Raises
    ------
    ValueError
        If a boundary is degenerate, the boundaries are not coplanar, or they
        do not form a valid positive-area polygonal region.

    Notes
    -----
    The exterior is oriented with the frame normal. Hole boundaries are
    oriented oppositely. Area is the exterior area minus all hole areas.

    """

    @property
    def __data__(self) -> dict:
        return {
            "exterior": self.exterior,
            "holes": self.holes,
            "frame": self.frame,
            "name": self.name,
        }

    def __init__(
        self,
        exterior: Polygon,
        holes: Optional[Iterable[Polygon]] = None,
        frame: Optional[Frame] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name)
        holes = list(holes or [])
        self._validate_loop(exterior, "exterior")
        for index, hole in enumerate(holes):
            self._validate_loop(hole, f"hole {index}")

        if frame is None:
            frame = Frame(*bestfit_frame_numpy(exterior.points))
            if frame.zaxis.dot(exterior.normal) < 0:
                frame.invert()

        self.frame = frame.copy()
        self.exterior = self._oriented_loop(exterior, matches_frame=True)
        self.holes = [self._oriented_loop(hole, matches_frame=False) for hole in holes]
        self._validate_region()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlanarRegion):
            return False
        return self.__data__ == other.__data__

    @staticmethod
    def _validate_loop(loop: Polygon, label: str) -> None:
        if len(loop.points) < 3:
            raise ValueError(f"The planar region {label} requires at least three points.")
        if loop.area <= 0:
            raise ValueError(f"The planar region {label} should have positive area.")

    def _oriented_loop(self, loop: Polygon, *, matches_frame: bool) -> Polygon:
        points = [point.copy() for point in loop.points]
        same_direction = loop.normal.dot(self.frame.zaxis) >= 0
        if same_direction is not matches_frame:
            points.reverse()
        return Polygon(points)

    def _to_local_points(self, points: Iterable[Point], tolerance: float) -> list[list[float]]:
        transformation = Transformation.from_change_of_basis(Frame.worldXY(), self.frame)
        local = transform_points(list(points), transformation)
        if any(abs(point[2]) > tolerance for point in local):
            raise NonCoplanarRegionsError("Planar region boundaries should be coplanar with the region frame.")
        return [[float(x), float(y), float(z)] for x, y, z in local]

    def _to_shapely(self, tolerance: Optional[float] = None) -> ShapelyPolygon:
        tolerance = TOL.absolute if tolerance is None else tolerance
        exterior = [(x, y) for x, y, _ in self._to_local_points(self.exterior.points, tolerance)]
        holes = [[(x, y) for x, y, _ in self._to_local_points(hole.points, tolerance)] for hole in self.holes]
        return ShapelyPolygon(exterior, holes=holes)

    def _validate_region(self) -> None:
        polygon = self._to_shapely()
        if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
            raise ValueError("The planar region boundaries should form a valid positive-area polygon.")

    @property
    def area(self) -> float:
        """float: The net area after subtracting holes."""
        return self._to_shapely().area

    @property
    def centroid(self) -> Point:
        """Point: The area centroid of the region."""
        centroid = self._to_shapely().centroid
        transformation = Transformation.from_change_of_basis(Frame.worldXY(), self.frame).inverted()
        return Point(centroid.x, centroid.y, 0).transformed(transformation)

    @property
    def points(self) -> list[Point]:
        """list[Point]: All exterior and hole boundary points."""
        return [*self.exterior.points, *(point for hole in self.holes for point in hole.points)]

    def compute_aabb(self) -> Box:
        """Compute the axis-aligned bounding box of the region."""
        return aabb_from_points(self.points)

    def compute_obb(self) -> Box:
        """Compute a principal-component oriented bounding box of the region."""
        return pca_box(self.points)

    def to_mesh(self) -> Mesh:
        """Convert the region to a triangle mesh while preserving holes.

        Returns
        -------
        Mesh
            A constrained Delaunay triangulation of the region.

        """
        triangulation = constrained_delaunay_triangles(self._to_shapely())
        transformation = Transformation.from_change_of_basis(Frame.worldXY(), self.frame).inverted()
        polygons = [_polygon_from_ring(triangle.exterior.coords, transformation) for triangle in _polygon_components(triangulation)]
        return Mesh.from_polygons(polygons)

    def transform(self, transformation: Transformation) -> None:
        """Transform the region and its oriented plane.

        Parameters
        ----------
        transformation
            The transformation to apply.

        """
        self.exterior.transform(transformation)
        for hole in self.holes:
            hole.transform(transformation)
        self.frame.transform(transformation)
        self._aabb = None
        self._obb = None


def intersection_planar_region_planar_region(
    region_a: PlanarRegion,
    region_b: PlanarRegion,
    tolerance: float = 1e-6,
    minimum_area: float = 0.0,
) -> list[PlanarRegion]:
    """Compute the connected overlap regions of two coplanar planar regions.

    Parameters
    ----------
    region_a
        The first planar region. Its frame determines result orientation.
    region_b
        The second planar region.
    tolerance
        Maximum deviation from the plane of region_a.
    minimum_area
        Minimum net area of each returned connected component.

    Returns
    -------
    list[PlanarRegion]
        Connected positive-area intersection regions in deterministic order.
        Boundary-only intersection returns an empty list.

    Raises
    ------
    ValueError
        If a tolerance is negative or the regions are not coplanar within the
        requested tolerance.

    Notes
    -----
    The planar topology operation is performed by Shapely in the local XY
    coordinates of region_a. Results inherit the frame orientation of
    region_a and preserve all interior rings.

    """
    if tolerance < 0:
        raise ValueError("The tolerance should be greater than or equal to zero.")
    if minimum_area < 0:
        raise ValueError("The minimum area should be greater than or equal to zero.")

    polygon_a = region_a._to_shapely(tolerance=tolerance)
    exterior_b = region_a._to_local_points(region_b.exterior.points, tolerance)
    holes_b = [region_a._to_local_points(hole.points, tolerance) for hole in region_b.holes]
    polygon_b = ShapelyPolygon(
        [(x, y) for x, y, _ in exterior_b],
        holes=[[(x, y) for x, y, _ in hole] for hole in holes_b],
    )
    if not polygon_b.is_valid:
        raise ValueError("The second planar region is invalid in the shared plane.")

    intersection = polygon_a.intersection(polygon_b)
    polygons = _polygon_components(intersection)
    polygons.sort(key=lambda polygon: (*polygon.bounds, polygon.area))

    transformation = Transformation.from_change_of_basis(Frame.worldXY(), region_a.frame).inverted()
    regions = []
    for polygon in polygons:
        if polygon.area <= 0 or polygon.area < minimum_area:
            continue
        exterior = _polygon_from_ring(polygon.exterior.coords, transformation)
        holes = [_polygon_from_ring(interior.coords, transformation) for interior in polygon.interiors]
        region = PlanarRegion(exterior, holes=holes, frame=region_a.frame)
        frame = Frame(region.centroid, region_a.frame.xaxis, region_a.frame.yaxis)
        regions.append(PlanarRegion(exterior, holes=holes, frame=frame))
    return regions


def _polygon_components(geometry: object) -> list[ShapelyPolygon]:
    if isinstance(geometry, ShapelyPolygon):
        return [geometry]
    if isinstance(geometry, (ShapelyMultiPolygon, ShapelyGeometryCollection)):
        return [polygon for component in geometry.geoms for polygon in _polygon_components(component)]
    return []


def _polygon_from_ring(coordinates: Iterable[tuple[float, ...]], transformation: Transformation) -> Polygon:
    local = [Point(x, y, 0) for x, y, *_ in coordinates]
    return Polygon([point.transformed(transformation) for point in local[:-1]])
