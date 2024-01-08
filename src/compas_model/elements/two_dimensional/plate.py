from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_model.elements.element import Element
from collections import OrderedDict

from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Vector
from compas.geometry import Line
from compas.geometry import Polygon
from compas.geometry import Box
from compas.geometry import cross_vectors
from compas.geometry import Transformation, Translation
from compas.geometry import bounding_box
from compas.geometry import distance_point_point
from compas.geometry import intersection_plane_plane_plane
from compas.geometry import intersection_line_plane
from compas_model.elements.triangulator import Triagulator


class Plate(Element):
    """A plate is a surface element defined by a polygon and thickness.
    There are constructor overloads to create a plate from two polygons or from points and vectors.

    The two polygon representation has the following behavior:
        - The first polygon represents the base outline of the plate.
        - Two outline frames are computed from it, pointing outward.
        - The plate geometry is created by lofting the two outlines.
        - Holes are stored in `geometry_simplified` - central outline and `face_polygons`.

    The plate implementation is inspired by the compas_wood package:
    https://github.com/petrasvestartas/compas_wood/blob/main/src/frontend/src/wood/include/wood_element.h

    Parameters
    ----------
    polygon : :class:`compas.geometry.Polygon`
        The center outlines of the plate.
    thickness : float
        The thickness of the plate.
    compute_loft : bool, optional
        If True, mesh between the outlines is computed and assigned to the geometry attribute.
        If False, the geometry attribute is set to the top and bottom polygons.
        The loft operation is time expensive and often the top and bottom outline preview is enough.
    **kwargs
        Additional keyword arguments.

    Attributes
    ----------
    face_frames : list[:class:`compas.geometry.Frame`]
        The frames of the faces of the plate.
    face_polygons : list[:class:`compas.geometry.Polygon`]
        The outlines of the faces of the plate.
    top_and_bottom_polygons : list[:class:`compas.geometry.Polygon`]
        The top and bottom polygons of the plate. The first two items of face_polygons.
    thickness : float
        The thickness of the plate.
    joint_types_per_face : list[int]
        The joint types of the plate.
        The list has 2 + number of points of polygon0.
    insertion : list[:class:`compas.geometry.Vector`]
        The insertion vectors of the plate. The list has 2 + number of points of a polygon.
    joint_types_per_face : list
        The joint types of the plate. The list has 2 + number of points of a polygon.
    name : str
        Name of the element.
    frame : :class:`compas.geometry.Frame`
        Local coordinate of the object.
    geometry_simplified : Any
        Minimal geometrical represetation of an object. For example a :class:`compas.geometry.Polyline` that can represent: a point, a line or a polyline.
    geometry : Any
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    id : int
        Index of the object, default is -1.
    key : str
        Guid of the class object as a string.
    aabb : :class:`compas.geometry.Box`:
        Axis-aligned-bounding-box.
    oobb : :class:`compas.geometry.Box`:
        Object-oriented-bounding-box.
    center : :class:`compas.geometry.Point`
        The center of the element. Currently the center is computed from the axis-aligned-bounding-box.
    area : float
        The area of the geometry. Measurement is made from the ``geometry``.
    volume : float
        The volume of the geometry. Measurement is made from the ``geometry``.
    center_of_mass : :class:`compas.geometry.Point`
        The center of mass of the geometry. Measurement is made from the ``geometry``.
    centroid : :class:`compas.geometry.Point`
        The centroid of the geometry. Measurement is made from the ``geometry``.
    is_support : bool
        Indicates whether the element is a support.
    display_schema : dict
        Information which attributes are visible in the viewer and how they are visualized.

    """

    def __init__(self, polygon, thickness, compute_loft=True, **kwargs):
        # --------------------------------------------------------------------------
        # Safety check.
        # --------------------------------------------------------------------------
        if len(polygon.points) < 3:
            raise ValueError(
                "A polygon must have at least three points. No plate is created."
            )

        if not thickness:
            raise ValueError(
                "The thickness of the plate is not defined. No plate is created."
            )

        # --------------------------------------------------------------------------
        # Create geometry.
        # --------------------------------------------------------------------------
        frame = Plate._get_average_frame(polygon)

        polygon0 = polygon.copy()
        polygon1 = polygon.copy()
        polygon0.transform(Translation.from_vector(frame.zaxis * -0.5 * thickness))
        polygon1.transform(Translation.from_vector(frame.zaxis * 0.5 * thickness))
        geometry = (
            [Triagulator.from_loft_two_point_lists(polygon0, polygon1)[0]]
            if compute_loft
            else [polygon0, polygon1]
        )

        # --------------------------------------------------------------------------
        # Call the default Element constructor with the given parameters.
        # --------------------------------------------------------------------------
        super().__init__(
            name="plate",
            frame=frame,
            geometry_simplified=[polygon],
            geometry=geometry,
            copy_geometry=False,  # geometry is created by Triagulator
            **kwargs,
        )

        self._thickness = thickness

        # --------------------------------------------------------------------------
        # Set the face frames.
        # --------------------------------------------------------------------------
        frame0 = Frame(
            self.frame.point + self.frame.zaxis * -self.thickness * 0.5,
            self.frame.xaxis,
            -self.frame.yaxis,
        )
        frame1 = Frame(
            self.frame.point + self.frame.zaxis * self.thickness * 0.5,
            self.frame.xaxis,
            self.frame.yaxis,
        )

        face_frames = [frame0, frame1]

        n = len(self.geometry_simplified[0].points)
        for i in range(n):
            point = (
                self.geometry_simplified[0][i]
                + self.geometry_simplified[0][(i + 1) % n]
            ) * 0.5
            xaxis = (
                self.geometry_simplified[0][(i + 1) % n]
                - self.geometry_simplified[0][i]
            )
            yaxis = self.frame.zaxis
            face_frames.append(Frame(point, xaxis, yaxis))
        self.face_frames = face_frames

        # ------------------------------------------------------------------
        # Iterate neighboring side face_frames.
        # Then intersect them with the top and bottom frames.
        # ------------------------------------------------------------------
        n = len(self.geometry_simplified[0].points)
        points0 = []
        points1 = []
        side_frames = self.face_frames[2:]
        for i in range(n):
            plane0 = Plane.from_frame(self.face_frames[0])
            plane1 = Plane.from_frame(self.face_frames[1])
            plane2 = Plane.from_frame(side_frames[i])
            plane3 = Plane.from_frame(side_frames[(i + 1) % n])
            result0 = intersection_plane_plane_plane(plane0, plane2, plane3)
            result1 = intersection_plane_plane_plane(plane1, plane2, plane3)
            if result0 and result1:
                points0.append(result0)
                points1.append(result1)
            else:
                raise ValueError(
                    "Property top_and_bottom polygon using intersection_plane_plane_plane failed."
                )

        # --------------------------------------------------------------------------
        # Set the face outlines.
        # --------------------------------------------------------------------------
        self._face_polygons = [Polygon(points0), Polygon(points1)]

        n = len(self._face_polygons[0].points)
        for i in range(n):
            face_outline = Polygon(
                [
                    self._face_polygons[0][i],
                    self._face_polygons[0][(i + 1) % n],
                    self._face_polygons[1][(i + 1) % n],
                    self._face_polygons[1][i],
                ]
            )
            self._face_polygons.append(face_outline)

        self._aabb = []
        self._oobb = []

    @classmethod
    def from_two_polygons(cls, polygon0, polygon1, **kwargs):
        """Create a plate from two polygons.¨

        Parameters
        ----------
        polygon0 : :class:`compas.geometry.Polygon`
            The first outline of the plate.
        polygon1 : :class:`compas.geometry.Polygon`
            The second outline of the plate.
        **kwargs

        Returns
        -------
        :class:`compas_model.elements.Plate`

        """

        # --------------------------------------------------------------------------
        # Safety check.
        # --------------------------------------------------------------------------
        if len(polygon0.points) != len(polygon1.points):
            raise ValueError(
                "The polygon0 and polygon1 have different number of points. No plate is created."
            )

        if len(polygon0.points) < 3:
            raise ValueError(
                "A polygon must have at least three points. No plate is created."
            )

        # --------------------------------------------------------------------------
        # Create average polygon.
        # --------------------------------------------------------------------------
        average_polygon_points = []
        for i in range(len(polygon0.points)):
            average_polygon_points.append(
                (polygon0.points[i] + polygon1.points[i]) * 0.5
            )
        average_polygon = Polygon(average_polygon_points)

        # --------------------------------------------------------------------------
        # Create average frame for the second polygon to compute thickness.
        # --------------------------------------------------------------------------
        thickness = distance_point_point(
            polygon0[0],
            Plane.from_frame(Plate._get_average_frame(polygon1)).closest_point(
                polygon0[0]
            ),
        )

        # --------------------------------------------------------------------------
        # Create an empty object.
        # --------------------------------------------------------------------------
        plate = cls.__new__(cls)
        frame = Plate._get_average_frame(average_polygon)

        super(cls, plate).__init__(
            name="plate",
            frame=frame,
            geometry_simplified=[average_polygon],
            geometry=[Triagulator.from_loft_two_point_lists(polygon0, polygon1)[0]],
            copy_geometry=False,
            **kwargs,
        )

        plate.thickness = thickness

        # --------------------------------------------------------------------------
        # The polygon position in relation to plate must be constant.
        # --------------------------------------------------------------------------
        signed_distance0 = plate.frame.zaxis.dot(plate.frame.point - polygon0[0])

        top_and_bottom_polygons = (
            [polygon0.copy(), polygon1.copy()]
            if signed_distance0 > 0
            else [polygon1.copy(), polygon0.copy()]
        )

        # --------------------------------------------------------------------------
        # Set side frames.
        # --------------------------------------------------------------------------
        n = len(top_and_bottom_polygons[0].points)
        frame0 = Frame(
            plate.frame.point - plate.frame.zaxis * thickness * 0.5,
            plate.frame.xaxis,
            -plate.frame.yaxis,
        )
        frame1 = Frame(
            plate.frame.point + plate.frame.zaxis * thickness * 0.5,
            plate.frame.xaxis,
            plate.frame.yaxis,
        )
        face_frames = [frame0, frame1]
        for i in range(n):
            origin = (
                plate.geometry_simplified[0].points[i]
                + plate.geometry_simplified[0].points[(i + 1) % n]
            ) * 0.5
            xaxis = (
                plate.geometry_simplified[0].points[(i + 1) % n]
                - plate.geometry_simplified[0].points[i]
            )
            yaxis0 = (
                top_and_bottom_polygons[1].points[i] - top_and_bottom_polygons[0][i]
            )
            yaxis1 = (
                top_and_bottom_polygons[1].points[(i + 1) % n]
                - top_and_bottom_polygons[0].points[(i + 1) % n]
            )
            yaxis = yaxis0 + yaxis1
            face_frames.append(Frame(point=origin, xaxis=xaxis, yaxis=yaxis))
        plate.face_frames = face_frames

        # --------------------------------------------------------------------------
        # Set the face outlines.
        # --------------------------------------------------------------------------
        face_polygons = [
            top_and_bottom_polygons[0],
            top_and_bottom_polygons[1],
        ]

        for i in range(n):
            face_outline = Polygon(
                [
                    face_polygons[0][i],
                    face_polygons[0][(i + 1) % n],
                    face_polygons[1][(i + 1) % n],
                    face_polygons[1][i],
                ]
            )
            face_polygons.append(face_outline)
        plate.face_polygons = face_polygons

        return plate

    @classmethod
    def from_points_and_vectors(cls, points, vectors, thickness, offset=0.00, **kwargs):
        """Create a plate from points and vectors.

        Parameters
        ----------
        points : list[:class:`compas.geometry.Point`]
            The points of the plate.
        vectors : list[:class:`compas.geometry.Vector`]
            The vectors of the plate.
        thickness : float
            The thickness of the plate.
        offset : float
            Offset paramater moves the plate in the direction of the normal.
            Default is 0.00.
        **kwargs

        Returns
        -------
        :class:`compas_model.elements.Plate`

        """

        # --------------------------------------------------------------------------
        # Safety check.
        # --------------------------------------------------------------------------
        if len(points) != len(vectors):
            raise ValueError(
                "The points and vectors have different number of points. No plate is created."
            )

        if len(points) < 3:
            raise ValueError(
                "A polygon must have at least three points. No plate is created."
            )

        # --------------------------------------------------------------------------
        # Create an empty object.
        # --------------------------------------------------------------------------
        plate = cls.__new__(cls)

        polygon = Polygon(points)

        super(cls, plate).__init__(
            name="plate",
            frame=Plate._get_average_frame(polygon),
            geometry_simplified=None,
            geometry=None,
            copy_geometry=False,
            **kwargs,
        )

        plate.thickness = thickness

        # --------------------------------------------------------------------------
        # Set the top and bottom polygons.
        # First create a set of lines.
        # Then intersect them with the top and bottom frames.
        # Also update the frame the mid frame.
        # --------------------------------------------------------------------------
        n = len(points)

        plane0 = Plane(
            plate.frame.point + plate.frame.normal * offset, plate.frame.normal
        )
        plane1 = Plane(
            plate.frame.point + plate.frame.normal * (offset + thickness),
            plate.frame.normal,
        )

        points0 = []
        points1 = []
        points_mid = []
        for i in range(n):
            line = Line(points[i] - vectors[i], points[i] + vectors[i])
            result0 = intersection_line_plane(line, (plane0.point, plane0.normal))
            result1 = intersection_line_plane(line, (plane1.point, plane1.normal))
            if result0 and result1:
                p0 = Point(*result0)
                p1 = Point(*result1)
                points0.append(p0)
                points1.append(p1)
                points_mid.append((p0 + p1) * 0.5)
            else:
                raise ValueError(
                    "Property top_and_bottom polygon using intersection_line_plane failed."
                )

        plate.frame = Frame(
            (plane0.point + plane1.point) * 0.5, plate.frame.xaxis, plate.frame.yaxis
        )

        plate.geometry_simplified = [Polygon(points_mid)]

        # --------------------------------------------------------------------------
        # Set the side frames.
        # --------------------------------------------------------------------------
        frame0 = Frame(
            plate.frame.point - plate.frame.zaxis * thickness * 0.5,
            plate.frame.xaxis,
            -plate.frame.yaxis,
        )
        frame1 = Frame(
            plate.frame.point + plate.frame.zaxis * thickness * 0.5,
            plate.frame.xaxis,
            plate.frame.yaxis,
        )
        face_frames = [frame0, frame1]
        for i in range(n):
            origin = (points0[i] + points1[(i + 1) % n]) * 0.5
            xaxis = points0[(i + 1) % n] - points0[i]
            yaxis = points1[i] - points0[i]
            face_frames.append(Frame(point=origin, xaxis=xaxis, yaxis=yaxis))
        plate.face_frames = face_frames

        plate.geometry = [Triagulator.from_loft_two_point_lists(points0, points1)[0]]

        # --------------------------------------------------------------------------
        # Set the face outlines.
        # --------------------------------------------------------------------------
        face_polygons = [Polygon(points0), Polygon(points1)]

        for i in range(n):
            face_outline = Polygon(
                [
                    face_polygons[0][i],
                    face_polygons[0][(i + 1) % n],
                    face_polygons[1][(i + 1) % n],
                    face_polygons[1][i],
                ]
            )
            face_polygons.append(face_outline)
        plate.face_polygons = face_polygons

        return plate

    # ==========================================================================
    # Serialization
    # ==========================================================================

    @property
    def data(self):
        data = {
            "frame": self.frame,
            "geometry_simplified": self.geometry_simplified,
            "geometry": self.geometry,
            "thickness": self.thickness,
            "insertion": self.insertion,
            "joint_types_per_face": self.joint_types_per_face,
            "face_frames": self.face_frames,
            "face_polygons": self.face_polygons,
            "id": self.id,
            "is_support": self.is_support,
            # "attributes": self.attributes,
        }

        # TODO: REMOVE AFTER SCENE IS FULLY IMPLEMENTED
        data["display_schema"] = OrderedDict(self.display_schema.items())

        return data

    @classmethod
    def from_data(cls, data):
        obj = cls(
            data["geometry_simplified"][0],
            data["thickness"],
            False,
            # **data["attributes"],
        )

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # --------------------------------------------------------------------------
        obj.geometry_simplified = data["geometry_simplified"]
        obj.geometry = data["geometry"]
        obj.joint_types_per_face = data["joint_types_per_face"]
        obj.insertion = data["insertion"]
        obj.face_frames = data["face_frames"]
        obj.face_polygons = data["face_polygons"]
        obj.id = data["id"]
        obj.is_support = data["is_support"]

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def top_and_bottom_polygons(self):
        return [self.face_polygons[0], self.face_polygons[1]]

    @property
    def joint_types_per_face(self):
        if not hasattr(self, "_joint_types_per_face"):
            self._joint_types_per_face = []
            for _ in range(len(self.geometry_simplified[0].points) + 2):
                self._joint_types_per_face.append(0)
        return self._joint_types_per_face

    @joint_types_per_face.setter
    def joint_types_per_face(self, joint_types_per_face):
        if len(joint_types_per_face) != (len(self.geometry_simplified[0].points) + 2):
            raise ValueError(
                "The joint_types must have 2 + number of points of polygon0."
            )
        else:
            self._joint_types_per_face = joint_types_per_face

    @property
    def face_frames(self):
        return self._face_frames

    @face_frames.setter
    def face_frames(self, face_frames):
        self._face_frames = face_frames

    @property
    def face_polygons(self):
        return self._face_polygons

    @face_polygons.setter
    def face_polygons(self, face_polygons):
        self._face_polygons = face_polygons

    @property
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, thickness):
        self._thickness = thickness

    @property
    def display_schema(self):
        face_color = [0.9, 0.9, 0.9] if not self.is_support else [0.968, 0.615, 0.517]
        lines_weight = 5

        return OrderedDict(
            [
                ("geometry_simplified", {"show_faces": False, "is_visible": True}),
                (
                    "geometry",
                    {"facecolor": face_color, "opacity": 0.75, "is_visible": True},
                ),
                ("frame", {}),
                ("aabb", {"opacity": 0.25}),
                ("oobb", {"opacity": 0.25}),
                ("face_polygons", {"linewidth": lines_weight, "show_faces": False}),
                ("face_frames", {"linewidth": lines_weight}),
                (
                    "top_and_bottom_polygons",
                    {"linewidth": lines_weight, "show_faces": False},
                ),
            ]
        )

    # ==========================================================================
    # Methods, overriden from Element
    # ==========================================================================

    def compute_aabb(self, inflate=None):
        """Compute the axis-aligned bounding box of the polygon.

        Parameters
        ----------
        inflate : float, optional
            Move the box points outside by a given value.

        Returns
        -------
        list[:class:`compas.geometry.Point`] or None

        """

        self._inflate = inflate if inflate else 0.0

        # --------------------------------------------------------------------------
        # Get points from the top and bottom polygons.
        # --------------------------------------------------------------------------
        points = []
        points.extend(self.face_polygons[0].points)
        points.extend(self.face_polygons[1].points)

        # --------------------------------------------------------------------------
        # Compute the bounding box from the found points and inflate it.
        # The inflation is needed to avoid floating point errors.
        # Private variable _inflate is used to track it during transformation.
        # --------------------------------------------------------------------------
        points_bbox = bounding_box(points)

        self._aabb = Box.from_bounding_box(
            bounding_box(
                [
                    [
                        points_bbox[0][0] - self._inflate,
                        points_bbox[0][1] - self._inflate,
                        points_bbox[0][2] - self._inflate,
                    ],
                    [
                        points_bbox[6][0] + self._inflate,
                        points_bbox[6][1] + self._inflate,
                        points_bbox[6][2] + self._inflate,
                    ],
                ]
            )
        )

        return self._aabb

    def compute_oobb(self, inflate=None):
        """Get object-oriented-bounding-box from the longest edge in the polygon

        Parameters
        ----------
        inflate : float, optional
            Move the box points outside by a given value.

        Returns
        -------
        list[:class:`compas.geometry.Point`] or None

        """

        self._inflate = inflate if inflate else 0.0

        # --------------------------------------------------------------------------
        # Get points from the top and bottom polygons.
        # --------------------------------------------------------------------------
        points = []
        points.extend(self.face_polygons[0].points)
        points.extend(self.face_polygons[1].points)

        # --------------------------------------------------------------------------
        # Transform from the longest edge frame to XY frame and compute the bounding box.
        # --------------------------------------------------------------------------

        vector_length = 0
        vector = Vector(0, 0, 0)
        for i in range(len(self.geometry_simplified[0].points)):
            vector = (
                self.geometry_simplified[0].points[
                    (i + 1) % len(self.geometry_simplified[0].points)
                ]
                - self.geometry_simplified[0].points[i]
            )
            if vector.length > vector_length:
                vector_length = vector.length
                vector_longest = vector

        frame = Frame(
            self.frame.point, vector_longest, cross_vectors(vector, self.frame.zaxis)
        )
        xform = Transformation.from_frame_to_frame(frame, Frame.worldXY())
        xform_inv = xform.inverse()

        self._oobb = []
        for i in range(len(points)):
            point = Point(*points[i])
            point.transform(xform)
            self._oobb.append(point)
        self._oobb = bounding_box(self._oobb)

        # --------------------------------------------------------------------------
        # Inflate the box.
        # --------------------------------------------------------------------------
        self._oobb = Box.from_bounding_box(
            bounding_box(
                [
                    [
                        self._oobb[0][0] - self._inflate,
                        self._oobb[0][1] - self._inflate,
                        self._oobb[0][2] - self._inflate,
                    ],
                    [
                        self._oobb[6][0] + self._inflate,
                        self._oobb[6][1] + self._inflate,
                        self._oobb[6][2] + self._inflate,
                    ],
                ]
            )
        )

        # --------------------------------------------------------------------------
        # Orient the points back to the local frame.
        # --------------------------------------------------------------------------
        self._oobb.transform(xform_inv)

        return self._oobb

    def transform(self, transformation):
        """Transforms all the attrbutes of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to be applied to the Element's geometry and frames.

        Returns
        -------
        None

        """

        # --------------------------------------------------------------------------
        # main constructor properties
        # --------------------------------------------------------------------------
        self.frame.transform(transformation)
        [g.transform(transformation) for g in self.geometry_simplified]
        [g.transform(transformation) for g in self.geometry]
        [g.transform(transformation) for g in self.face_frames]
        [g.transform(transformation) for g in self.face_polygons]
        self.insertion.transform(transformation)

        self.compute_aabb()
        self.compute_oobb()

    # ==========================================================================
    # Methods, specific to this class
    # ==========================================================================
    def compute_loft(self):
        """Compute the mesh between the two outlines of the plate.

        Returns
        -------
        Mesh

        """

        self.geometry = [
            Triagulator.from_loft_two_point_lists(
                self.face_polygons[0].points, self.face_polygons[1].points
            )[0]
        ]
        return self.geometry[0]

    def add_holes(self, holes, add_frames=False):
        """Add holes to the plate.

        Parameters
        ----------
        holes : list[:class:`compas.geometry.Polygon`]
            The holes to be added to the plate.
        add_frames : bool, optional
            If True, the frames of the holes are added to the face_frames.

        Returns
        -------
        None

        """
        # --------------------------------------------------------------------------
        # Compare the winding of the polygon.
        # If the winding is different, reverse the polygon.
        # --------------------------------------------------------------------------

        xform = Transformation.from_frame_to_frame(self.frame, Frame.worldXY())

        holes_oriented = []
        for hole in holes:
            hole_xy = hole.transformed(xform)
            hole_copy = hole.copy()
            if self._is_counterclockwise(hole_xy):
                hole_copy.points.reverse()
            holes_oriented.append(hole_copy)

        # --------------------------------------------------------------------------
        # Add the holes to the geometry_simplified.
        # --------------------------------------------------------------------------
        self.geometry_simplified.extend(holes_oriented)

        # --------------------------------------------------------------------------
        # Add extruded holes to the face_polygons.
        # --------------------------------------------------------------------------
        for hole in holes_oriented:
            # top and the bottom polygon of the hole
            hole0 = hole.copy()
            hole0.transform(
                Translation.from_vector(self.frame.zaxis * -self.thickness * 0.5)
            )
            hole1 = hole.copy()
            hole1.transform(
                Translation.from_vector(self.frame.zaxis * self.thickness * 0.5)
            )

            # # update the face_frames
            # self.face_frames.append(self._get_average_frame(hole))
            self.face_polygons.append(hole0)
            self.face_polygons.append(hole1)

            # create sides
            n = len(hole.points)
            for i in range(n):
                self.face_polygons.append(
                    Polygon(
                        [
                            hole0[i],
                            hole0[(i + 1) % n],
                            hole1[(i + 1) % n],
                            hole1[i],
                        ]
                    )
                )

                # update the face_frames
                if add_frames:
                    origin = (hole0[i] + hole0[(i + 1) % n]) * 0.5
                    xaxis = hole0[(i + 1) % n] - hole0[i]
                    yaxis = hole1[i] - hole0[i]
                    self.face_frames.append(
                        Frame(point=origin, xaxis=xaxis, yaxis=yaxis)
                    )

        # --------------------------------------------------------------------------
        # Update the geometry.
        # --------------------------------------------------------------------------
        self.compute_loft()

    def add_top_and_bottom_holes(self, holes_pairs, add_frames=False):
        """Add holes to the top and bottom polygons of the plate.

        Parameters
        ----------
        holes : list[:class:`compas.geometry.Polygon`]
            The holes to be added to the plate.
        add_frames : bool, optional
            If True, the frames of the holes are added to the face_frames.

        Returns
        -------
        None

        """
        # --------------------------------------------------------------------------
        # Check if holes in a correct vertical order.
        # --------------------------------------------------------------------------
        xform = Transformation.from_frame_to_frame(self.frame, Frame.worldXY())
        for pair in range(0, len(holes_pairs), 2):
            hole0 = holes_pairs[pair].transformed(xform)
            hole1 = holes_pairs[pair + 1].transformed(xform)
            if hole0[0].z > hole1[0].z:
                holes_pairs[pair], holes_pairs[pair + 1] = (
                    holes_pairs[pair + 1],
                    holes_pairs[pair],
                )

        # --------------------------------------------------------------------------
        # Create middle polygon from the polygon pairs.
        # --------------------------------------------------------------------------
        holes = []
        for pair in range(0, len(holes_pairs), 2):
            hole0 = holes_pairs[pair]
            hole1 = holes_pairs[pair + 1]
            mid_points = []
            for i in range(len(hole0.points)):
                mid_points.append((hole0.points[i] + hole1.points[i]) * 0.5)
            holes.append(Polygon(mid_points))

        # --------------------------------------------------------------------------
        # Compare the winding of the polygon.
        # If the winding is different, reverse the polygon.
        # --------------------------------------------------------------------------

        holes_oriented = []
        for idx, hole in enumerate(holes):
            # center outline
            hole_copy = hole.copy()
            is_clockwise = self._is_counterclockwise(hole_copy.transformed(xform))
            if is_clockwise:
                hole_copy.points.reverse()
            holes_oriented.append(hole_copy)

            # pairs of top and bottom holes
            holes_pairs_0 = holes_pairs[idx * 2].copy()
            holes_pairs_1 = holes_pairs[idx * 2 + 1].copy()

            if is_clockwise:
                holes_pairs_0.points.reverse()
                holes_pairs_1.points.reverse()

            # update the face_frames
            # self.face_frames.append(self._get_average_frame(hole))
            self.face_polygons.append(holes_pairs_0)
            self.face_polygons.append(holes_pairs_1)

            # create sides
            n = len(hole.points)
            for i in range(n):
                self.face_polygons.append(
                    Polygon(
                        [
                            holes_pairs_0[i],
                            holes_pairs_0[(i + 1) % n],
                            holes_pairs_1[(i + 1) % n],
                            holes_pairs_1[i],
                        ]
                    )
                )

                # update the face_frames
                if add_frames:
                    origin = (holes_pairs_0[i] + holes_pairs_1[(i + 1) % n]) * 0.5
                    xaxis = holes_pairs_0[(i + 1) % n] - holes_pairs_0[i]
                    yaxis = holes_pairs_1[i] - holes_pairs_0[i]
                    self.face_frames.append(
                        Frame(point=origin, xaxis=xaxis, yaxis=yaxis)
                    )

        # --------------------------------------------------------------------------
        # Add the holes to the geometry_simplified.
        # --------------------------------------------------------------------------
        self.geometry_simplified.extend(holes_oriented)

    # ==========================================================================
    # Private methods
    # ==========================================================================

    @staticmethod
    def _get_average_frame(polygon):
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

    def _is_counterclockwise(self, polygon):
        """
        Check if a polygon on the XY plane is clockwise.

        Parameters:
        - polygon (compas.geometry.Polyline): The polyline to be checked.

        Returns:
        - bool: True if the polygon is clockwise, False otherwise.
        """
        sum_val = 0.0

        for i in range(len(polygon.points)):
            current_point = polygon.points[i]
            next_point = polygon.points[(i + 1) % len(polygon.points)]
            sum_val += (next_point.x - current_point.x) * (
                next_point.y + current_point.y
            )

        return sum_val < 0.0
