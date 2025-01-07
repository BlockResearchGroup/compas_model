from math import fabs

from shapely.geometry import Polygon as ShapelyPolygon

import compas_model.models  # noqa: F401
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.geometry import bestfit_plane
from compas.geometry import distance_point_point
from compas.geometry import transform_points


def get_separation_plane(relative_position: Vector, axis: Vector, box0: Box, box1: Box):
    return abs(relative_position.dot(axis)) > (
        abs((box0.frame.xaxis * box0.width * 0.5).dot(axis))
        + abs((box0.frame.yaxis * box0.depth * 0.5).dot(axis))
        + abs((box0.frame.zaxis * box0.height * 0.5).dot(axis))
        + abs((box1.frame.xaxis * box1.width * 0.5).dot(axis))
        + abs((box1.frame.yaxis * box1.depth * 0.5).dot(axis))
        + abs((box1.frame.zaxis * box1.height * 0.5).dot(axis))
    )


# NOTE: our default box is not super fast here
# because it will actually compute the min/max values
# we should consider making a dedicated object for this
def is_aabb_aabb_collision(box0: Box, box1: Box):
    """Verify if this axis-aligned bounding-box collides with another axis-aligned bounding-box.

    Parameters
    ----------
    box0 : :class:`compas.geometry.Box`
        First axis-aligned bounding-box.
    box1 : :class:`compas.geometry.Box`
        Second axis-aligned bounding-box.

    Returns
    -------
    bool
        True if the two axis-aligned bounding-box collide.
        False otherwise.

    """
    xmin0 = box0.xmin
    xmin1 = box1.xmin
    xmax0 = box0.xmax
    xmax1 = box1.xmax

    if xmax1 < xmin0 or xmax0 < xmin1:
        return False

    ymin0 = box0.ymin
    ymin1 = box1.ymin
    ymax0 = box0.ymax
    ymax1 = box1.ymax

    if ymax1 < ymin0 or ymax0 < ymin1:
        return False

    zmin0 = box0.zmin
    zmin1 = box1.zmin
    zmax0 = box0.zmax
    zmax1 = box1.zmax

    if zmax1 < zmin0 or zmax0 < zmin1:
        return False

    return True


def is_box_box_collision(box0: Box, box1: Box):
    """Verify if this box collides with another box.

    Parameters
    ----------
    box0 : :class:`compas.geometry.Box`
        First box.
    box1 : :class:`compas.geometry.Box`
        Second box.

    Returns
    -------
    bool
        True if the two boxes collide.
        False otherwise.

    """
    relative_position = box1.frame.point - box0.frame.point

    result = not (
        get_separation_plane(relative_position, box0.frame.xaxis, box0, box1)
        or get_separation_plane(relative_position, box0.frame.yaxis, box0, box1)
        or get_separation_plane(relative_position, box0.frame.zaxis, box0, box1)
        or get_separation_plane(relative_position, box1.frame.xaxis, box0, box1)
        or get_separation_plane(relative_position, box1.frame.yaxis, box0, box1)
        or get_separation_plane(relative_position, box1.frame.zaxis, box0, box1)
        or get_separation_plane(relative_position, box0.frame.xaxis.cross(box1.frame.xaxis), box0, box1)
        or get_separation_plane(relative_position, box0.frame.xaxis.cross(box1.frame.yaxis), box0, box1)
        or get_separation_plane(relative_position, box0.frame.xaxis.cross(box1.frame.zaxis), box0, box1)
        or get_separation_plane(relative_position, box0.frame.yaxis.cross(box1.frame.xaxis), box0, box1)
        or get_separation_plane(relative_position, box0.frame.yaxis.cross(box1.frame.yaxis), box0, box1)
        or get_separation_plane(relative_position, box0.frame.yaxis.cross(box1.frame.zaxis), box0, box1)
        or get_separation_plane(relative_position, box0.frame.zaxis.cross(box1.frame.xaxis), box0, box1)
        or get_separation_plane(relative_position, box0.frame.zaxis.cross(box1.frame.yaxis), box0, box1)
        or get_separation_plane(relative_position, box0.frame.zaxis.cross(box1.frame.zaxis), box0, box1)
    )

    return result


def is_face_to_face_collision(
    polygons0,
    polygons1,
    frames0=None,
    frames1=None,
    tolerance_flatness=1e-2,
    tolerance_area=1e1,
    log=False,
):
    """Construct interfaces by intersecting coplanar mesh faces.

    Parameters
    ----------
    assembly : compas_assembly.datastructures.Assembly
        An assembly of discrete blocks.
    nmax : int, optional
        Maximum number of neighbours per block.
    tolerance_flatness : float, optional
        Maximum deviation from the perfectly flat interface plane.
    tolerance_area : float, optional
        Minimum area of a "face-face" interface.
    log : bool, optional
        Log the conversion process, here the algorithms mostly fails due to user wrong inputs.

    Returns
    -------
    Polygon of the Interface - :class:`compas.geometry.Polygon`
    Current Element ID - list[int]
    Other Element ID - list[int]
    Current Element Face Index - int
    Other Element Face Index - int
    """

    _frames0 = frames0
    _frames1 = frames1

    if _frames0 is None and _frames1 is None:
        _frames0 = [Frame.from_plane(Plane(*bestfit_plane(polygon))) for polygon in polygons0]
        _frames1 = [Frame.from_plane(Plane(*bestfit_plane(polygon))) for polygon in polygons1]

    interfaces = []

    for id_0, face_polygon_0 in enumerate(polygons0):
        matrix = Transformation.from_frame_to_frame(_frames0[id_0].copy(), Frame.worldXY())

        shapely_polygon_0 = _to_shapely_polygon(matrix, face_polygon_0, tolerance_flatness, tolerance_area, log)
        if shapely_polygon_0 is None:
            if log:
                print("Collider -> is_face_to_face_collision -> shapely_polygon_0 is None, frame or polygon is bad")
            continue

        for id_1, face_polygon_1 in enumerate(polygons1):
            if _is_parallel_and_coplanar(_frames0[id_0], _frames1[id_1]) is False:
                continue

            shapely_polygon_1 = _to_shapely_polygon(matrix, face_polygon_1, tolerance_flatness, tolerance_area, log)
            if shapely_polygon_1 is None:
                continue

            if not shapely_polygon_0.intersects(shapely_polygon_1):
                continue

            intersection = shapely_polygon_0.intersection(shapely_polygon_1)
            area = intersection.area
            if area < tolerance_area:
                continue

            polygon = _to_compas_polygon(matrix, intersection)
            interfaces.append([(id_0, id_1), polygon])

    return interfaces


def _to_shapely_polygon(matrix, polygon, tolerance_flatness=1e-3, tolerance_area=1e-1, log=False):
    """Convert a compas polygon to shapely polygon on xy plane.

    Parameters
    ----------
    matrix : :class:`compas.geometry.Transformation`
        Transformation matrix to transform the polygon to the xy plane.
    polygon : :class:`compas.geometry.Polygon`
        Compas polygon.
    tolerance_flatness : float, optional
        Tolerance for the planarity of the polygon.
    tolerance_area : float, optional
        Tolerance for the area of the polygon.
    log : bool, optional
        Log the conversion process, here the algorithms mostly fails due to user wrong inputs.

    Returns
    -------
    :class:`shapely.geometry.Polygon`
        Shapely polygon on the xy plane.

    """

    # Orient points to the xy plane.
    projected = transform_points(polygon.points, matrix)

    # Check the planarity and the area of the polygon.
    if not all(fabs(point[2]) < tolerance_flatness for point in projected):
        if log:
            print("collider -> to_shapely_polygon: the polygon planarity is above the tolerance_flatness.")
        return None
    elif polygon.area < tolerance_area:
        if log:
            print(
                "collider -> is_face_to_face_collision -> "
                + "to_shapely_polygon: the polygon area is smaller than tolerance_area. "
                + str(polygon.area)
                + " < "
                + str(tolerance_area)
            )
        return None
    else:
        return ShapelyPolygon(projected)


def _to_compas_polygon(matrix, shapely_polygon):
    """Convert a shapely polygon to compas polygon back to the frame.

    Parameters
    ----------
    matrix : :class:`compas.geometry.Transformation`
        Transformation matrix to transform the polygon to the original frame.
    shapely_polygon : :class:`shapely.geometry.Polygon`
        Shapely polygon on the xy plane.

    Returns
    -------
    :class:`compas.geometry.Polygon`

    """

    coords = [[x, y, 0.0] for x, y, _ in shapely_polygon.exterior.coords]
    return Polygon(transform_points(coords, matrix.inverted())[:-1])


def _is_parallel_and_coplanar(
    frame0,
    frame1,
    tolerance_normal_colinearity=1e-1,
    tolerance_projection_distance=1e-1,
):
    """Check if two frames are coplanar and at the same position

    Parameters
    ----------
    frame0 : :class:`compas.geometry.Frame`
        First frame.
    frame1 : :class:`compas.geometry.Frame`
        Second frame.
    tolerance_normal_colinearity : float, optional
        Tolerance for the colinearity of the normals.
    tolerance_projection_distance : float, optional
        Tolerance for the distance between the projected points.

    Returns
    -------
    bool
        True if the two frames are coplanar and at the same position.
        False otherwise.

    """

    # Are the two normals are parallel?
    are_parellel = abs(frame0.normal.cross(frame1.normal).length) < tolerance_normal_colinearity

    # Are planes at the same positions?
    projected_point = Plane(frame0.point, frame0.normal).projected_point(frame1.point)
    are_close = distance_point_point(projected_point, frame1.point) < tolerance_projection_distance
    return are_parellel and are_close


def get_collision_pairs(
    model,
    aabb_and_obb_inflation=0.01,
    obb_obb=True,
    face_to_face=True,
    tolerance_flatness=1e-2,
    tolerance_area=1e1,
    log=False,
):
    # type: (compas_model.models.Model, float, bool, bool, float, float, bool) -> list
    """Get the collision pairs of the elements in the model.

    Parameters
    ----------
    model : :class:`compas_model.model.Model`
        Model of the assembly.
    aabb_and_obb_inflation : float, optional
        Inflation of the axis-aligned bounding-box and oriented bounding-box.
    obb_obb : bool, optional
        Verify the collision between oriented bounding-boxes.
    face_to_face : bool, optional
        Verify the collision between the faces of the elements.
    has_orientation : bool, optional
        Consider the polygon winding.
    tolerance_flatness : float, optional
        Maximum deviation from the perfectly flat interface plane.
    tolerance_area : float, optional
        Minimum area of a "face-face" interface.
    log : bool, optional
        Log the conversion process, here the algorithms mostly fails due to user wrong inputs.

    Returns
    -------
    list[[int, int, [(int, int), :class:`compas.geometry.Polygon`]]
        List of collision pairs. Each collision pair is a list of two element IDs and a list of interface polygons.

    """

    elements = list(model.elements())

    for e in elements:
        e.compute_aabb(aabb_and_obb_inflation)
        e.compute_obb(aabb_and_obb_inflation)

    collision_pairs = []
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            if not is_aabb_aabb_collision(elements[i].aabb, elements[j].aabb):
                continue

            if not obb_obb or is_box_box_collision(elements[i].obb, elements[j].obb):
                if not face_to_face:
                    collision_pairs.append([i, j])
                else:
                    interfaces = is_face_to_face_collision(
                        elements[i].face_polygons,
                        elements[j].face_polygons,
                        None,
                        None,
                        tolerance_flatness,
                        tolerance_area,
                        log,
                    )
                    if interfaces:
                        result = [i, j]
                        result.append(interfaces)
                        collision_pairs.append(result)

    return collision_pairs
