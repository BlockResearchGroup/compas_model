from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from copy import deepcopy

from compas_model.elements.element import Element
from compas_model.elements.element_type import ElementType
from collections import OrderedDict

from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Vector
from compas.geometry import Polygon
from compas.geometry import cross_vectors
from compas.geometry import Transformation
from compas.geometry import bounding_box
from compas.geometry import distance_point_point
from compas_model.elements.triangulator import Triagulator

# TODO: REMOVE AFTER TOLERANCE IS FULLY IMPLEMENTED
ANGLE_TOLERANCE = 1e-3  # [radians]
DEFAULT_TOLERANCE = 1e-6


class Plate(Element):
    """A plate is a surface element defined by two outlines.

    The two polygon representation has the following behavior:
        - The first polygon represents the base outline of the plate.
        - Two outline frames are computed from it, pointing outward.
        - The plate geometry is created by lofting the two outlines using the Ear Clipping algorithm.
        - The simplified geometry also facilitates the storage of holes, but they are not meshed.

    The plate implementation is inspired by the compas_wood package:
    https://github.com/petrasvestartas/compas_wood/blob/main/src/frontend/src/wood/include/wood_element.h

    Parameters
    ----------
    polygon0 : :class:`compas.geometry.Polygon`
        The first outline of the plate.
    polygon1 : :class:`compas.geometry.Polygon`
        The second outline of the plate.
    compute_loft : bool, optional
        If True, the loft of the two outlines is computed.
        If False, the loft is not computed.
        Default is False.
    insertion : list, optional
        The insertion vectors of the plate.
        The list must have 2 + number of points of polygon0.
        Default is None.
    joint_types_per_face : list, optional
        The joint types of the plate.
        The list must have 2 + number of points of polygon0.
        Default is None.
    **kwargs
        Additional keyword arguments.

    Attributes
    ----------
    insertion : list
        The insertion vectors of the plate.
        The list has 2 + number of points of polygon0.
    joint_types_per_face : list
        The joint types of the plate.
        The list has 2 + number of points of polygon0.
    face_frames : list
        The frames of the faces of the plate.
    face_outlines : list
        The outlines of the faces of the plate.
    thickness : float
        The thickness of the plate.
    geometry : list
        The geometry of the plate.
    geometry_simplified : list
        The simplified geometry of the plate.
    frame_global : :class:`compas.geometry.Frame`
        The global frame of the plate.
    frame : :class:`compas.geometry.Frame`
        The local frame of the plate.
    id : list
        The unique identifier of the plate.
    attributes : dict
        The attributes of the plate.
    is_support : bool
        Indicates whether the element is a support.

    """

    def __init__(
        self,
        polygon0=None,
        polygon1=None,
        compute_loft=False,
        insertion=None,
        joint_types_per_face=None,
        **kwargs
    ):

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
        # Create average plane.
        # --------------------------------------------------------------------------
        frame = self._get_average_plane(polygon0)

        # --------------------------------------------------------------------------
        # Check the winding of the polygons.
        # --------------------------------------------------------------------------
        self.geometry_simplified = [polygon0.copy(), polygon1.copy()]
        reverse = self._check_winding(polygon1, frame)
        if reverse:
            frame = Frame(frame.point, frame.xaxis, -frame.yaxis)
            for i in range(len(self.geometry_simplified)):
                points = list(self.geometry_simplified[i].points)
                points.reverse()
                self.geometry_simplified[i] = Polygon(points)

        # --------------------------------------------------------------------------
        # Insertion vectors and joint types.
        # --------------------------------------------------------------------------
        if insertion:
            if len(insertion) != (len(polygon0.points) + 2):
                raise ValueError(
                    "The insertion_vectors must have 2 + number of points of polygon0."
                )
            else:
                self.insertion = insertion
                if reverse:
                    self.insertion[2:] = reversed(self.insertion[2:])

        if joint_types_per_face:
            if len(joint_types_per_face) != (len(polygon0.points) + 2):
                raise ValueError(
                    "The joint_types must have 2 + number of points of polygon0."
                )
            else:
                self._joint_types_per_face = joint_types_per_face
                if reverse:
                    self._joint_types_per_face[2:] = reversed(
                        self._joint_types_per_face[2:]
                    )

        # --------------------------------------------------------------------------
        # Create loft of the two outlines.
        # --------------------------------------------------------------------------
        geometry = None
        if compute_loft:
            geometry = [
                Triagulator.from_loft_two_point_lists(
                    self.geometry_simplified[0].points,
                    self.geometry_simplified[1].points,
                )[0]
            ]

        # --------------------------------------------------------------------------
        # Call the default Element constructor with the given parameters.
        # --------------------------------------------------------------------------
        super().__init__(
            name=ElementType.PLATE,
            frame=frame,
            geometry_simplified=[polygon0, polygon1],
            geometry=geometry,
            copy_geometry=False,  # geometry is created by Triagulator
        )

        # --------------------------------------------------------------------------
        # Set custom attributes given by the user.
        # --------------------------------------------------------------------------
        self.attributes = {}
        self.attributes.update(kwargs)

    # ==========================================================================
    # Serialization
    # ==========================================================================

    @property
    def data(self):

        data = {
            "frame": self.frame,
            "geometry_simplified": self.geometry_simplified,
            "geometry": self.geometry,
            "id": self.id,
            "insertion": self.insertion,
            "frame_global": self.frame_global,
            "joint_types_per_face": self.joint_types_per_face,
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
            polygon0=data["geometry_simplified"][0],
            polygon1=data["geometry_simplified"][1],
            compute_loft=False,
            insertion=None,
            joint_types_per_face=data["joint_types_per_face"],
            **data["attributes"],
        )

        obj.id = data["id"]
        obj.insertion = data["insertion"]
        obj.frame_global = data["frame_global"]
        obj.is_support = data["is_support"]
        obj.forces = data["forces"]
        obj.fabrication = data["fabrication"]

        # --------------------------------------------------------------------------
        # Plate specific attributes.
        # --------------------------------------------------------------------------
        obj.geometry = data["geometry"]

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def joint_types_per_face(self):
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
    def insertion(self):
        return self._insertion

    @insertion.setter
    def insertion(self, insertion):
        if len(insertion) != (len(self.geometry_simplified[0].points) + 2):
            raise ValueError(
                "The insertion_vectors must have 2 + number of points of polygon0."
            )
        else:
            self._insertion = insertion

    @property
    def face_frames(self):
        if hasattr(self, "_face_frames"):
            return self._face_frames
        else:
            self._face_frames = [
                self.frame,
            ]

            top_frame = self._get_average_plane(self.geometry_simplified[1])
            plane = Plane.from_frame(self.frame)
            p0 = plane.closest_point(top_frame.point)
            p1 = plane.closest_point(top_frame.point + top_frame.zaxis)
            if distance_point_point(p0, top_frame.point) > distance_point_point(
                p1, top_frame.point
            ):
                top_frame = Frame(top_frame.point, top_frame.xaxis, -top_frame.yaxis)
            self._face_frames.append(top_frame)

            n = len(self.geometry_simplified[0].points)
            for i in range(n):
                face_frame = Frame(
                    (
                        self.geometry_simplified[1][(i + 1) % n]
                        + self.geometry_simplified[0][i]
                    )
                    * 0.5,
                    self.geometry_simplified[0][(i + 1) % n]
                    - self.geometry_simplified[0][i],
                    self.geometry_simplified[1][i] - self.geometry_simplified[0][i],
                )
                self._face_frames.append(face_frame)

            return self._face_frames

    @property
    def face_outlines(self):
        if hasattr(self, "_face_outlines"):
            return self._face_outlines
        else:
            self._face_outlines = [
                self.geometry_simplified[0],
                self.geometry_simplified[1],
            ]
            n = len(self.geometry_simplified[0].points)
            for i in range(n):
                face_outline = Polygon(
                    [
                        self.geometry_simplified[0][i],
                        self.geometry_simplified[0][(i + 1) % n],
                        self.geometry_simplified[1][(i + 1) % n],
                        self.geometry_simplified[1][i],
                    ]
                )
                self._face_outlines.append(face_outline)

            return self._face_outlines

    @property
    def thickness(self):
        return Plane.from_frame(self.frame).distance_to_point(
            self.geometry_simplified[0]
        )

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
                        "linewidth": 5,
                        "opacity": 1.0,
                        "is_visible": True,
                        "show_faces": False,
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
    # Methods, overriden from Element
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
        # Copy the two polygon points and transform them to XY plane.
        # --------------------------------------------------------------------------
        points = []
        for polygon in self.geometry_simplified:
            points.extend(polygon.points)

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
            self._inflate = inflate if inflate else 0.00

        # --------------------------------------------------------------------------
        # Create transformation to XY plane.
        # --------------------------------------------------------------------------
        xform = Transformation.from_frame_to_frame(self.frame, Frame.worldXY())
        xform_inv = xform.inverse()

        # --------------------------------------------------------------------------
        # Copy the two polygon points and transform them to XY plane.
        # --------------------------------------------------------------------------
        points = []
        for polygon in self.geometry_simplified:
            for point in polygon.points:
                points.append(point.transformed(xform))

        # --------------------------------------------------------------------------
        # Compute the bounding box from the found points and inflate it.
        # The inflation is needed to avoid floating point errors.
        # Private variable _inflate is used to track it during transformation.
        # --------------------------------------------------------------------------
        points_bbox = bounding_box(points)

        self._oobb = bounding_box(
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

        # --------------------------------------------------------------------------
        # Orient back
        # --------------------------------------------------------------------------
        for i in range(len(self._oobb)):
            point = Point(
                self._oobb[i][0], self._oobb[i][1], self._oobb[i][2]
            ).transformed(xform_inv)
            self._oobb[i] = [point[0], point[1], point[2]]

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
            polygon0=self.geometry_simplified[0],
            polygon1=self.geometry_simplified[1],
            compute_loft=False,
            insertion=None,
            joint_types_per_face=self.joint_types_per_face,
            **self.attributes,
        )
        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # --------------------------------------------------------------------------
        new_instance.id = list(self.id)
        new_instance.insertion = list(self.insertion)
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
    # Private geometry methods
    # ==========================================================================

    def _get_average_plane(self, polygon, reverse=False):

        # --------------------------------------------------------------------------
        # number of points
        # --------------------------------------------------------------------------
        n = len(polygon.points)

        # --------------------------------------------------------------------------
        # origin
        # --------------------------------------------------------------------------
        origin = Point(0, 0, 0)
        for point in polygon:
            origin = origin + point
        origin = origin / n

        # --------------------------------------------------------------------------
        # xaxis
        # --------------------------------------------------------------------------
        xaxis = polygon[1] - polygon[0]
        xaxis.unitize()

        # --------------------------------------------------------------------------
        # zaxis
        # --------------------------------------------------------------------------
        zaxis = Vector(0, 0, 0)

        for i in range(n):
            prev_id = ((i - 1) + n) % n
            next_id = ((i + 1) + n) % n
            zaxis = zaxis + cross_vectors(
                polygon.points[i] - polygon.points[prev_id],
                polygon.points[next_id] - polygon.points[i],
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
        if reverse:
            frame = Frame(origin, frame.xaxis, -frame.yaxis)

        return frame

    def _check_winding(self, polygon1, frame):
        """Check the winding of the polygons.
        If after orientation to XY plane the polygon1 is above zero reverse the two polygons.
        """
        polygon1_copy = polygon1.copy()
        xform = Transformation.from_frame_to_frame(frame, Frame.worldXY())
        polygon1_copy.transform(xform)
        return polygon1_copy[0].z > 0

    # ==========================================================================
    # Example
    # ==========================================================================

    @classmethod
    def from_minimal_example(cls):
        """Returns a plate.

        Returns
        -------
        plate : :class:`compas_model.elements.Plate`
            List of polygons with holes.

        """
        polygon0 = Polygon(
            [
                Point(2.891611, 0, 0),
                Point(1.445806, 3.445158, 0),
                Point(-1.445806, 3.445158, 0),
                Point(-2.891611, -0, 0),
                Point(-1.445806, -3.445158, 0),
                Point(1.445806, -3.445158, 0),
            ]
        )
        polygon1 = Polygon(
            [
                Point(3.270739, 0.003139, 1),
                Point(1.680353, 3.792813, 1),
                Point(-1.500419, 3.792813, 1),
                Point(-3.090805, 0.003139, 1),
                Point(-1.500419, -3.786535, 1),
                Point(1.680353, -3.786535, 1),
            ]
        )

        plate = cls(polygon0, polygon1, True)
        return plate
