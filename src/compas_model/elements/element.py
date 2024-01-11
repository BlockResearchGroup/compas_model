from __future__ import print_function
from __future__ import absolute_import
from __future__ import division


from compas.data import Data
from compas.geometry import (
    Frame,
    Vector,
    Transformation,
    Point,
    Box,
    bounding_box,
    Scale,
    distance_point_point,
)


class Element(Data):
    """Class representing a structural object.

    Parameters
    ----------
    name : str, optional
        Name of the element
    frame : :class:`compas.geometry.Frame`, optional
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry_simplified : Any, optional
        Minimal geometrical represetation of an object. For example a :class:`compas.geometry.Polyline` that can represent: a point, a line or a polyline.
    geometry : Any, optional
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    copy_geometry : bool, optional
        If True, the geometry will be copied to avoid references.
    kwargs (dict, optional):
        Additional keyword arguments.

    Attributes
    ----------
    name : str
        Name of the element
    frame : :class:`compas.geometry.Frame`
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry_simplified : Any
        Minimal geometrical represetation of an object. For example a :class:`compas.geometry.Polyline` that can represent: a point, a line or a polyline.
    geometry : Any
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    id : int
        Unique identifier of the element.
    key : str
        Unique key of the element.
    insertion : :class:`compas.geometry.Vector`
        The insertion vector of the element.
    is_support : bool
        If True, the element is a support.

    Examples
    --------
    >>> frame = Frame([3, 0, 0], [0.866, 0.1, 0.0], [0.5, 0.866, 0.0])
    >>> box = Box(frame=frame, xsize=2, ysize=4, zsize=0.25)
    >>> element = Element("BLOCK", Frame.worldXY(), Point(0,0,0), box)
    >>> element.insertion = Vector(0, 0, 1)

    """

    def __init__(
        self,
        name=None,
        frame=None,
        geometry_simplified=None,
        geometry=None,
        copy_geometry=True,
        **kwargs
    ):
        # --------------------------------------------------------------------------
        # Call the inherited Data constructor.
        # --------------------------------------------------------------------------
        super(Element, self).__init__(**kwargs)

        # --------------------------------------------------------------------------
        # Set the element name.
        # --------------------------------------------------------------------------
        self.name = name.lower() if name else "unknown"

        # --------------------------------------------------------------------------
        # Set the base frame of the element.
        # --------------------------------------------------------------------------
        self.frame = frame.copy() if frame else Frame.worldXY()

        # --------------------------------------------------------------------------
        # Copy geometries to avoid transformation issues.
        # --------------------------------------------------------------------------
        self.geometry_simplified = []
        self.geometry = []
        if geometry_simplified:
            self.copy_geometry = copy_geometry
            self.geometry_simplified = self._copy_geometries(
                geometry_simplified, copy_geometry
            )

        if geometry:
            self.geometry = self._copy_geometries(geometry, copy_geometry)

        # --------------------------------------------------------------------------
        # Define this property dynamically in the class.
        # --------------------------------------------------------------------------
        self._aabb = None
        self._obb = None
        self._inflate = 0.0
        self._id = -1
        self._insertion = Vector(0, 0, 1)
        self._is_support = False

    def _copy_geometries(self, geometries, copy_flag):
        """
        Helper function to copy geometries.

        Parameters
        ----------
        geometries : Any
            A list of geometries.
        copy_flag : bool
            If True, the geometry will be copied to avoid references.

        Returns
        -------
        list
        """
        if isinstance(geometries, list):
            copied_geometries = []
            for g in geometries:
                if g and copy_flag:
                    copied_geometries.append(g.copy())
                else:
                    copied_geometries.append(g)
            return copied_geometries
        else:
            if geometries and copy_flag:
                return [geometries.copy()]
            else:
                return [geometries]

    # ==========================================================================
    # Serialization
    # ==========================================================================

    @property
    def data(self):
        data = {
            "name": self.name,
            "frame": self.frame,
            "geometry_simplified": self.geometry_simplified,
            "geometry": self.geometry,
            "copy_geometry": self.copy_geometry,
            "id": self.id,
            "insertion": self.insertion,
            "is_support": self.is_support,
        }

        return data

    @classmethod
    def from_data(cls, data):
        obj = cls(
            name=data["name"],
            frame=data["frame"],
            geometry_simplified=data["geometry_simplified"],
            geometry=data["geometry"],
            copy_geometry=data["copy_geometry"],
        )

        obj.id = data["id"]
        obj.insertion = data["insertion"]
        obj.is_support = data["is_support"]

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def key(self):
        return str(self.guid)

    @property
    def insertion(self):
        return self._insertion

    @insertion.setter
    def insertion(self, value):
        self._insertion = value

    @property
    def aabb(self):
        if not self._aabb:
            self._aabb = self.compute_aabb()
        return self._aabb

    @property
    def obb(self):
        if not self._obb:
            self._obb = self.compute_obb()
        return self._obb

    def get_geometry_points(self):
        """Get points from the geometry attribute.
        This method is needed for aabb and obb computation and subsequent collision detection.


        Returns
        -------
        list[:class:`compas.geometry.Point`]
            The points of the geometry.

        Raises
        ------
        ValueError
            If the geometry is not a Mesh, Polyline, Line, Box, Pointcloud or Point.

        """

        raise NotImplementedError

    def compute_aabb(self, inflate=None):
        """Get axis-aligned-bounding-box from geometry attributes points

        Parameters
        ----------
        inflate : float, optional
            Move the box points outside by a given value.

        Returns
        -------
        list[:class:`compas.geometry.Point`] or None

        """

        self._inflate = inflate if inflate else 0.00

        # --------------------------------------------------------------------------
        # Geometry attribute can be have different types.
        # Retrieve points coordinates from the most common geometry types and create the bounding box.
        # --------------------------------------------------------------------------
        self._aabb = Box.from_bounding_box(bounding_box(self.get_geometry_points()))

        # --------------------------------------------------------------------------
        # Check the flatness.
        # --------------------------------------------------------------------------
        is_flat = (
            self._aabb.width < 0.001
            or self._aabb.depth < 0.001
            or self._aabb.height < 0.001
        ) and self._inflate == 0.00
        if is_flat:
            self._inflate = 0.001

        # --------------------------------------------------------------------------
        # Compute the bounding box from the found points and inflate it.
        # The inflation is needed to avoid floating point errors.
        # Private variable _inflate is used to track it during transformation.
        # --------------------------------------------------------------------------
        self._aabb.transform(
            Scale.from_factors(
                [
                    (self._aabb.width + self._inflate) / self._aabb.width,
                    (self._aabb.depth + self._inflate) / self._aabb.depth,
                    (self._aabb.height + self._inflate) / self._aabb.height,
                ]
            )
        )

        return self._aabb

    def compute_obb(self, inflate=None):
        """Get object-oriented-bounding-box from geometry attributes points

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
        # Geometry attribute can be have different types.
        # Retrieve point coordinates from the most common geometry types.
        # --------------------------------------------------------------------------
        points = self.get_geometry_points()

        # --------------------------------------------------------------------------
        # Transform the points to the local frame and compute the bounding box.
        # --------------------------------------------------------------------------
        xform = Transformation.from_frame_to_frame(self.frame, Frame.worldXY())

        self._obb = []
        for i in range(len(points)):
            point = Point(*points[i])
            point.transform(xform)
            self._obb.append(point)
        self._obb = Box.from_bounding_box(bounding_box(self._obb))

        # --------------------------------------------------------------------------
        # Check the flatness.
        # --------------------------------------------------------------------------
        is_flat = (
            self._obb.width < 0.001
            or self._obb.depth < 0.001
            or self._obb.height < 0.001
        ) and self._inflate == 0.00
        if is_flat:
            self._inflate = 0.001

        # --------------------------------------------------------------------------
        # Compute the bounding box from the found points and inflate it.
        # The inflation is needed to avoid floating point errors.
        # Private variable _inflate is used to track it during transformation.
        # --------------------------------------------------------------------------
        self._obb.transform(
            Scale.from_factors(
                [
                    (self._obb.width + self._inflate) / self._obb.width,
                    (self._obb.depth + self._inflate) / self._obb.depth,
                    (self._obb.height + self._inflate) / self._obb.height,
                ]
            )
        )

        # --------------------------------------------------------------------------
        # Orient the points back to the local frame.
        # --------------------------------------------------------------------------
        self._obb.transform(xform.inverse())

        return self._obb

    @property
    def center(self):
        return self.aabb.frame.point

    @property
    def is_support(self):
        return self._is_support

    @is_support.setter
    def is_support(self, value):
        self._is_support = value

    # ==========================================================================
    # Collision detection.
    # ==========================================================================

    def has_aabb_collision(self, other, inflate=0.00):
        """Check collision using the AABB.

        Parameters
        ----------
        other : :class:`compas.geometry.Box`
            The other element to check collision with.
        inflate : float, optional
            Move the box points outside by a given value to avoid floating point errors.
        """
        # --------------------------------------------------------------------------
        # inflate the boxes
        # --------------------------------------------------------------------------
        if inflate > 1e-3:
            self.compute_aabb(inflate)
            other.compute_aabb(inflate)

        # --------------------------------------------------------------------------
        # aabb collision
        # --------------------------------------------------------------------------
        collision_x_axis = self._aabb.corner(6)[0] < other._aabb.corner(0)[0] or other._aabb.corner(6)[0] < self._aabb.corner(0)[0]  # type: ignore
        collision_y_axis = self._aabb.corner(6)[1] < other._aabb.corner(0)[1] or other._aabb.corner(6)[1] < self._aabb.corner(0)[1]  # type: ignore
        collision_z_axis = self._aabb.corner(6)[2] < other._aabb.corner(0)[2] or other._aabb.corner(6)[2] < self._aabb.corner(0)[2]  # type: ignore
        aabb_collision = not (collision_x_axis or collision_y_axis or collision_z_axis)
        if not aabb_collision:
            return False

    def has_obb_collision(self, other, inflate=0.00):
        """Check collision using the OBB.

        Parameters
        ----------
        other : :class:`compas.geometry.Box`
            The other element to check collision with.
        inflate : float, optional
            Move the box points outside by a given value to avoid floating point errors.
        """
        # --------------------------------------------------------------------------
        # inflate the boxes
        # --------------------------------------------------------------------------
        if inflate > 1e-3:
            self.compute_obb(inflate)
            other.compute_obb(inflate)

        # --------------------------------------------------------------------------
        # obb collision
        # --------------------------------------------------------------------------

        # point, axis, size description
        class OBB(object):
            def to_p(self, p):
                return Point(p[0], p[1], p[2])

            def __init__(self, box=[]):
                origin = (self.to_p(box[0]) + self.to_p(box[6])) * 0.5
                x_axis = self.to_p(box[1]) - self.to_p(box[0])
                y_axis = self.to_p(box[3]) - self.to_p(box[0])
                self.frame = Frame(origin, x_axis, y_axis)
                self.half_size = [0.0, 0.0, 0.0]
                self.half_size[0] = distance_point_point(box[0], box[1]) * 0.5
                self.half_size[1] = distance_point_point(box[0], box[3]) * 0.5
                self.half_size[2] = distance_point_point(box[0], box[4]) * 0.5

        # convert the eight points to a frame and half-size description
        box1 = OBB(self._obb)
        box2 = OBB(other._obb)

        # get sepratation plane
        def GetSeparatingPlane(RPos, axis, box1, box2):
            return abs(RPos.dot(axis)) > (
                abs((box1.frame.xaxis * box1.half_size[0]).dot(axis))
                + abs((box1.frame.yaxis * box1.half_size[1]).dot(axis))
                + abs((box1.frame.zaxis * box1.half_size[2]).dot(axis))
                + abs((box2.frame.xaxis * box2.half_size[0]).dot(axis))
                + abs((box2.frame.yaxis * box2.half_size[1]).dot(axis))
                + abs((box2.frame.zaxis * box2.half_size[2]).dot(axis))
            )

        # compute the obb collision
        RPos = box2.frame.point - box1.frame.point  # type: ignore

        result = not (
            GetSeparatingPlane(RPos, box1.frame.xaxis, box1, box2)
            or GetSeparatingPlane(RPos, box1.frame.yaxis, box1, box2)
            or GetSeparatingPlane(RPos, box1.frame.zaxis, box1, box2)
            or GetSeparatingPlane(RPos, box2.frame.xaxis, box1, box2)
            or GetSeparatingPlane(RPos, box2.frame.yaxis, box1, box2)
            or GetSeparatingPlane(RPos, box2.frame.zaxis, box1, box2)
            or GetSeparatingPlane(RPos, box1.frame.xaxis.cross(box2.frame.xaxis), box1, box2)  # type: ignore
            or GetSeparatingPlane(RPos, box1.frame.xaxis.cross(box2.frame.yaxis), box1, box2)  # type: ignore
            or GetSeparatingPlane(RPos, box1.frame.xaxis.cross(box2.frame.zaxis), box1, box2)  # type: ignore
            or GetSeparatingPlane(RPos, box1.frame.yaxis.cross(box2.frame.xaxis), box1, box2)  # type: ignore
            or GetSeparatingPlane(RPos, box1.frame.yaxis.cross(box2.frame.yaxis), box1, box2)  # type: ignore
            or GetSeparatingPlane(RPos, box1.frame.yaxis.cross(box2.frame.zaxis), box1, box2)  # type: ignore
            or GetSeparatingPlane(RPos, box1.frame.zaxis.cross(box2.frame.xaxis), box1, box2)  # type: ignore
            or GetSeparatingPlane(RPos, box1.frame.zaxis.cross(box2.frame.yaxis), box1, box2)  # type: ignore
            or GetSeparatingPlane(RPos, box1.frame.zaxis.cross(box2.frame.zaxis), box1, box2)  # type: ignore
        )

        return result

    def has_collision(self, other, inflate=0.00):
        """Check collision using the AABB and OBB attributes.
        This function can be used as a callback for tree searches or as is.
        It is also recommended to use box collision first before checking high-resolution collisions.
        The translation from C++ to Python was done following this discussion:
        https://discourse.mcneel.com/t/box-contains-box-check-for-coincident-boxes/59642/19
        For more performance check: https://github.com/rohan-sawhney/fcpw

        Parameters
        ----------
        other : :class:`compas_model.elements.Element`
            The other element to check collision with.
        inflate : float, optional
            Move the box points outside by a given value to avoid floating point errors.

        Returns
        -------
        bool
            True if there is a collision, False otherwise."""

        if self.has_aabb_collision(other, inflate):
            return True

        return self.has_obb_collision(other, inflate)

    # ==========================================================================
    # Transformations
    # ==========================================================================

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

        # --------------------------------------------------------------------------
        # attributes that are dependent on a user given specifc data or geometry
        # --------------------------------------------------------------------------
        self.compute_aabb()
        self.compute_obb()

    def transformed(self, transformation):
        """Creates a transformed copy of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`:
            The transformation to be applied to the copy of an element.

        Returns
        -------
        :class:`compas_model.elements.Element`
            A new instance of the Element with the specified transformation applied.

        """
        new_instance = self.copy()
        new_instance.transform(transformation)
        return new_instance

    # ==========================================================================
    # Printing
    # ==========================================================================

    def __repr__(self):
        return """{0} {1}""".format(self.name, self.guid)

    def __str__(self):
        return self.__repr__()
