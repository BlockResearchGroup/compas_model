from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.geometry import Line
from compas.geometry import Polygon
from compas.geometry import Point
from compas.geometry import bounding_box
from compas.geometry import Box
from compas.geometry import Vector
from compas.geometry import Frame
from compas.geometry import cross_vectors
from compas.geometry import Transformation
from compas.geometry import distance_point_point_sqrd
from compas_model.elements.element import Element


class Interface(Element):
    """A beam representation of a Line and a Box.

    Parameters
    ----------
    name : str, optional
        Name of the element
    frame : :class:`compas.geometry.Frame`, optional
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry_simplified : Any, optional
        Minimal geometrical represetation of an object. For example a list of :class:`compas.geometry.Polyline` can represent a plate.
    geometry : Any, optional
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    kwargs (dict, optional):
        Additional keyword arguments.

    Attributes
    ----------
    dtype : str, read-only
        The type of the object in the form of a fully qualified module name and a class name, separated by a forward slash ("/").
        For example: ``"compas.datastructures/Mesh"``.
    data : dict
        The representation of the object as a dictionary containing only built-in Python data types.
        The structure of the dict is described by the data schema.
    guid : str, read-only
        The globally unique identifier of the object.
        The guid is generated with ``uuid.uuid4()``.
    name : str
        The name of the object.
        This name is not necessarily unique and can be set by the user.
        The default value is the object's class name: ``self.__class__.__name__``.
    frame : :class:`compas.geometry.Frame`
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry_simplified : :class:`compas.geometry.Line`
        Minimal geometrical represetation of an object. For example a :class:`compas.geometry.Polyline` that can represent: a point, a line or a polyline.
    geometry : :class:`compas.geometry.Box`
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    aabb : :class:`compas.geometry.Box`
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`
        The collision geometry of the element.
    dimensions : list
        The dimensions of the element.
    features : dict
        The features of the element, joinery, openings, etc.
    insertion : :class:`compas.geometry.Vector`
        The insertion vector of the element. Default is (0, 0, -1).
    node : :class:`compas_model.model.ElementNode`
        The node of the element.

    """

    def __init__(self, polygon, **kwargs):

        super(Interface, self).__init__(
            frame=polygon.frame, geometry_simplified=polygon, geometry=polygon.to_mesh(), **kwargs
        )

    # ==========================================================================
    # Serialization.
    # ==========================================================================

    @property
    def data(self):
        return {
            "name": self.name,
            "frame": self.frame,
            "geometry_simplified": self.geometry_simplified.points,
            "geometry": self.geometry,
            "aabb": self.aabb,
            "obb": self.obb,
            "collision_mesh": self.collision_mesh,
            "dimensions": self.dimensions,
            "features": self.features,
            "insertion": self.insertion,
            "attributes": self.attributes,
        }

    @classmethod
    def from_data(cls, data):
        element = cls(Polygon(data["geometry_simplified"]))
        element._name = data["name"]
        element._aabb = data["aabb"]
        element._obb = data["obb"]
        element._collision_mesh = data["collision_mesh"]
        element._dimensions = data["dimensions"]
        element._features = data["features"]
        element._insertion = data["insertion"]
        element.attributes.update(data["attributes"])
        return element

    # ==========================================================================
    # Templated methods to provide minimal information for:
    # aabb
    # obb
    # geometry_collision
    # transform
    # ==========================================================================

    @property
    def dimensions(self):
        if not type(self.obb) is Box:
            raise TypeError("OBB is not set as a Box.")
        return [self.obb.width, self.obb.height, self.obb.depth]

    def compute_aabb(self, inflate=0.0):

        """Computes the Axis Aligned Bounding Box (AABB) of the element.

        Attributes
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """

        self._aabb = self._to_non_zero_aabb(self.geometry_simplified.points, inflate=inflate)
        return self._aabb

    def compute_obb(self, inflate=0.0):
        """Computes the Oriented Bounding Box (OBB) of the element.

        Attributes
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """

        # orient polygon to xy frame
        polygon = self.geometry_simplified.copy()

        # find the longest edge
        longest_edge_index = 0
        longest_edge_length = distance_point_point_sqrd(polygon.points[0], polygon.points[1])
        n = len(polygon.points)
        for i in range(1, n):
            edge_length = distance_point_point_sqrd(polygon.points[i], polygon.points[(i + 1) % n])
            if edge_length > longest_edge_length:
                longest_edge_length = edge_length
                longest_edge_index = i
        longest_edge_line = Line(polygon.points[longest_edge_index], polygon.points[(longest_edge_index + 1) % n])

        # create a frame from the longest edge as x-axis, and y-axis is the cross_product of the longest edge and z-axis
        xaxis = longest_edge_line.direction
        zaxis = polygon.normal
        yaxis = Vector(*cross_vectors(xaxis, zaxis))
        yaxis.unitize()
        frame = Frame(longest_edge_line.midpoint, xaxis, yaxis)

        # orient polygon to the new frame
        xform = Transformation.from_frame_to_frame(frame, Frame.worldXY())
        polygon.transform(xform)

        # compute the non zero box
        self._obb = self._to_non_zero_aabb(polygon.points, inflate)
        self._obb.transform(xform.inverse())

        return self._obb

    def compute_collision_mesh(self):
        """Computes the collision geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """
        self._collision_mesh = self.geometry
        return self._collision_mesh

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

        self.frame.transform(transformation)
        self.geometry_simplified.transform(transformation)
        self.geometry.transform(transformation)

        # I do not see the other way than to check the private property.
        # Otherwise it gets computed and transformed twice.
        # Also, we do not want to have these properties computed, unless needed.
        # It can be done above geometry transformations, but they will be computed.
        if self._aabb:
            self.compute_aabb()

        if self._obb:
            self.obb.transform(transformation)

        if self._collision_mesh:
            self.transform(transformation)

    def _to_non_zero_aabb(self, points, inflate=0.0, non_zero_tolerance=0.01):
        """
        Helper function to create a box from a bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`

        """

        # ==========================================================================
        # Compute the bounding box that can have zero length edges (invalid box).
        # ==========================================================================
        aabb_points = bounding_box(points)

        # ==========================================================================
        # Simple scaling or additiona of box dimensionsis not allowed,
        # when the bounding box have zero length edges.
        # Zero length edges will results is scaling or division by zero,
        # for example when frame of a box is create unitize method is used.
        # Solution: coordinate addition for box diagonals.
        # ==========================================================================
        tolerance = (
            non_zero_tolerance
            if Vector.from_start_end(aabb_points[0], aabb_points[1]).length < 1e-6
            or Vector.from_start_end(aabb_points[0], aabb_points[3]).length < 1e-6
            or Vector.from_start_end(aabb_points[0], aabb_points[4]).length < 1e-6
            else 0.0
        )

        p0 = Point(
            aabb_points[0][0] - tolerance,
            aabb_points[0][1] - tolerance,
            aabb_points[0][2] - tolerance,
        )
        p1 = Point(
            aabb_points[6][0] + tolerance,
            aabb_points[6][1] + tolerance,
            aabb_points[6][2] + tolerance,
        )

        return Box(
            frame=Frame((p0 + p1) * 0.5, [1, 0, 0], [0, 1, 0]),
            xsize=p1[0] - p0[0] + inflate,
            ysize=p1[1] - p0[1] + inflate,
            zsize=p1[2] - p0[2] + inflate,
        )
