from collections.abc import Iterable
from typing import cast

from shapely import line_merge
from shapely import unary_union
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon as ShapelyPolygon

from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Polyline
from compas.geometry import Transformation
from compas.geometry import transform_points
from compas.tolerance import TOL

from .planar_region import PlanarRegion
from .section import ClipElementResult
from .section import SectionClassification
from .section import SectionElementResult


def section_mesh(
    mesh: Mesh,
    frame: Frame,
    source_guid: str,
    tolerance: float = 1e-6,
    minimum_area: float = 0.0,
) -> SectionElementResult:
    """Section a mesh with an oriented plane.

    Parameters
    ----------
    mesh
        The mesh to section. The input is not modified.
    frame
        The cutting-plane frame. Its Z axis points toward the front side.
    source_guid
        String representation of the source element GUID.
    tolerance
        Absolute distance used for plane classification and endpoint welding.
    minimum_area
        Minimum net area of returned closed section regions.
    Returns
    -------
    SectionElementResult
        Section faces, outlines, and source-geometry classification.

    Raises
    ------
    ValueError
        If an option is invalid or the mesh has no vertices.

    Notes
    -----
    Closed regions are reconstructed from welded triangle-plane segments using
    Shapely line merging and ring nesting. This function never clips the input
    mesh.

    """
    _validate_options(tolerance, minimum_area)
    vertices = cast(Iterable[int], mesh.vertices())
    distances = [_signed_distance(_mesh_vertex_point(mesh, vertex), frame) for vertex in vertices]
    if not distances:
        raise ValueError("Cannot section an empty mesh.")

    classification = _classify_distances(distances, tolerance)
    regions, open_curves = intersection_mesh_plane(mesh, frame, tolerance=tolerance, minimum_area=minimum_area)

    return SectionElementResult(
        source_guid=source_guid,
        classification=classification,
        representation="mesh",
        regions=regions,
        open_curves=open_curves,
    )


def clip_mesh(
    mesh: Mesh,
    frame: Frame,
    source_guid: str,
    tolerance: float = 1e-6,
    minimum_area: float = 0.0,
    cap: bool = True,
) -> ClipElementResult:
    """Clip a mesh and retain everything behind an oriented plane.

    Entirely-behind meshes are copied unchanged. Intersected closed meshes are
    capped when requested; open input meshes remain open.
    """
    complete_section = section_mesh(mesh, frame, source_guid, tolerance=tolerance, minimum_area=0.0)
    section = SectionElementResult(
        source_guid,
        cast(SectionClassification, complete_section.classification),
        "mesh",
        regions=[region for region in complete_section.regions if region.area >= minimum_area],
        open_curves=complete_section.open_curves,
    )
    vertices = cast(Iterable[int], mesh.vertices())
    distances = [_signed_distance(_mesh_vertex_point(mesh, vertex), frame) for vertex in vertices]
    has_front = any(distance > tolerance for distance in distances)
    has_behind = any(distance < -tolerance for distance in distances)
    geometry = None

    if section.classification == "behind" or (section.classification == "intersecting" and has_behind and not has_front):
        geometry = mesh
    elif section.classification == "intersecting" and has_behind:
        geometry = clip_mesh_halfspace(mesh, frame, side="behind", tolerance=tolerance)
        if cap and mesh.is_closed() and geometry is not None:
            _add_caps(geometry, complete_section.regions, reverse=True)
    return ClipElementResult(section, geometry)


def intersection_mesh_plane(
    mesh: Mesh,
    frame: Frame,
    tolerance: float = 1e-6,
    minimum_area: float = 0.0,
) -> tuple[list[PlanarRegion], list[Polyline]]:
    """Intersect a mesh with a plane and reconstruct closed and open curves.

    Parameters
    ----------
    mesh
        The input mesh.
    frame
        The oriented cutting-plane frame.
    tolerance
        Absolute plane and endpoint-welding tolerance.
    minimum_area
        Minimum net area of returned closed regions.

    Returns
    -------
    tuple[list[PlanarRegion], list[Polyline]]
        Closed section regions and unclosed intersection chains.

    """
    _validate_options(tolerance, minimum_area)
    vertices, faces = mesh.to_vertices_and_faces(triangulated=True)
    if not vertices:
        raise ValueError("Cannot intersect an empty mesh.")

    to_local = Transformation.from_change_of_basis(Frame.worldXY(), frame)
    to_world = to_local.inverted()
    local_vertices = transform_points(vertices, to_local)
    distances = [point[2] for point in local_vertices]
    weld_tolerance = tolerance if tolerance > 0 else TOL.absolute
    lines = []
    coplanar_polygons = []

    for face in faces:
        points = [[float(value) for value in local_vertices[index]] for index in face]
        face_distances = [distances[index] for index in face]
        if all(abs(distance) <= tolerance for distance in face_distances):
            coplanar_polygons.append(ShapelyPolygon([(point[0], point[1]) for point in points]))
            continue

        intersections = _triangle_plane_intersections(points, face_distances, tolerance)
        if len(intersections) == 2:
            a = _weld_xy(intersections[0], weld_tolerance)
            b = _weld_xy(intersections[1], weld_tolerance)
            if a != b:
                lines.append(LineString([a, b]))

    closed_polygons, open_lines = _assemble_lines(lines)
    polygonal = [*closed_polygons, *coplanar_polygons]
    merged = unary_union(polygonal) if polygonal else MultiPolygon([])
    regions = _regions_from_shapely(merged, frame, to_world, minimum_area, weld_tolerance)
    curves = [_polyline_from_linestring(line, to_world) for line in open_lines]
    curves.sort(key=lambda curve: tuple(curve.points[0]))
    return regions, curves


def reconstruct_planar_regions(
    polylines: Iterable[Polyline],
    frame: Frame,
    tolerance: float = 1e-6,
    minimum_area: float = 0.0,
) -> tuple[list[PlanarRegion], list[Polyline]]:
    """Reconstruct planar regions and open chains from unordered polylines.

    Parameters
    ----------
    polylines
        Curve approximations lying on the target plane.
    frame
        The oriented plane used for projection and region orientation.
    tolerance
        Absolute coplanarity and endpoint-welding tolerance.
    minimum_area
        Minimum net area of returned regions.

    Returns
    -------
    tuple[list[PlanarRegion], list[Polyline]]
        Closed nested regions and remaining open chains.

    Raises
    ------
    ValueError
        If options are invalid or a polyline deviates from the plane.

    """
    _validate_options(tolerance, minimum_area)
    weld_tolerance = tolerance if tolerance > 0 else TOL.absolute
    to_local = Transformation.from_change_of_basis(Frame.worldXY(), frame)
    to_world = to_local.inverted()
    lines = []
    for polyline in polylines:
        local = transform_points(polyline.points, to_local)
        if any(abs(point[2]) > tolerance for point in local):
            raise ValueError("Section polylines should lie on the reconstruction plane.")
        for a, b in zip(local, local[1:]):
            start = _weld_xy([float(value) for value in a], weld_tolerance)
            end = _weld_xy([float(value) for value in b], weld_tolerance)
            if start != end:
                lines.append(LineString([start, end]))

    polygons, opened = _assemble_lines(lines)
    merged = unary_union(polygons) if polygons else MultiPolygon([])
    regions = _regions_from_shapely(merged, frame, to_world, minimum_area, weld_tolerance)
    curves = [_polyline_from_linestring(line, to_world) for line in opened]
    curves.sort(key=lambda curve: tuple(curve.points[0]))
    return regions, curves


def clip_mesh_halfspace(
    mesh: Mesh,
    frame: Frame,
    side: str,
    tolerance: float = 1e-6,
) -> Mesh | None:
    """Clip a mesh to one half-space without modifying the input.

    Parameters
    ----------
    mesh
        The mesh to clip.
    frame
        The clipping-plane frame.
    side
        ``"front"`` for the positive half-space or ``"behind"`` for the
        negative half-space.
    tolerance
        Absolute distance treated as lying on the plane.

    Returns
    -------
    Mesh or None
        The uncapped clipped mesh, or ``None`` if no polygonal geometry remains.

    Raises
    ------
    ValueError
        If ``side`` is unsupported or tolerance is negative.

    """
    if side not in {"front", "behind"}:
        raise ValueError(f"Unsupported clipping side: {side!r}.")
    if tolerance < 0:
        raise ValueError("The tolerance should be greater than or equal to zero.")

    sign = 1.0 if side == "front" else -1.0
    polygons = []
    for face in mesh.faces():
        vertices = mesh.face_vertices(face)
        if vertices is None:
            continue
        points = [_mesh_vertex_point(mesh, vertex) for vertex in vertices]
        clipped = _clip_polygon(points, frame, sign, tolerance)
        if len(clipped) >= 3:
            polygons.append(Polygon(clipped))
    if not polygons:
        return None
    return Mesh.from_polygons(polygons)


def _validate_options(tolerance: float, minimum_area: float) -> None:
    if tolerance < 0:
        raise ValueError("The tolerance should be greater than or equal to zero.")
    if minimum_area < 0:
        raise ValueError("The minimum area should be greater than or equal to zero.")


def _signed_distance(point: Point, frame: Frame) -> float:
    return (point - frame.point).dot(frame.zaxis)


def _mesh_vertex_point(mesh: Mesh, vertex: int) -> Point:
    coordinates = mesh.vertex_coordinates(vertex)
    if coordinates is None:
        raise ValueError(f"Mesh vertex {vertex!r} has no coordinates.")
    return Point(*coordinates)


def _classify_distances(distances: list[float], tolerance: float) -> SectionClassification:
    front = any(distance > tolerance for distance in distances)
    behind = any(distance < -tolerance for distance in distances)
    coplanar = any(abs(distance) <= tolerance for distance in distances)
    if front and not behind and not coplanar:
        return "front"
    if behind and not front and not coplanar:
        return "behind"
    if coplanar and not front and not behind:
        return "coplanar"
    return "intersecting"


def _triangle_plane_intersections(
    points: list[list[float]],
    distances: list[float],
    tolerance: float,
) -> list[list[float]]:
    intersections = []
    for index, point_a in enumerate(points):
        point_b = points[(index + 1) % len(points)]
        distance_a = distances[index]
        distance_b = distances[(index + 1) % len(points)]
        on_a = abs(distance_a) <= tolerance
        on_b = abs(distance_b) <= tolerance
        if on_a:
            intersections.append([point_a[0], point_a[1], 0.0])
        if on_a or on_b or distance_a * distance_b >= 0:
            continue
        ratio = distance_a / (distance_a - distance_b)
        intersections.append(
            [
                point_a[0] + ratio * (point_b[0] - point_a[0]),
                point_a[1] + ratio * (point_b[1] - point_a[1]),
                0.0,
            ]
        )
    return _unique_points(intersections, tolerance)


def _unique_points(points: Iterable[list[float]], tolerance: float) -> list[list[float]]:
    unique = []
    threshold = tolerance if tolerance > 0 else TOL.absolute
    for point in points:
        if not any(Point(*point).distance_to_point(Point(*other)) <= threshold for other in unique):
            unique.append(point)
    return unique


def _weld_xy(point: list[float], tolerance: float) -> tuple[float, float]:
    return (round(point[0] / tolerance) * tolerance, round(point[1] / tolerance) * tolerance)


def _assemble_lines(lines: list[LineString]) -> tuple[list[ShapelyPolygon], list[LineString]]:
    if not lines:
        return [], []
    merged = line_merge(unary_union(lines))
    components = [merged] if isinstance(merged, LineString) else list(merged.geoms) if isinstance(merged, MultiLineString) else []
    closed = [line for line in components if line.is_ring]
    opened = [line for line in components if not line.is_ring]
    rings = [ShapelyPolygon(line.coords) for line in closed if ShapelyPolygon(line.coords).area > 0]
    polygons = []
    for index, ring in enumerate(rings):
        containers = [other for other_index, other in enumerate(rings) if other_index != index and other.contains(ring)]
        if len(containers) % 2:
            continue
        holes = [
            list(other.exterior.coords)
            for other_index, other in enumerate(rings)
            if other_index != index
            and ring.contains(other)
            and sum(candidate.contains(other) for candidate_index, candidate in enumerate(rings) if candidate_index not in {index, other_index} and ring.contains(candidate)) == 0
        ]
        polygons.append(ShapelyPolygon(ring.exterior.coords, holes=holes))
    return polygons, opened


def _regions_from_shapely(
    geometry: object,
    frame: Frame,
    to_world: Transformation,
    minimum_area: float,
    simplification: float,
) -> list[PlanarRegion]:
    if isinstance(geometry, ShapelyPolygon):
        polygons = [geometry]
    elif isinstance(geometry, MultiPolygon):
        polygons = list(geometry.geoms)
    else:
        polygons = []
    polygons.sort(key=lambda polygon: (*polygon.bounds, polygon.area))
    regions = []
    for polygon in polygons:
        simplified = polygon.simplify(simplification, preserve_topology=True)
        if not isinstance(simplified, ShapelyPolygon):
            continue
        polygon = simplified
        if polygon.area < minimum_area or polygon.area <= 0:
            continue
        exterior = _polygon_from_coordinates(polygon.exterior.coords, to_world)
        holes = [_polygon_from_coordinates(interior.coords, to_world) for interior in polygon.interiors]
        regions.append(PlanarRegion(exterior, holes=holes, frame=frame))
    return regions


def _polygon_from_coordinates(coordinates: Iterable[tuple[float, ...]], transformation: Transformation) -> Polygon:
    points = [Point(x, y, 0).transformed(transformation) for x, y, *_ in coordinates]
    return Polygon(points[:-1])


def _polyline_from_linestring(line: LineString, transformation: Transformation) -> Polyline:
    return Polyline([Point(x, y, 0).transformed(transformation) for x, y, *_ in line.coords])


def _clip_polygon(points: list[Point], frame: Frame, sign: float, tolerance: float) -> list[Point]:
    output = []
    for index, current in enumerate(points):
        previous = points[index - 1]
        current_distance = sign * _signed_distance(current, frame)
        previous_distance = sign * _signed_distance(previous, frame)
        current_inside = current_distance >= -tolerance
        previous_inside = previous_distance >= -tolerance
        if current_inside != previous_inside:
            denominator = current_distance - previous_distance
            ratio = current_distance / denominator
            intersection = current + (previous - current) * ratio
            intersection -= frame.zaxis * _signed_distance(intersection, frame)
            output.append(intersection)
        if current_inside:
            point = current.copy()
            if abs(_signed_distance(point, frame)) <= tolerance:
                point -= frame.zaxis * _signed_distance(point, frame)
            output.append(point)
    return output


def _add_caps(mesh: Mesh, regions: list[PlanarRegion], reverse: bool) -> None:
    for region in regions:
        cap = region.to_mesh()
        if reverse:
            cap.flip_cycles()
        mesh.join(cap, weld=True)
