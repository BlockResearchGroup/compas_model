from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.data import Data
from compas.geometry import (
    Frame,
    Vector,
    Transformation,
    Polyline,
    Point,
    Box,
    Line,
    Pointcloud,
    bounding_box,
    distance_point_point,
    centroid_points,
    centroid_polyhedron,
    volume_polyhedron,
)

from compas.datastructures import Mesh
from copy import deepcopy
from collections import OrderedDict
from compas_model.elements.element_type import ElementType


class Element(Data):
    """Class representing a structural object.

    Parameters
    ----------
    name : :class:`compas_model.elements.ElementType` or str, optional
        Name of the element, e.g., ElementType.block. If you have a custom element type, you can define it as a string e.g. "BLOCK".
    frame : :class:`compas.geometry.Frame`, optional
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`. There is also a global frame stored as an attribute.
    geometry_simplified : Any, optional
        Minimal geometrical represetation of an object. For example a :class:`compas.geometry.Polyline` that can represent: a point, a line or a polyline.
    geometry : Any, optional
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    kwargs (dict, optional):
        Additional keyword arguments.

    Attributes
    ----------
    id : list[int]
        Index of the object, if not defined, it is [-1]. The attribute is defined as a list to keep grouping information e.g. [0,1].
    key : str
        Guid of the class object as a string.
    frame_global : :class:`compas.geometry.Frame`
        Global coordinate system that can be used for the element orientation in a larger group.
    insertion : :class:`compas.geometry.Vector`
        Direction of the element.
    aabb : list[:class:`compas.geometry.Point`]:
        A list of eight points defining the axis-aligned-bounding-box.
    oobb : list[:class:`compas.geometry.Point`]:
        A list of eight points defining the object-oriented-bounding-box.
    aabb_mesh : :class:`compas.datastructures.Mesh`
        A mesh computed from the eight points of axis-aligned-bounding-box.
    oobb_mesh : :class:`compas.datastructures.Mesh`
        A mesh computed from the eight points of orient-object-bounding-box.
    center : :class:`compas.geometry.Point`
        The center of the element. Currently the center is computed from the axis-aligned-bounding-box.
    dimensions : list[float]
        The XYZ dimensions of the ``aabb`` attributed.
    surface_area : float
        The area of the geometry. Measurement is made from the ``geometry`` meshes.
    volume : float
        The volume of the geometry. Measurement is made from the ``geometry`` meshes.
    center_of_mass : :class:`compas.geometry.Point`
        The center of mass of the geometry. Measurement is made from the ``geometry`` meshes.
    centroid : :class:`compas.geometry.Point`
        The centroid of the geometry. Measurement is made from the ``geometry`` meshes.
    is_support : bool
        Indicates whether the element is a support.
    forces : list[tuple]
        A list of Tuple(name, lines) that can be used for force vector vizualization.
    fabrication : list[tuple]
        A list of Tuple(name, geometry) information that can be used for fabrication geometry vizualization.

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
        super(Element, self).__init__()

        # --------------------------------------------------------------------------
        # Set the element name.
        # --------------------------------------------------------------------------
        self.name = name.lower() if name else ElementType.UNKNOWN

        # --------------------------------------------------------------------------
        # Set the base frame of the element.
        # --------------------------------------------------------------------------
        self.frame = frame.copy() if frame else Frame.worldXY()

        # --------------------------------------------------------------------------
        # Check if simplified and representation geometries are provided.
        # --------------------------------------------------------------------------
        if not geometry_simplified or not geometry:
            raise AssertionError(
                "User must define a simplified geometry and the representation geometry."
            )

        # --------------------------------------------------------------------------
        # Copy geometries to avoid transformation issues.
        # --------------------------------------------------------------------------
        self.copy_geometry = copy_geometry
        self.geometry_simplified = self._copy_geometries(
            geometry_simplified, copy_geometry
        )
        self.geometry = self._copy_geometries(geometry, copy_geometry)

        # --------------------------------------------------------------------------
        # Set custom attributes given by the user.
        # --------------------------------------------------------------------------
        self.attributes = {}
        self.attributes.update(kwargs)

        # Compute AABB and OBB.
        self.compute_aabb(0.00)
        self.compute_oobb(0.00)

    def _copy_geometries(self, geometries, copy_flag):
        """
        Helper function to copy geometries.

        Returns
        -------
        list
        """
        return (
            [g.copy() if g and copy_flag else g for g in geometries]
            if isinstance(geometries, list)
            else [geometries.copy()]
            if copy_flag
            else [geometries]
        )

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
            "frame_global": self.frame_global,
            "forces": self.forces,
            "fabrication": self.fabrication,
            "is_support": self.is_support,
            "attributes": self.attributes,
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
            **data["attributes"],
        )

        obj.id = data["id"]
        obj.insertion = data["insertion"]
        obj.forces = data["forces"]
        obj.fabrication = data["fabrication"]
        obj.frame_global = data["frame_global"]
        obj.is_support = data["is_support"]

        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        obj.display_schema = OrderedDict(data["display_schema"].items())

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def id(self):
        if not hasattr(self, "_id"):
            self._id = [-1]
        return self._id

    @id.setter
    def id(self, value):
        self._id = [value] if isinstance(value, int) else value

    @property
    def key(self):
        return str(self.guid)

    @property
    def frame_global(self):
        if not hasattr(self, "_frame_global"):
            self._frame_global = Frame.worldXY()
        return self._frame_global

    @frame_global.setter
    def frame_global(self, value):
        self._frame_global = value

    @property
    def insertion(self):
        if not hasattr(self, "_insertion"):
            self._insertion = Vector(0, 0, 1)
        return self._insertion

    @insertion.setter
    def insertion(self, value):
        self._insertion = value

    @property
    def aabb(self):
        if not hasattr(self, "_aabb"):
            self.compute_aabb()
        return self._aabb

    @property
    def oobb(self):
        if not hasattr(self, "_oobb"):
            self.compute_oobb()
        return self._oobb

    def _get_geometry_points(self):
        """Get points from the geometry attribute."""
        points = []
        for i in range(len(self.geometry)):
            if isinstance(self.geometry[i], Mesh):
                points.extend(list(self.geometry[i].vertices_attributes("xyz")))
            elif isinstance(self.geometry[i], Polyline):
                points.extend(self.geometry[i])
            elif isinstance(self.geometry[i], Line):
                points.extend([self.geometry[i].start, self.geometry[i].end])
            elif isinstance(self.geometry[i], Box):
                for j in range(8):
                    points.append(self.geometry[i].corner(j))
            elif isinstance(self.geometry[i], Pointcloud):
                points.extend(self.geometry[i].points)
            elif isinstance(self.geometry[i], Point):
                points.extend([self.geometry[i]])

        if len(points) < 2:
            raise AssertionError(
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
        points_bbox = self._get_geometry_points()

        # --------------------------------------------------------------------------
        # Compute the bounding box from the found points and inflate it.
        # The inflation is needed to avoid floating point errors.
        # Private variable _inflate is used to track it during transformation.
        # --------------------------------------------------------------------------
        points_bbox = bounding_box(points_bbox)

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
        # Inflate the box.
        # --------------------------------------------------------------------------
        self._oobb = bounding_box(
            [
                [
                    self._oobb[0][0] - inflate,
                    self._oobb[0][1] - inflate,
                    self._oobb[0][2] - inflate,
                ],
                [
                    self._oobb[6][0] + inflate,
                    self._oobb[6][1] + inflate,
                    self._oobb[6][2] + inflate,
                ],
            ]
        )

        # --------------------------------------------------------------------------
        # Orient the points back to the local frame.
        # --------------------------------------------------------------------------
        for i in range(len(self._oobb)):
            point = Point(*self._oobb[i])
            point.transform(xform_inv)
            self._oobb[i] = list(point)

        return self._oobb

    @property
    def aabb_mesh(self):
        aabb = self.aabb
        aabb_mesh = Mesh.from_vertices_and_faces(
            aabb,
            [
                [0, 1, 2, 3],
                [4, 5, 6, 7],
                [0, 1, 5, 4],
                [1, 2, 6, 5],
                [2, 3, 7, 6],
                [3, 0, 4, 7],
            ],
        )
        return aabb_mesh

    @property
    def oobb_mesh(self):
        oobb = self.oobb
        oobb_mesh = Mesh.from_vertices_and_faces(
            oobb,
            [
                [0, 1, 2, 3],
                [4, 5, 6, 7],
                [0, 1, 5, 4],
                [1, 2, 6, 5],
                [2, 3, 7, 6],
                [3, 0, 4, 7],
            ],
        )
        return oobb_mesh

    @property
    def center(self):
        points = self.aabb
        return Point(
            (points[0][0] + points[6][0]) / 2,
            (points[0][1] + points[6][1]) / 2,
            (points[0][2] + points[6][2]) / 2,
        )

    @property
    def dimensions(self):
        eight_points = self.oobb
        width = distance_point_point(eight_points[0], eight_points[1])  # type: ignore
        length = distance_point_point(eight_points[0], eight_points[3])  # type: ignore
        height = distance_point_point(eight_points[0], eight_points[4])  # type: ignore
        self._dimensions = [width, length, height]
        return self._dimensions

    @property
    def surface_area(self):
        self._surface_area = 0.0
        for mesh in self.geometry:
            if isinstance(mesh, Mesh):
                self._surface_area += mesh.area()
        return self._surface_area

    @property
    def volume(self):
        self._volume_area = 0.0
        for mesh in self.geometry:
            if isinstance(mesh, Mesh):
                vertex_index = {
                    vertex: index
                    for index, vertex in enumerate(self.geometry[0].vertices())
                }
                vertices = [
                    self.geometry[0].vertex_coordinates(vertex)
                    for vertex in self.geometry[0].vertices()
                ]
                faces = [
                    [
                        vertex_index[vertex]
                        for vertex in self.geometry[0].face_vertices(face)
                    ]
                    for face in self.geometry[0].faces()
                ]
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
                vertex_index = {
                    vertex: index
                    for index, vertex in enumerate(self.geometry[0].vertices())
                }
                vertices = [
                    self.geometry[0].vertex_coordinates(vertex)
                    for vertex in self.geometry[0].vertices()
                ]
                faces = [
                    [
                        vertex_index[vertex]
                        for vertex in self.geometry[0].face_vertices(face)
                    ]
                    for face in self.geometry[0].faces()
                ]
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
        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        if not hasattr(self, "_display_schema"):

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
                            "edges": True,
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
                            "opacity": 0.5,
                            "edges": True,
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
                            "edges": True,
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
                            "edges": True,
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
                            "edges": True,
                            "is_visible": False,
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

    @display_schema.setter
    def display_schema(self, value):
        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        self._display_schema = value

    # ==========================================================================
    # Structure and Fabrication Attributes.
    # ==========================================================================

    @property
    def forces(self):
        if not hasattr(self, "_forces"):
            self._forces = []
        return self._forces

    @forces.setter
    def forces(self, value):
        if isinstance(value, list):
            self._forces = value
        else:
            raise TypeError("Forces is not of type dict.")

    def add_forces(self, name, points=[], vectors=[], thickness=10, color=[1, 0, 0]):
        """Add forces for the vizualization."""

        # --------------------------------------------------------------------------
        # Add lines as attribute.
        # --------------------------------------------------------------------------
        lines = []
        for point, vector in zip(points, vectors):
            if vector.length < 1e-3:
                continue
            line = Line(point, point + vector)
            lines.append(line)

        self.forces.append((name, lines))

        # --------------------------------------------------------------------------
        # Add forces to the display
        # --------------------------------------------------------------------------
        self.display_schema[name] = {
            "linecolor": color,
            "linewidth": thickness,
        }

    @property
    def fabrication(self):
        if not hasattr(self, "_fabrication"):
            self._fabrication = []
        return self._fabrication

    @fabrication.setter
    def fabrication(self, value):
        if isinstance(value, list):
            self._fabrication = value
        else:
            raise TypeError("Fabrication is not of type dict.")

    def add_fabrication(
        self, name, geometry, parameters, thickness=10, color=[1, 0, 0]
    ):
        """Add fabrication for the vizualization."""

        # --------------------------------------------------------------------------
        # Add fabrication to the display
        # --------------------------------------------------------------------------
        self.fabrication[name] = {
            "geometry": geometry,
            "parameters": parameters,
        }

        # --------------------------------------------------------------------------
        # Add forces to the display
        # --------------------------------------------------------------------------
        self.display_schema[name] = {
            "linecolor": color,
            "linewidth": thickness,
        }

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
            # print(RPos, axis)
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

        """
        # copy main properties
        new_instance = self.__class__(
            name=self.name,
            frame=self.frame,
            geometry_simplified=self.geometry_simplified,
            geometry=self.geometry,
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

        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        new_instance._display_schema = deepcopy(self.display_schema)

        return new_instance

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
        self.frame_global.transform(transformation)

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

    def transform_to_frame(self, target_frame):
        """Applies frame_to_frame transformation to the geometry using the frame attribute.

        Parameters
        ----------
        frame : :class:`compas.geometry.Frame`
            The target frame to which the Element will be transformed.

        Returns
        -------
        None

        """
        xform = Transformation.from_frame_to_frame(self.frame, target_frame)
        self.transform(xform)

    def transform_from_frame_to_frame(self, source_frame, target_frame):
        """Applies frame_to_frame transformation to the geometry from souce_frame to target_frame.

        Parameters
        ----------
        source_frame : :class:`compas.geometry.Frame`
            frame from which the Element will be transformed.
        target_frame : :class:`compas.geometry.Frame`
            frame to which the Element will be transformed.

        Returns
        -------
        None

        """
        xform = Transformation.from_frame_to_frame(source_frame, target_frame)
        self.transform(xform)

    def transformed_to_frame(self, frame):
        """Creates an oriented copy of the object.

        Parameters
        ----------
        frame : :class:`compas.geometry.Frame`
            The target frame to which the Element will be transformed.

        Returns
        -------
        :class:`compas_model.elements.Element`

        """
        new_instance = self.copy()
        new_instance.transform_to_frame(frame)
        return new_instance

    def transformed_from_frame_to_frame(self, source_frame, target_frame):
        """Creates a copy of the object and transforms it from the source_frame to the target_frame.

        Parameters
        ----------
        source_frame : :class:`compas.geometry.Frame`
            frame from which the Element will be transformed.
        target_frame : :class:`compas.geometry.Frame`
            frame to which the Element will be transformed.

        Returns
        -------
        :class:`compas_model.elements.Element`

        """
        new_instance = self.copy()
        new_instance.transform_from_frame_to_frame(source_frame, target_frame)
        return new_instance

    # ==========================================================================
    # Constructors
    # ==========================================================================

    @classmethod
    def from_frame(cls, width, height, depth, frame=None):
        """method create a frame element at the origin point with the frame at worldXY"""
        box = Box.from_width_height_depth(width, height, depth)
        v, f = box.to_vertices_and_faces()
        mesh = Mesh.from_vertices_and_faces(v, f)
        element = Element(
            name=ElementType.UNKNOWN,
            frame=Frame.worldXY(),
            geometry_simplified=Line(Point(-width, 0, 0), Point(width, 0, 0)),
            geometry=mesh,
        )
        if frame:
            element.transform_to_frame(frame)
        return element

    @classmethod
    def from_box_dimensions(cls, width, height, depth, frame=None):
        """Method create a frame element at the origin point with the frame at worldXY."""
        box = Box.from_width_height_depth(width, height, depth)
        v, f = box.to_vertices_and_faces()
        mesh = Mesh.from_vertices_and_faces(v, f)
        my_frame = frame if frame else Frame.worldXY()

        element = Element(
            name=ElementType.UNKNOWN,
            frame=my_frame,
            geometry_simplified=Line(Point(-width, 0, 0), Point(width, 0, 0)),
            geometry=mesh,
        )
        if frame:
            element.transform_to_frame(frame)
        return element

    # ==========================================================================
    # Printing
    # ==========================================================================

    def __repr__(self):
        return """{0} {1}""".format(self.name, self.guid)

    def __str__(self):
        return self.__repr__()
