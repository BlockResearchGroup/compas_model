from compas.geometry import (
    Frame,
    Polygon,
    Plane,
    Transformation,
    transform_points,
    distance_point_point,
    Point,
    Vector,
    cross_vectors,
)
from math import fabs

try:
    from shapely.geometry import Polygon as ShapelyPolygon

    shapely_available = True
except ImportError:
    print("Shapely package is not available. Please install it.")
    shapely_available = False


def aabb_aabb(box0, box1):
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

    p0_0 = box0.xmin, box0.ymin, box0.zmin
    p0_1 = box0.xmax, box0.ymax, box0.zmax
    p1_0 = box1.xmin, box1.ymin, box1.zmin
    p1_1 = box1.xmax, box1.ymax, box1.zmax

    if p0_1[0] < p1_0[0] or p1_1[0] < p0_0[0]:
        return False

    if p0_1[1] < p1_0[1] or p1_1[1] < p0_0[1]:
        return False

    if p0_1[2] < p1_0[2] or p1_1[2] < p0_0[2]:
        return False

    return True


def box_box(box0, box1):
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
    # get separation plane
    def GetSeparatingPlane(RPos, axis, box0, box1):
        return abs(RPos.dot(axis)) > (
            abs((box0.frame.xaxis * box0.width * 0.5).dot(axis))
            + abs((box0.frame.yaxis * box0.depth * 0.5).dot(axis))
            + abs((box0.frame.zaxis * box0.height * 0.5).dot(axis))
            + abs((box1.frame.xaxis * box1.width * 0.5).dot(axis))
            + abs((box1.frame.yaxis * box1.depth * 0.5).dot(axis))
            + abs((box1.frame.zaxis * box1.height * 0.5).dot(axis))
        )

    # compute the obb collision
    RPos = box1.frame.point - box0.frame.point

    result = not (
        GetSeparatingPlane(RPos, box0.frame.xaxis, box0, box1)
        or GetSeparatingPlane(RPos, box0.frame.yaxis, box0, box1)
        or GetSeparatingPlane(RPos, box0.frame.zaxis, box0, box1)
        or GetSeparatingPlane(RPos, box1.frame.xaxis, box0, box1)
        or GetSeparatingPlane(RPos, box1.frame.yaxis, box0, box1)
        or GetSeparatingPlane(RPos, box1.frame.zaxis, box0, box1)
        or GetSeparatingPlane(
            RPos, box0.frame.xaxis.cross(box1.frame.xaxis), box0, box1
        )
        or GetSeparatingPlane(
            RPos, box0.frame.xaxis.cross(box1.frame.yaxis), box0, box1
        )
        or GetSeparatingPlane(
            RPos, box0.frame.xaxis.cross(box1.frame.zaxis), box0, box1
        )
        or GetSeparatingPlane(
            RPos, box0.frame.yaxis.cross(box1.frame.xaxis), box0, box1
        )
        or GetSeparatingPlane(
            RPos, box0.frame.yaxis.cross(box1.frame.yaxis), box0, box1
        )
        or GetSeparatingPlane(
            RPos, box0.frame.yaxis.cross(box1.frame.zaxis), box0, box1
        )
        or GetSeparatingPlane(
            RPos, box0.frame.zaxis.cross(box1.frame.xaxis), box0, box1
        )
        or GetSeparatingPlane(
            RPos, box0.frame.zaxis.cross(box1.frame.yaxis), box0, box1
        )
        or GetSeparatingPlane(
            RPos, box0.frame.zaxis.cross(box1.frame.zaxis), box0, box1
        )
    )

    return result


def face_to_face(polygons0, polygons1, tmax=1e-2, amin=1e1):
    """Construct interfaces by intersecting coplanar mesh faces.

    Parameters
    ----------
    assembly : compas_assembly.datastructures.Assembly
        An assembly of discrete blocks.
    nmax : int, optional
        Maximum number of neighbours per block.
    tmax : float, optional
        Maximum deviation from the perfectly flat interface plane.
    amin : float, optional
        Minimum area of a "face-face" interface.

    Returns
    -------
    Polygon of the Interface - :class:`compas.geometry.Polygon`
    Current Element ID - list[int]
    Other Element ID - list[int]
    Current Element Face Index - int
    Other Element Face Index - int
    """

    # --------------------------------------------------------------------------
    # sanity check
    # --------------------------------------------------------------------------
    if shapely_available is False:
        return []

    # --------------------------------------------------------------------------
    # iterate face polygons and get intersection area
    # DEPENDENCY: shapely library
    # --------------------------------------------------------------------------

    def to_shapely_polygon(matrix, polygon, tmax=1e-3, amin=1e-1):
        """convert a compas polygon to shapely polygon on xy plane"""

        # orient points to the xy plane
        projected = transform_points(polygon.points, matrix)
        # geometry.append(Polygon(projected))

        # check if the oriented point is on the xy plane within the tolerance
        # then return the shapely polygon
        if not all(fabs(point[2]) < tmax for point in projected):
            # for point in projected:
            #     print("tolerance is off " + str(fabs(point[2])) + " > " + str(tmax))
            print("to_shapely_polygon: tolerance is off")
            return None
        elif polygon.area < amin:
            print("area is off " + str(polygon.area) + " < " + str(amin))
            # print("area is off " + str(polygon.area) + " < " + str(amin))
            print("to_shapely_polygon: area is off")
            return None
        else:
            return ShapelyPolygon(projected)

    def to_compas_polygon(matrix, shapely_polygon):
        """convert a shapely polygon to compas polygon back to the frame"""

        # convert coordiantes to 3D by adding the z coordinate
        coords = [[x, y, 0.0] for x, y, _ in shapely_polygon.exterior.coords]

        # orient points to the original first mesh frame
        coords = transform_points(coords, matrix.inverted())[:-1]

        # convert to compas polygon
        return Polygon(coords)

    def is_coplanar(frame0, frame1, t_normal_colinearity=1e-1, t_dist_frames=1e-1):
        """check if two frames are coplanar and at the same position"""

        # get the normal vector of the first frame
        normal0 = frame0.normal

        # get the normal vector of the second frame
        normal1 = frame1.normal

        cross_product = normal0.cross(normal1)

        # check if the two normal vectors are parallel
        are_parellel = abs(cross_product.length) < t_normal_colinearity

        # are planes at the same positions?
        plane = Plane(frame0.point, frame0.normal)
        projected_point = plane.projected_point(frame1.point)
        are_close = distance_point_point(projected_point, frame1.point) < t_dist_frames
        return are_parellel and are_close

    def get_average_frame(polygon):
        # --------------------------------------------------------------------------
        # number of points
        # --------------------------------------------------------------------------
        points = list(polygon.points)
        n = len(points)

        # --------------------------------------------------------------------------
        # origin
        # --------------------------------------------------------------------------
        origin = Point(0, 0, 0)
        for point in points:
            origin = origin + point
        origin = origin / n

        # --------------------------------------------------------------------------
        # xaxis
        # --------------------------------------------------------------------------
        xaxis = points[1] - points[0]
        xaxis.unitize()

        # --------------------------------------------------------------------------
        # zaxis
        # --------------------------------------------------------------------------
        zaxis = Vector(0, 0, 0)

        for i in range(n):
            prev_id = ((i - 1) + n) % n
            next_id = ((i + 1) + n) % n
            zaxis = zaxis + cross_vectors(
                points[i] - points[prev_id],
                points[next_id] - points[i],
            )

        zaxis.unitize()

        # --------------------------------------------------------------------------
        # yaxis
        # --------------------------------------------------------------------------
        yaxis = cross_vectors(zaxis, xaxis)

        # --------------------------------------------------------------------------
        # frame
        # --------------------------------------------------------------------------
        frame = Frame(origin, xaxis, yaxis)

        return frame

    frames0 = [
        get_average_frame(polygon) for polygon in polygons0
    ]  # this better must be done for all elements
    frames1 = [get_average_frame(polygon) for polygon in polygons1]
    interfaces = []

    for id_0, face_polygon_0 in enumerate(polygons0):

        # get the transformation matrix
        matrix = Transformation.from_frame_to_frame(
            frames0[id_0].copy(), Frame.worldXY()
        )

        # get the shapely polygon
        shapely_polygon_0 = to_shapely_polygon(matrix, face_polygon_0, tmax, amin)
        if shapely_polygon_0 is None:
            # print(face_polygon_0)
            # print(element0.face_frames[id_0])
            # ca2.global_geometry.append(face_polygon_0)
            # ca2.global_geometry.append(element0.face_frames[id_0])
            print("WARNING: shapely_polygon_0 is None, frame or polygon is bad")
            continue

        for id_1, face_polygon_1 in enumerate(polygons1):

            if is_coplanar(frames0[id_0], frames1[id_1]) is False:
                continue

            # print(id_0, id_1)

            # get the shapely polygon
            shapely_polygon_1 = to_shapely_polygon(matrix, face_polygon_1, tmax, amin)
            if shapely_polygon_1 is None:
                # print("WARNING: shapely_polygon_1 is None, frame or polygon is bad")
                continue

            # check if polygons intersect
            if not shapely_polygon_0.intersects(shapely_polygon_1):
                # print("shapely_polygon_0.intersects(shapely_polygon_1)")
                continue

            # get intersection area and check if it is big enough within the given tolerance
            intersection = shapely_polygon_0.intersection(shapely_polygon_1)
            area = intersection.area
            if area < amin:
                # print("area is off " + str(area) + " < " + str(amin))
                continue

            # convert shapely polygon to compas polygon
            polygon = to_compas_polygon(matrix, intersection)

            interfaces.append([(id_0, id_1), polygon])

    # output
    return interfaces


def get_collision_pairs(
    model,
    aabb_and_obb_infliation=0.01,
    obb_obb=True,
    face_to_face=True,
    tmax=1e-2,
    amin=1e1,
):
    # ==========================================================================
    # SIMPLE FOR LOOP
    # ==========================================================================
    elements = model.elements_list

    for e in elements:
        e.compute_aabb(aabb_and_obb_infliation)
        e.compute_obb(aabb_and_obb_infliation)

    collision_pairs = []
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            if aabb_aabb(elements[i].aabb, elements[j].aabb):
                if not obb_obb or box_box(elements[i].obb, elements[j].obb):
                    if not face_to_face:
                        collision_pairs.append([i, j])
                    else:
                        interfaces = face_to_face(
                            elements[i].face_polygons,
                            elements[j].face_polygons,
                            tmax,
                            amin,
                        )
                        if interfaces:
                            result = [i, j]
                            result.append(interfaces)
                            collision_pairs.append(result)

    return collision_pairs
