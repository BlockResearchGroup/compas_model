from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from copy import deepcopy

from compas_model.elements.element import Element
from compas_model.elements.element_type import ElementType
from collections import OrderedDict

import math

from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Vector
from compas.geometry import Polygon
from compas.geometry import add_vectors
from compas.geometry import angle_vectors
from compas.geometry import cross_vectors
from compas.geometry import dot_vectors
from compas.geometry import scale_vector
from compas.geometry import subtract_vectors
from compas.geometry import bounding_box
from compas.datastructures import Mesh

# TODO: REMOVE AFTER TOLERANCE IS FULLY IMPLEMENTED
ANGLE_TOLERANCE = 1e-3  # [radians]
DEFAULT_TOLERANCE = 1e-6


class Beam(Element):
    """A representation of a beam, where the center-line is the Frame X-Axis.

    It is very similar :class:`compas.geometry.Box` but with the following differences:
        - The beam is defined from the start of the center_axis, not from the center.
        - The beam can be extended along its axes or to a given plane.
        - The beam has a target frame and an axis, which can be used for fabrication or structural analysis.
        - The beam's simplified geometry is represented as an axis, and the full geometry is represented as a box mesh.
        - The adjacency (interfaces, joinery, etc.) must be stored within the model class.

    The implementation is inspired by the compas_timber beam class:
    https://github.com/gramaziokohler/compas_timber/blob/main/src/compas_timber/parts/beam.py

    Parameters
    ----------
    frame : :class:`compas.geometry.Frame`
        A local coordinate system of the beam:
        Origin is located at the starting point of the center_axis.
        x-axis corresponds to the center_axis (major axis), usually also the fibre direction in solid wood beams.
        y-axis corresponds to the width of the cross-section, usually the smaller dimension.
        z-axis corresponds to the height of the cross-section, usually the larger dimension.
    length : float
        Length of the beam.
    width : float
        Width of the cross-section.
    height : float
        Height of the cross-section.

    Attributes
    ----------
    frame : :class:`compas.geometry.Frame`
        The coordinate system (frame) of this beam.
    length : float
        Length of the beam.
    width : float
        Width of the cross-section
    height : float
        Height of the cross-section
    blank : :class:`compas.geometry.Box`
        A feature-less box representing the parametric geometry of this beam.
        This method is useful, when then beam geometry has been changed.
        For example when Boolean operations are applied to the beam.
    face_frames : list(:class:`compas.geometry.Frame`)
        A list of frames representing the 6 faces of this beam.
        0: +y (side's frame normal is equal to the beam's Y positive direction)
        1: +z
        2: -y
        3: -z
        4: -x (side at the starting end)
        5: +x (side at the end of the beam)
    face_outlines : list(:class:`compas.geometry.Polygon`)
        A list of polygons representing the 6 faces of this beam.
        The order is the same as the face_frames.
    center_axis : :class:`compas.geometry.Line`
        A line representing the center_axis of this beam.
    center_axis_start : :class:`compas.geometry.Point`
        The point at the start of the center_axis of this beam.
    center_axis_end : :class:`compas.geometry.Point`
        The point at the end of the center_axis of this beam.
    long_edges : list(:class:`compas.geometry.Line`)
        A list containing the 4 lines along the long axis of this beam.
    mid_point : :class:`compas.geometry.Point`
        The point at the middle of the center_axis of this beam.
    target : float
        A normalized value between 0.0 and 1.0 indicating the position of the target point on the center_axis.
        0.0 indicates the start, 1.0 indicates the end.
    target_length : float
        The length of the target beam.
    target_frame : :class:`compas.geometry.Frame`
        The frame at the target position on the center_axis of this beam.
    target_axis : :class:`compas.geometry.Line`
        A line representing the target beam.
    frame_global : :class:`compas.geometry.Frame`
        The global coordinate system of this beam.
    insertion : :class:`compas.geometry.Vector`
        The insertion vector of this beam.
    id : list(int)
        The unique identifier of this beam.
    attributes : dict
        The attributes of this beam.
    geometry : list(:class:`compas.datastructures.Mesh`)
        The geometry of this beam.
    geometry_simplified : list(:class:`compas.geometry.Line`)
        The simplified geometry of this beam.
    is_support : bool
        Indicates whether the element is a support.

    """

    def __init__(self, frame, length, width, height, **kwargs):

        # ---------------------------------------------------------------------
        # Define the simplified geometry and the geometry of the beam.
        # ---------------------------------------------------------------------
        geometry_simplified = Line(
            frame.point, Point(*add_vectors(frame.point, frame.xaxis * length))
        )

        geometry = Mesh.from_vertices_and_faces(
            *self._create_box(frame, width, height, length).to_vertices_and_faces()
        )

        # ---------------------------------------------------------------------
        # Define the square section and the length of the beam
        # ---------------------------------------------------------------------
        self._width = width
        self._height = height
        self._length = length

        # ---------------------------------------------------------------------
        # Call the Elemenet constructor and update the attributes.
        # ---------------------------------------------------------------------
        super(Beam, self).__init__(
            name=ElementType.BEAM,
            frame=frame,
            geometry_simplified=[geometry_simplified],
            geometry=[geometry],
            copy_mesh=True,
        )

        self.attributes.update(kwargs)

    # ==========================================================================
    # Serialization
    # ==========================================================================

    @property
    def data(self):

        data = {
            "frame": self.frame,
            "geometry": self.geometry,
            "id": self.id,
            "insertion": self.insertion,
            "frame_global": self.frame_global,
            "width": self.width,
            "height": self.height,
            "length": self.length,
            "target": self.target,
            "target_length": self.target_length,
            "forces": self.forces,
            "fabrication": self.fabrication,
            "is_support": self.is_support,
            "attributes": self.attributes,
        }

        # TODO: REMOVE AFTER SCENE IS FULLY IMPLEMENTED
        data["display_schema"] = OrderedDict(self.display_schema.items())

        return data

    @classmethod
    def from_data(cls, data):

        obj = cls(
            frame=data["frame"],
            length=data["length"],
            width=data["width"],
            height=data["height"],
            **data["attributes"],
        )

        obj.id = data["id"]
        obj.insertion = data["insertion"]
        obj.frame_global = data["frame_global"]
        obj.forces = data["forces"]
        obj.fabrication = data["fabrication"]
        obj.is_support = data["is_support"]

        # --------------------------------------------------------------------------
        # Beam specific attributes.
        # --------------------------------------------------------------------------
        obj.geometry = data["geometry"]
        obj.target = data["target"]
        obj.target_length = data["target_length"]

        return obj

    # ==========================================================================
    # Attributes - target
    # ==========================================================================
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    @property
    def blank(self):
        return Mesh.from_vertices_and_faces(
            *self._create_box(
                self.frame, self.width, self.height, self.length
            ).to_vertices_and_faces()
        )

    @property
    def face_frames(self):
        return [
            Frame(
                Point(
                    *add_vectors(self.mid_point, self.frame.yaxis * self.width * 0.5)
                ),
                self.frame.xaxis,
                -self.frame.zaxis,
            ),
            Frame(
                Point(
                    *add_vectors(self.mid_point, -self.frame.zaxis * self.height * 0.5)
                ),
                self.frame.xaxis,
                -self.frame.yaxis,
            ),
            Frame(
                Point(
                    *add_vectors(self.mid_point, -self.frame.yaxis * self.width * 0.5)
                ),
                self.frame.xaxis,
                self.frame.zaxis,
            ),
            Frame(
                Point(
                    *add_vectors(self.mid_point, self.frame.zaxis * self.height * 0.5)
                ),
                self.frame.xaxis,
                self.frame.yaxis,
            ),
            Frame(self.frame.point, -self.frame.yaxis, self.frame.zaxis),
            Frame(
                Point(*add_vectors(self.frame.point, self.frame.xaxis * self.length)),
                self.frame.yaxis,
                self.frame.zaxis,
            ),
        ]

    @property
    def face_outlines(self):
        p0 = Point(*add_vectors(self.mid_point, self.frame.yaxis * self.width * 0.5))
        p1 = Point(*add_vectors(self.mid_point, -self.frame.zaxis * self.height * 0.5))
        p2 = Point(*add_vectors(self.mid_point, -self.frame.yaxis * self.width * 0.5))
        p3 = Point(*add_vectors(self.mid_point, self.frame.zaxis * self.height * 0.5))
        p5 = Point(*add_vectors(self.frame.point, self.frame.xaxis * self.length))

        offsets = [
            (
                self.frame.xaxis * self.length * 0.5,
                self.frame.zaxis * self.height * 0.5,
            ),
            (self.frame.xaxis * self.length * 0.5, self.frame.yaxis * self.width * 0.5),
            (
                self.frame.xaxis * self.length * 0.5,
                self.frame.zaxis * self.height * 0.5,
            ),
            (self.frame.xaxis * self.length * 0.5, self.frame.yaxis * self.width * 0.5),
            (self.frame.yaxis * self.width * 0.5, self.frame.zaxis * self.height * 0.5),
            (self.frame.yaxis * self.width * 0.5, self.frame.zaxis * self.height * 0.5),
        ]

        return [
            Polygon(
                [
                    p + offset[0] + offset[1],
                    p + offset[0] - offset[1],
                    p - offset[0] - offset[1],
                    p - offset[0] + offset[1],
                ]
            )
            for p, offset in zip([p0, p1, p2, p3, self.frame.point, p5], offsets)
        ]

    @property
    def center_axis(self):
        return Line(self.center_axis_start, self.center_axis_end)

    @property
    def center_axis_start(self):
        return self.frame.point

    @property
    def center_axis_end(self):
        return Point(*add_vectors(self.frame.point, self.frame.xaxis * self.length))

    @property
    def long_edges(self):
        y = self.frame.yaxis
        z = self.frame.zaxis
        w = self.width * 0.5
        h = self.height * 0.5
        ps = self.center_axis_start
        pe = self.center_axis_end

        return [
            Line(ps + v, pe + v)
            for v in (y * w + z * h, -y * w + z * h, -y * w - z * h, y * w - z * h)
        ]

    @property
    def mid_point(self):
        return Point(
            *add_vectors(self.frame.point, self.frame.xaxis * self.length * 0.5)
        )

    # ==========================================================================
    # Attributes - Target Beam
    # Beams often have two states: 1) before fabrication, 2) after fabrication.
    # Also: 1) before fabrication, 2) for structural analysis.
    # If there is no fabrication the beam and the target beam are the same.
    # Otherwise, we need store the target_beam properties.
    # ==========================================================================

    @property
    def target(self):
        if not hasattr(self, "_target"):
            self._target = 0
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def set_target_by_point(self, point):
        """Given a point on the beam axis, get its normalized value on it.
        The result of this method can be used in line.point_at(t) method"""
        line = self.geometry_simplified[0]
        squared_length = line.vector.length**2

        if (point - line.start).length ** 2 <= (point - line.end).length ** 2:
            self.target = line.vector.dot(point - line.start) / squared_length
        else:
            self.target = 1.0 + line.vector.dot(point - line.end) / squared_length

    @property
    def target_length(self):
        if not hasattr(self, "_target_length"):
            self._target_length = self._length
        return self._target_length

    @target_length.setter
    def target_length(self, value):
        self._target_length = value

    @property
    def target_frame(self):
        return Frame(
            self.geometry_simplified[0].point_at(self.target),
            self.frame.xaxis,
            self.frame.yaxis,
        )

    @property
    def target_axis(self):
        point_start = self.geometry_simplified[0].point_at(self.target)
        point_end = (
            self.geometry_simplified[0].point_at(self.target)
            + self.frame.xaxis * self.target_length
        )
        return Line(point_start, point_end)

    # ==========================================================================
    # Methods, overriden from the inherited methods.
    # ==========================================================================

    def compute_aabb(self, inflate=0.00):
        """Get axis-aligned-bounding-box from geometry attributes points

        Parameters
        ----------
        inflate : float, optional
            Move the box points outside by a given value.

        Returns
        -------
        list[:class:`compas.geometry.Point`] or None

        """

        # --------------------------------------------------------------------------
        # Define this property dynamically in the class.
        # --------------------------------------------------------------------------
        if not hasattr(self, "_aabb"):
            self._aabb = []  # The eight points that defines the box.
            self._inflate = inflate if inflate else 0.00

        # --------------------------------------------------------------------------
        # Geometry attribute can be have different types.
        # Retrieve point coordinates from the most common geometry types.
        # --------------------------------------------------------------------------
        box = self._create_box(self.frame, self.width, self.height, self.length)

        points = []
        for i in range(8):
            points.append(box.corner(i))

        # --------------------------------------------------------------------------
        # Compute the bounding box from the found points and inflate it.
        # The inflation is needed to avoid floating point errors.
        # Private variable _inflate is used to track it during transformation.
        # --------------------------------------------------------------------------
        points_bbox = bounding_box(points)

        self._aabb = bounding_box(
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

        return self._aabb

    def compute_oobb(self, inflate=0.00):
        """Get object-oriented-bounding-box from geometry attributes points

        Parameters
        ----------
        inflate : float, optional
            Move the box points outside by a given value.

        Returns
        -------
        list[:class:`compas.geometry.Point`] or None

        """
        # --------------------------------------------------------------------------
        # Define this property dynamically in the class.
        # --------------------------------------------------------------------------
        if not hasattr(self, "_oobb"):
            self._oobb = []  # The eight points that defines the box.

        # --------------------------------------------------------------------------
        # Geometry attribute can be have different types.
        # Retrieve point coordinates from the most common geometry types.
        # --------------------------------------------------------------------------
        box = self._create_box(
            self.frame,
            self.width + inflate * 2,
            self.height + inflate * 2,
            self.length + inflate * 2,
        )

        self._oobb = []
        for i in range(8):
            self._oobb.append(box.corner(i))

        return self._oobb

    def copy(self):
        """Makes an independent copy of all properties of this class.

        Parameters
        ----------
        all_attributes : bool, optional
            If True, all attributes are copied.
            If False, only the main properties are copied.

        Returns
        -------
        :class:`compas_model.elements.Element`
            The copied element.

        """

        new_instance = self.__class__(
            frame=self.frame,
            length=self.length,
            width=self.width,
            height=self.height,
            **self.attributes,
        )
        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # --------------------------------------------------------------------------
        new_instance.id = list(self.id)
        new_instance.insertion = Vector(
            self.insertion[0], self.insertion[1], self.insertion[2]
        )
        new_instance.frame_global = self.frame_global.copy()

        # --------------------------------------------------------------------------
        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        # --------------------------------------------------------------------------
        new_instance._display_schema = deepcopy(self.display_schema)

        # --------------------------------------------------------------------------
        # If the beam geometry is not a box (e.g. after boolean operations), reassign it.
        # --------------------------------------------------------------------------
        new_instance.geometry = []
        for g in self.geometry:
            new_instance.geometry.append(g.copy())

        return new_instance

    # ==========================================================================
    # Methods
    # ==========================================================================

    def extend(self, length0, length1):
        """Extend the beam by a given amount at both ends."""

        # ---------------------------------------------------------------------
        # Get the target point that is later update.
        # ---------------------------------------------------------------------
        target_frame = self.target_frame
        self.target_length = self.length

        # ---------------------------------------------------------------------
        # Update the length, length should not be change by the user.
        # ---------------------------------------------------------------------
        self._length = self.length + (length0) + (length1)

        # ---------------------------------------------------------------------
        # Update the frame.
        # ---------------------------------------------------------------------
        self.frame.point = self.frame.point - self.frame.xaxis * length0

        # ---------------------------------------------------------------------
        # Update oobb and aabb to avoid recomputing them.
        # ---------------------------------------------------------------------
        self.compute_aabb()
        self.compute_oobb()

        # ---------------------------------------------------------------------
        # Update the simplified geometry.
        # ---------------------------------------------------------------------
        point_start = self.geometry_simplified[0].start - self.frame.xaxis * length0
        point_end = self.geometry_simplified[0].end + self.frame.xaxis * length1
        self.geometry_simplified = [Line(point_start, point_end)]

        # ---------------------------------------------------------------------
        # Update the geometry.
        # ---------------------------------------------------------------------
        self.geometry = [
            Mesh.from_vertices_and_faces(
                *self._create_box(
                    self.frame, self.width, self.height, self.length
                ).to_vertices_and_faces()
            )
        ]

        # Update the target point.
        self.set_target_by_point(target_frame.point)

    def extend_to_plane(self, frame):
        """Returns the amount by which to extend the beam in each direction using metric units.

        Parameters
        ----------
        frame : :class:`compas.geometry.Frame`
            The target plane to which the beam should be extended.

        Returns
        -------
        tuple(float, float)
            Extension amount at start of beam, Extension amount at end of beam

        """

        # ---------------------------------------------------------------------
        # Check if the planes are coplanar, if they are raise an error.
        # ---------------------------------------------------------------------
        if abs(self.frame.zaxis.dot(frame.zaxis)) >= 1 - 1e-6:
            print(abs(self.frame.zaxis.dot(frame.zaxis)), "\n", frame.normal)
            raise ValueError(
                "The given plane is coplanar with the beam, no extension is made."
            )

        # ---------------------------------------------------------------------
        # Find the intersection points of the long edges with the plane.
        # ---------------------------------------------------------------------
        x = {}
        pln = Plane.from_frame(frame)
        for e in self.long_edges:
            p, t = self._intersection_line_plane(e, pln)
            x[t] = p

        # ---------------------------------------------------------------------
        # Find which side to extend the beam to.
        # ---------------------------------------------------------------------
        px = self._intersection_line_plane(self.center_axis, pln)[0]
        side, _ = self.get_beam_end_closest_to_point(px)

        # ---------------------------------------------------------------------
        # Calculate the extension amounts.
        # ---------------------------------------------------------------------
        ds = 0.0
        de = 0.0
        if side == "start":
            tmin = min(x.keys())
            ds = tmin * self.length  # should be negative
        elif side == "end":
            tmax = max(x.keys())
            de = (tmax - 1.0) * self.length

        print("ds: ", ds)
        print("de: ", de)
        self.extend(-ds, de)

    def set_frame_zaxis(self, vector):
        """Align the z_axis of the beam's definition with the given vector.

        Parameters
        ----------
        vector : :class:`compas.geometry.Vector`
            The vector with which to align the z_axis.

        """

        # ---------------------------------------------------------------------
        # Align the frame z-axis with the given vector.
        # ---------------------------------------------------------------------
        y_vector = Vector(*cross_vectors(self.frame.xaxis, vector)) * -1.0
        self.frame = Frame(self.frame.point, self.frame.xaxis, y_vector)

        # ---------------------------------------------------------------------
        # Update oobb and aabb to avoid recomputing them.
        # ---------------------------------------------------------------------
        self.compute_aabb()
        self.compute_oobb()

        # ---------------------------------------------------------------------
        # Update the geometry.
        # ---------------------------------------------------------------------
        self.geometry = [
            Mesh.from_vertices_and_faces(
                *self._create_box(
                    self.frame, self.width, self.height, self.length
                ).to_vertices_and_faces()
            )
        ]

    def get_beam_end_closest_to_point(self, point):
        """Returns which endpoint of the center_axis of the beam is closer to the given point.

        Parameters
        ----------
        point : :class:`compas.geometry.Point`
            The point of interest.

        Returns
        -------
        list(str, :class:`compas.geometry.Point`)
            Two element list. First element is either 'start' or 'end' depending on the result.
            The second element is the actual endpoint of the beam's center_axis which correspond to the result.

        """

        # ---------------------------------------------------------------------
        # Measure the distance to the line end points.
        # ---------------------------------------------------------------------
        ps = self.center_axis_start
        pe = self.center_axis_end
        ds = point.distance_to_point(ps)
        de = point.distance_to_point(pe)

        # ---------------------------------------------------------------------
        # Return the closest end.
        # ---------------------------------------------------------------------
        if ds <= de:
            return ["start", ps]
        else:
            return ["end", pe]

    @property
    def display_schema(self):

        face_color = (
            [0.9, 0.9, 0.9] if not self.is_support else [0.9686, 0.6157, 0.5176]
        )

        ordered_dict = OrderedDict(
            [
                (
                    "geometry_simplified",
                    {
                        "facecolor": [0.0, 0.0, 0.0],
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 3,
                        "opacity": 1.0,
                        "is_visible": True,
                    },
                ),
                (
                    "geometry",
                    {
                        "facecolor": face_color,
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 1,
                        "opacity": 0.75,
                        "is_visible": True,
                    },
                ),
                (
                    "frame",
                    {
                        "facecolor": [0.0, 0.0, 0.0],
                        "linecolor": [1.0, 1.0, 1.0],
                        "linewidth": 1,
                        "opacity": 1.0,
                        "is_visible": False,
                    },
                ),
                (
                    "aabb_mesh",
                    {
                        "facecolor": [0.0, 0.0, 0.0],
                        "linecolor": [1.0, 1.0, 1.0],
                        "linewidth": 1,
                        "opacity": 0.25,
                        "is_visible": False,
                    },
                ),
                (
                    "oobb_mesh",
                    {
                        "facecolor": [0.0, 0.0, 0.0],
                        "linecolor": [1.0, 1.0, 1.0],
                        "linewidth": 1,
                        "opacity": 0.25,
                        "is_visible": False,
                    },
                ),
                (
                    "face_frames",
                    {
                        "facecolor": [0.0, 0.0, 0.0],
                        "linecolor": [1.0, 1.0, 1.0],
                        "linewidth": 1,
                        "opacity": 1.0,
                        "is_visible": False,
                    },
                ),
                (
                    "face_outlines",
                    {
                        "facecolor": [1.0, 0.0, 0.0],
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 3,
                        "opacity": 1.0,
                        "is_visible": False,
                        "show_faces": False,
                    },
                ),
                (
                    "long_edges",
                    {
                        "facecolor": [1.0, 0.0, 0.0],
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 3,
                        "opacity": 1.0,
                        "is_visible": False,
                        "show_faces": False,
                    },
                ),
                (
                    "mid_point",
                    {
                        "pointcolor": [0.0, 0.0, 0.0],
                        "is_visible": False,
                        "pointsize": 20,
                    },
                ),
                (
                    "center_axis_start",
                    {
                        "pointcolor": [0.0, 0.0, 0.0],
                        "is_visible": False,
                        "pointsize": 20,
                    },
                ),
                (
                    "center_axis_end",
                    {
                        "pointcolor": [0.0, 0.0, 0.0],
                        "is_visible": False,
                        "pointsize": 20,
                    },
                ),
                (
                    "target_frame",
                    {
                        "facecolor": [1.0, 0.0, 0.0],
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 3,
                        "opacity": 1.0,
                        "is_visible": False,
                        "show_faces": False,
                    },
                ),
                (
                    "target_axis",
                    {
                        "facecolor": [1.0, 0.0, 0.0],
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 7,
                        "opacity": 1.0,
                        "is_visible": False,
                        "show_faces": False,
                    },
                ),
            ]
        )
        # --------------------------------------------------------------------------
        # create forces display schema
        # --------------------------------------------------------------------------
        if hasattr(self, "_forces"):
            for force_tuple in self._forces:
                setattr(self, force_tuple[0], force_tuple[1])

        # --------------------------------------------------------------------------
        # create fabrication display schema
        # --------------------------------------------------------------------------
        if hasattr(self, "_fabrication"):
            for fabrication_tuple in self._fabrication:
                setattr(self, fabrication_tuple[0], fabrication_tuple[1])

        return ordered_dict

    # ==========================================================================
    # Constructors
    # ==========================================================================
    @classmethod
    def from_line(cls, center_axis, width, height, z_vector=None):
        """Define the beam from its center_axis.

        Parameters
        ----------
        center_axis : :class:`compas.geometry.Line`
            The center_axis of the beam to be created.
        length : float
            Length of the beam.
        width : float
            Width of the cross-section.
        height : float
            Height of the cross-section.
        z_vector : :class:`compas.geometry.Vector`
            A vector indicating the height direction (z-axis) of the cross-section.
            Defaults to WorldZ or WorldX depending on the center_axis's orientation.

        Returns
        -------
        :class:`compas_timber.parts.Beam`

        """
        x_vector = center_axis.vector

        if not z_vector:
            z_vector = Vector(0, 0, 1)
            angle = angle_vectors(z_vector, x_vector)
            if angle < ANGLE_TOLERANCE or angle > math.pi - ANGLE_TOLERANCE:
                z_vector = Vector(1, 0, 0)
        else:
            z_vector = z_vector

        y_vector = Vector(*cross_vectors(x_vector, z_vector)) * -1.0
        if y_vector.length < DEFAULT_TOLERANCE:
            raise ValueError(
                "The given z_vector seems to be parallel to the given center_axis."
            )
        frame = Frame(center_axis.start, x_vector, y_vector)
        length = center_axis.length

        return cls(frame, length, width, height)

    @classmethod
    def from_endpoints(cls, point_start, point_end, width, height, z_vector=None):
        """Creates a Beam from the given endpoints.

        Parameters
        ----------
        point_start : :class:`compas.geometry.Point`
            The start point of a center_axis
        end_point : :class:`compas.geometry.Point`
            The end point of a center_axis
        width : float
            Width of the cross-section.
        height : float
            Height of the cross-section.
        z_vector : :class:`compas.geometry.Vector`
            A vector indicating the height direction (z-axis) of the cross-section.
            Defaults to WorldZ or WorldX depending on the center_axis's orientation.

        Returns
        -------
        :class:`compas_timber.parts.Beam`

        """
        line = Line(point_start, point_end)
        return cls.from_center_axis(line, width, height, z_vector)

    # ==========================================================================
    # Private geometry methods
    # ==========================================================================

    def _create_box(self, frame, xsize, ysize, zsize):
        """Create box from frame.
        This method is needed, because compas box is create from center, not by domains."""
        boxframe = frame.copy()
        boxframe.point += boxframe.xaxis * zsize * 0.5
        return Box(zsize, xsize, ysize, frame=boxframe)

    def _intersection_line_plane(self, line, plane, tol=1e-6):
        """Computes the intersection point of a line and a plane.

        A tuple containing the intersection point and a `t` value are returned.

        The `t` parameter is the normalized parametric value (0.0 -> 1.0) of the location of the intersection point
        in relation to the line's starting point.
        0.0 indicates intersaction near the starting point, 1.0 indicates intersection near the end.

        If no intersection is found, [None, None] is returned.

        Parameters
        ----------
        line : :class:`compas.geometry.Line`
            Two points defining the line.
        plane : :class:`compas.geometry.Plane`
            The target point and normal defining the plane.
        tol : float, optional. Default is 1e-6.
            A tolerance for membership verification.

        Returns
        -------
        tuple(:class:`compas.geometry.Point`, float)

        """
        a, b = line
        o, n = plane

        ab = subtract_vectors(b, a)
        dotv = dot_vectors(n, ab)

        if math.fabs(dotv) <= tol:
            # ---------------------------------------------------------------------
            # If the dot product (cosine of the angle between segment and plane),
            # is close to zero the line and the normal are almost perpendicular,
            # hence there is no intersection.
            # ---------------------------------------------------------------------
            return None, None

        # ---------------------------------------------------------------------
        # Targeted on the ratio = -dot_vectors(n, ab) / dot_vectors(n, oa)
        # There are three scenarios:
        # 1) 0.0 < ratio < 1.0: the intersection is between a and b
        # 2) ratio < 0.0: the intersection is on the other side of a
        # 3) ratio > 1.0: the intersection is on the other side of b
        # ---------------------------------------------------------------------
        oa = subtract_vectors(a, o)
        t = -dot_vectors(n, oa) / dotv
        ab = scale_vector(ab, t)
        return Point(*add_vectors(a, ab)), t

    # ==========================================================================
    # Minimal examples
    # ==========================================================================

    @classmethod
    def from_minimal_example(cls):

        beam = Beam(
            frame=Frame(point=[-5, 0, 0], xaxis=[1, 0, 0], yaxis=[0, 1, 0]),
            length=10,
            width=1,
            height=2,
        )
        beam.extend(1, 2.5)
        return beam

    @classmethod
    def from_minimal_example_collection(cls):

        frames = [
            [[-21.0, -1.5, 1], [0, 1, 0], [0, 0, 1]],
            [[-26, 3.5, 0.5], [1, 0, 0], [0, 0, 1]],
            [[-7, -1, 0.5], [0, 1, 0], [0, 0, 1]],
            [[-12, -1.5, 0.5], [1, 0, 0], [0, 0, 1]],
            [[2.5, -1, 0.5], [0, 1, 0], [0, 0, 1]],
            [[2, -1.5, 0.5], [1, 0, 0], [0, 0, 1]],
            [[16, 12.5, 0.5], [0, 1, 0], [0, 0, 1]],
            [[16, 2.5, 0.5], [0, 1, 0], [0, 0, 1]],
        ]

        beams = []
        for frame in frames:
            beam = Beam(
                frame=Frame(point=frame[0], xaxis=frame[1], yaxis=frame[2]),
                length=10,
                width=1,
                height=1,
            )
            beams.append(beam)

        return beams
