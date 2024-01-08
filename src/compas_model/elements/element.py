from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.scene import SceneObject
from compas.scene import GeometryObject
from compas.scene.descriptors.color import ColorAttribute

from compas.data import Data
from compas.geometry import (
    Frame,
    Vector,
    Transformation,
    Polyline,
    Point,
    Box,
    Line,
    Polygon,
    Pointcloud,
    bounding_box,
    distance_point_point,
    centroid_points,
    centroid_polyhedron,
    volume_polyhedron,
)

from compas.datastructures import Mesh
from collections import OrderedDict


class Element(Data):
    """Class representing a structural object.

    Parameters
    ----------
    name : str, optional
        Name of the element
    frame : :class:`compas.geometry.Frame`, optional
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`. There is also a global frame stored as an attribute.
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
    insertion : :class:`compas.geometry.Vector`
        Direction of the element.
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

    Examples
    --------
    >>> frame = Frame([3, 0, 0], [0.866, 0.1, 0.0], [0.5, 0.866, 0.0])
    >>> box = Box(frame=frame, xsize=2, ysize=4, zsize=0.25)
    >>> element = Element("BLOCK", Frame.worldXY(), Point(0,0,0), box)
    >>> element.insertion = Vector(0, 0, 1)

    """

    pointcolor = ColorAttribute()
    linecolor = ColorAttribute()
    surfacecolor = ColorAttribute()

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
        self._oobb = None
        self._inflate = 0.0
        self._id = -1
        self._insertion = Vector(0, 0, 1)

    def _copy_geometries(self, geometries, copy_flag):
        """
        Helper function to copy geometries.

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

        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        data["display_schema"] = self.display_schema

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

        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        obj.display_schema = OrderedDict(data["display_schema"].items())

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = [value] if isinstance(value, int) else value

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
    def oobb(self):
        if not self._oobb:
            self._oobb = self.compute_oobb()
        return self._oobb

    def _get_geometry_points(self):
        """Get points from the geometry attribute.

        Returns
        -------
        list[:class:`compas.geometry.Point`]
            The points of the geometry.

        Raises
        ------
        ValueError
            If the geometry is not a Mesh, Polyline, Line, Box, Pointcloud or Point.

        """
        points = []
        for i in range(len(self.geometry)):
            if isinstance(self.geometry[i], Mesh):
                points += list(self.geometry[i].vertices_attributes("xyz"))
            elif isinstance(self.geometry[i], Polyline):
                points += self.geometry[i]
            elif isinstance(self.geometry[i], Polygon):
                points += self.geometry[i].points
            elif isinstance(self.geometry[i], Line):
                points += [self.geometry[i].start, self.geometry[i].end]
            elif isinstance(self.geometry[i], Box):
                for j in range(8):
                    points.append(self.geometry[i].corner(j))
            elif isinstance(self.geometry[i], Pointcloud):
                points += self.geometry[i].points
            elif isinstance(self.geometry[i], Point):
                points += [self.geometry[i]]

        if len(points) < 2:
            raise ValueError(
                "Geometry is neither a Mesh, Polyline, Line, Box, Pointcloud or Point, consider defining your own Element class implementation and override this method."
            )

        return points

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
        # Retrieve point coordinates from the most common geometry types.
        # --------------------------------------------------------------------------
        points_bbox = self._get_geometry_points()

        # --------------------------------------------------------------------------
        # Compute the bounding box from the found points and inflate it.
        # The inflation is needed to avoid floating point errors.
        # Private variable _inflate is used to track it during transformation.
        # --------------------------------------------------------------------------
        points_bbox = bounding_box(points_bbox)

        # --------------------------------------------------------------------------
        # Check if elements are not flat.
        # --------------------------------------------------------------------------
        xaxis = Vector.from_start_end(points_bbox[0], points_bbox[1])
        yaxis = Vector.from_start_end(points_bbox[0], points_bbox[3])
        zaxis = Vector.from_start_end(points_bbox[0], points_bbox[4])
        is_flat = (
            xaxis.length < 0.001 or yaxis.length < 0.001 or zaxis.length < 0.001
        ) and self._inflate == 0.00
        if is_flat:
            self._inflate = 0.001

        # --------------------------------------------------------------------------
        # Create inflated box.
        # --------------------------------------------------------------------------
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
        points = self._get_geometry_points()

        # --------------------------------------------------------------------------
        # Transform the points to the local frame and compute the bounding box.
        # --------------------------------------------------------------------------
        xform = Transformation.from_frame_to_frame(self.frame, Frame.worldXY())
        xform_inv = xform.inverse()

        self._oobb = []
        for i in range(len(points)):
            point = Point(*points[i])
            point.transform(xform)
            self._oobb.append(point)
        self._oobb = bounding_box(self._oobb)

        # --------------------------------------------------------------------------
        # Check if elements are not flat.
        # --------------------------------------------------------------------------
        xaxis = Vector.from_start_end(self._oobb[0], self._oobb[1])
        yaxis = Vector.from_start_end(self._oobb[0], self._oobb[3])
        zaxis = Vector.from_start_end(self._oobb[0], self._oobb[4])
        is_flat = (
            xaxis.length < 0.001 or yaxis.length < 0.001 or zaxis.length < 0.001
        ) and self._inflate == 0.00
        if is_flat:
            self._inflate = 0.001

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

    @property
    def center(self):
        return self.aabb.frame.point

    @property
    def area(self):
        self._area = 0.0
        for mesh in self.geometry:
            if isinstance(mesh, Mesh):
                self._area += mesh.area()
        return self._area

    @property
    def volume(self):
        self._volume_area = 0.0
        for mesh in self.geometry:
            if isinstance(mesh, Mesh):
                vertices, faces = mesh.to_vertices_and_faces()
                self._volume_area += volume_polyhedron((vertices, faces))
        return self._volume_area

    @property
    def center_of_mass(self):
        sum_of_points = [0, 0, 0]
        count = 0
        for g in self.geometry:
            # --------------------------------------------------------------------------
            # get centroid from all meshes
            # --------------------------------------------------------------------------
            if isinstance(g, Mesh):
                vertices, faces = g.to_vertices_and_faces()
                self._center_of_mass = centroid_polyhedron((vertices, faces))
                sum_of_points = [
                    sum_of_points[i] + self._center_of_mass[i] for i in range(3)
                ]
                count += 1

        # --------------------------------------------------------------------------
        # return the avarege of all centroids
        # --------------------------------------------------------------------------
        self._center_of_mass = [sum_of_points[i] / count for i in range(3)]
        return self._center_of_mass

    @property
    def centroid(self):
        x_sum = 0.0
        y_sum = 0.0
        z_sum = 0.0
        count = 0

        for g in self.geometry:
            # --------------------------------------------------------------------------
            # get centroid from all meshes
            # --------------------------------------------------------------------------
            if isinstance(g, Mesh):
                x, y, z = centroid_points(
                    [g.vertex_coordinates(key) for key in g.vertices()]
                )
                x_sum += x
                y_sum += y
                z_sum += z
                count += 1

        # --------------------------------------------------------------------------
        # return the avarege of all centroids
        # --------------------------------------------------------------------------
        self._centroid = Point(x_sum / count, y_sum / count, z_sum / count)
        return self._centroid

    @property
    def is_support(self):
        if not hasattr(self, "_is_support"):
            self._is_support = False
        return self._is_support

    @is_support.setter
    def is_support(self, value):
        self._is_support = value

    @property
    def display_schema(self):
        face_color = [0.9, 0.9, 0.9] if not self.is_support else [0.968, 0.615, 0.517]

        return OrderedDict(
            [
                ("geometry_simplified", {"is_visible": True}),
                (
                    "geometry",
                    {"facecolor": face_color, "opacity": 0.75, "is_visible": True},
                ),
                ("frame", {}),
                ("aabb", {"opacity": 0.25}),
                ("oobb", {"opacity": 0.25}),
            ]
        )

    @display_schema.setter
    def display_schema(self, value):
        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        self._display_schema = value

    # ==========================================================================
    # Methods
    # ==========================================================================

    def has_collision(self, other, inflate=0.00):
        """Check collision by the aabb and oobb attributes.
        This function is could be used as a call-back for tree searches or as is.
        Also it is often recommend use box collision before, high resolution collision are checked.
        Translation from C++ to Python was made following this discussion:
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

        # --------------------------------------------------------------------------
        # inflate the boxes
        # --------------------------------------------------------------------------
        if inflate > 1e-3:
            self.compute_aabb(inflate)
            self.compute_oobb(inflate)
            other.compute_aabb(inflate)
            other.compute_oobb(inflate)

        # --------------------------------------------------------------------------
        # aabb collision
        # --------------------------------------------------------------------------
        collision_x_axis = self._aabb[6][0] < other._aabb[0][0] or other._aabb[6][0] < self._aabb[0][0]  # type: ignore
        collision_y_axis = self._aabb[6][1] < other._aabb[0][1] or other._aabb[6][1] < self._aabb[0][1]  # type: ignore
        collision_z_axis = self._aabb[6][2] < other._aabb[0][2] or other._aabb[6][2] < self._aabb[0][2]  # type: ignore
        aabb_collision = not (collision_x_axis or collision_y_axis or collision_z_axis)
        if not aabb_collision:
            return False

        # --------------------------------------------------------------------------
        # oobb collision
        # --------------------------------------------------------------------------

        # point, axis, size description
        class OBB:
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
        box1 = OBB(self._oobb)
        box2 = OBB(other._oobb)

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

        # compute the oobb collision
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

    # def copy(self):
    #     """Makes an independent copy of all properties of this class.

    #     Parameters
    #     ----------
    #     all_attributes : bool, optional
    #         If True, all attributes are copied.
    #         If False, only the main properties are copied.

    #     Returns
    #     -------
    #     :class:`compas_model.elements.Element`

    #     """
    #     # copy main properties
    #     new_instance = self.__class__(
    #         name=self.name,
    #         frame=self.frame,
    #         geometry_simplified=self.geometry_simplified,
    #         geometry=self.geometry,
    #         **self.attributes,
    #     )

    #     # --------------------------------------------------------------------------
    #     # The attributes that are dependent on user given specifc data or geometry.
    #     # --------------------------------------------------------------------------
    #     new_instance.id = list(self.id)
    #     new_instance.insertion = Vector(
    #         self.insertion[0], self.insertion[1], self.insertion[2]
    #     )
    #     new_instance.frame_global = self.frame_global.copy()

    #     # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
    #     new_instance._display_schema = deepcopy(self.display_schema)

    #     return new_instance

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
        self.compute_oobb()

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
