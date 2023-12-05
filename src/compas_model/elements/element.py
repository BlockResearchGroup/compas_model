from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.data import Data
from compas.geometry import (
    Frame,
    Plane,
    Vector,
    Geometry,
    Transformation,
    Polyline,
    Polygon,
    Point,
    Box,
    Line,
    Pointcloud,
    bounding_box,
    convex_hull,
    distance_point_point,
    cross_vectors,
    centroid_points,
    distance_point_plane_signed,
    intersection_plane_plane_plane,
    centroid_polyhedron,
    volume_polyhedron,
)
from compas.datastructures import Mesh, mesh_bounding_box
import copy
from collections import OrderedDict


class Element(Data):

    """Class representing a structural object of an assembly.

    Parameters
    ----------
        name : str
            e.g., "BLOCK", "BEAM", "FRAME"
            to be consistent majority of names are stored in ELEMENT_NAME class
        id : list[int] or int
            unique identifier/s , e.g.,0 or [0] or [0, 1] or [1, 5, 9].
            one object can have an index and belong to a group/s
        frame : :class:`~compas.geometry.Frame`
            local frame of the element
            there is also a global frame stored as an attribute
        geometry_simplified : list[:class:`~compas.geometry.Polyline`]
            minimal geometrical represetation of an object
            type is a polyline since it can represent: a point, a line or a polyline
        geometry : list[any]
            a list of geometries used for the element visualization
            currently supported types: :class:`~compas.geometry` or :class:`~compas.datastrcutures.Mesh`
        insertion : list[:class:`~compas.geometry.Vector`, int]
            direction of the element, often defined by a single vector (can be also a sequence)
            and an index in an insertion sequence
        kwargs (dict, optional):
            additional keyword arguments can be passed to the element.

    Attributes
    ----------
        frame_global : :class:`~compas.geometry.Frame`
            global plane that can be used for the element orientation in a larger assembly
        aabb : list[:class:`~compas.geometry.Point`]:
            a list of XYZ coordinates defining the bounding box for collision detection.
        oobb : list[:class:`~compas.geometry.Point`]:
            a list of XYZ coordinates defining the an oriented bounding box to the frame.
        convex_hull : list[:class:`~compas.datastrcutures.Mesh`]:
            a mesh computed from the geometry geometries points
        area : float
            the surface are of an element based on geometry geometry
        volume : float
            the volume of an element based on geometry 3d geometry

    Examples
    --------
        >>> element = Element("BLOCK", 0, Frame.worldXY(), Point(0,0,0), \
                            Box( \
                                frame=Frame([3, 0, 0], [0.866, 0.1, 0.0], [0.5, 0.866, 0.0]), \
                                xsize=2, ysize=4, zsize=0.25), \
                            [Vector(0, 0, 1), 0])
    """

    def __init__(
        self,
        name=None,
        id=None,
        frame=None,
        geometry_simplified=None,
        geometry=None,
        insertion=None,
        **kwargs
    ):
        # --------------------------------------------------------------------------
        # call the inherited Data constructor for json serialization
        # --------------------------------------------------------------------------
        super(Element, self).__init__()

        # --------------------------------------------------------------------------
        # name
        # the string can be any string
        # but better use the existing container: compas_assembly2.ELEMENT_NAME.BLOCK
        # --------------------------------------------------------------------------
        if not name:
            self.name = "CUSTOM"
        else:
            self.name = name.upper()

        # --------------------------------------------------------------------------
        # indexing
        # indices are store as a list to keep grouping information e.g. [0,1]
        # --------------------------------------------------------------------------
        if id is None:
            self.id = [-1]
        else:
            self.id = [id] if isinstance(id, int) else id

        # --------------------------------------------------------------------------
        # orientation frames
        # if user does not give a frame, try to define it based on geometry_simplified
        # --------------------------------------------------------------------------
        if frame:
            if isinstance(frame, Frame):
                self.frame = Frame.copy(frame)
            else:
                origin = [0, 0, 0]
                if isinstance(geometry_simplified[0], Point):  # type: ignore
                    origin = geometry_simplified[0]  # type: ignore
                elif isinstance(geometry_simplified[0], Line):  # type: ignore
                    origin = geometry_simplified[0].start  # type: ignore
                elif isinstance(geometry_simplified[0], Polyline):  # type: ignore
                    origin = geometry_simplified[0][0]  # type: ignore
                elif isinstance(geometry_simplified[0], (int, float)) and len(geometry_simplified) == 3:  # type: ignore
                    origin = geometry_simplified
                self.frame = Frame(origin, [1, 0, 0], [0, 1, 0])
        else:
            self.frame = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])

        # --------------------------------------------------------------------------
        # minimal representation and geometrical shapes
        # iterate through the input geometry
        # check if they are valid geometry objects
        # duplicate them and add them geometry list to avoid transformation issues
        # geometry, can be meshes, breps, curves, points, etc.
        # --------------------------------------------------------------------------
        self.geometry_simplified = []
        if geometry_simplified:
            if isinstance(geometry_simplified, list):
                # input - list of numbers, means user gives a point (most probably)
                if (
                    isinstance(geometry_simplified[0], (int, float))
                    and len(geometry_simplified) == 3
                ):
                    self.geometry_simplified.append(
                        Point(
                            geometry_simplified[0],
                            geometry_simplified[1],
                            geometry_simplified[2],
                        )
                    )
                # input - list of gometries
                else:
                    for g in geometry_simplified:
                        if isinstance(g, Geometry) or isinstance(g, Mesh):
                            self.geometry_simplified.append(g.copy())
                        elif isinstance(g, list):
                            if len(g) == 3:
                                self.geometry_simplified.append(Point(g[0], g[1], g[2]))
            else:
                # input - one geometry
                if isinstance(geometry_simplified, Geometry):
                    self.geometry_simplified.append(geometry_simplified.copy())

            if len(geometry_simplified) == 0:  # type: ignore
                raise AssertionError("User must define a simple geometry")

        # --------------------------------------------------------------------------
        # display geometry - geometry, can be meshes, breps, curves, pointcloud, etc.
        # --------------------------------------------------------------------------
        self.geometry = []
        if geometry:
            # input - list of gometries
            if isinstance(geometry, list):
                for g in geometry:
                    if isinstance(g, Geometry) or isinstance(g, Mesh):
                        self.geometry.append(g.copy())
            # input - one geometry
            else:
                if isinstance(geometry, Geometry) or isinstance(geometry, Mesh):
                    self.geometry.append(geometry.copy())

        # --------------------------------------------------------------------------
        # insertion direction and index in a sequnece
        # the insertion direction can be a vector, but also a polyline, plane...
        # the index is always integer
        # --------------------------------------------------------------------------
        is_insertion_valid = False
        if insertion:
            if isinstance(insertion, list):
                # input - list of vector
                if len(insertion) == 1:
                    if isinstance(insertion[0], Vector):
                        self.insertion = insertion[0]
                        is_insertion_valid = True
                # input - list of vector coordinates in one list
                elif len(insertion) == 3:
                    self.insertion = Vector(insertion[0], insertion[1], insertion[2])
                    is_insertion_valid = True
            elif isinstance(insertion, Vector):
                # input - vector
                self.insertion = insertion
                is_insertion_valid = True

        if not is_insertion_valid:
            self.insertion = Vector(0, 0, 1)

        # --------------------------------------------------------------------------
        # custom attributes given by the user
        # --------------------------------------------------------------------------
        self.attributes = {}  # set the attributes of an object
        self.attributes.update(kwargs)  # update the attributes of with the kwargs

        # --------------------------------------------------------------------------
        # compute aabb and oobb, since most of the time they are used
        # --------------------------------------------------------------------------
        self.aabb(0.00)
        self.oobb(0.00)

    # ==========================================================================
    # DISPLAY
    # ==========================================================================
    @property
    def display_schema(self):
        """Display schema of the element.

        Returns
        -------
        dict
            The display schema of the element.

        """
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
                    },
                ),
                (
                    "geometry",
                    {
                        "facecolor": [0.9, 0.9, 0.9],
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 1,
                        "opacity": 0.75,
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
                (
                    "convex_hull",
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

        return ordered_dict

    # ==========================================================================
    # SERIALIZATION
    # ==========================================================================

    @property
    def data(self):
        # create the data object from the class properties
        # call the inherited Data constructor for json serialization
        data = {
            "name": self.name,
            "id": self.id,
            "frame": self.frame,
            "geometry_simplified": self.geometry_simplified,
            "geometry": self.geometry,
            "insertion": self.insertion,
            "attributes": self.attributes,
        }

        # custom properties
        data["frame_global"] = self.frame_global
        data["aabb"] = self.aabb()
        data["oobb"] = self.oobb()
        data["convex_hull"] = self.convex_hull
        data["fabrication"] = self.fabrication
        data["structure"] = self.structure

        return data

    @classmethod
    def from_data(cls, data):
        """Alternative to None default __init__ parameters."""
        obj = cls(
            name=data["name"],
            id=data["id"],
            frame=data["frame"],
            geometry_simplified=data["geometry_simplified"],
            geometry=data["geometry"],
            insertion=None,
            **data["attributes"],
        )

        if data.get("insertion", None) is not None:
            obj.insertion = data["insertion"]

        # custom properties
        obj._frame_global = data["frame_global"]
        obj._aabb = data["aabb"]
        obj._oobb = data["oobb"]
        obj._convex_hull = data["convex_hull"]
        obj._fabrication = data["fabrication"]
        obj._structure = data["structure"]

        return obj

    # ==========================================================================
    # CONSTRUCTOR OVERLOADING
    # ==========================================================================
    @classmethod
    def from_geometry_simplified_and_geometry(cls, geometry_simplified, geometry=None):
        """convert a geometry to element, when indexing and types are not important"""

        if geometry is not None:
            return Element(geometry_simplified=geometry_simplified, geometry=geometry)
        else:
            return Element(geometry_simplified=geometry_simplified)

    @classmethod
    def from_simplices_and_geometryes(cls, simplices=[], geometryes=None):
        """convert a list of geometries to elements, with assumtion that other property will be filled later"""
        elements = []

        for id, s in enumerate(simplices):
            if geometryes is list:
                elements.append(
                    Element(
                        geometry_simplified=s, geometry=geometryes[id % len(geometryes)]
                    )
                )
            else:
                elements.append(Element(geometry_simplified=s))

        # output
        return elements

    @classmethod
    def from_block(cls, mesh):
        """method create a block element at the origin point with the frame at worldXY"""
        return Element(
            name="BLOCK",
            id=-1,
            frame=Frame.worldXY,
            geometry_simplified=Point(0, 0, 0),
            geometry=mesh,
        )

    @classmethod
    def from_frame(cls, width, height, depth, frame=None):
        """method create a frame element at the origin point with the frame at worldXY"""
        box = Box.from_width_height_depth(width, height, depth)
        v, f = box.to_vertices_and_faces()
        mesh = Mesh.from_vertices_and_faces(v, f)
        element = Element(
            name="BEAM",
            id=0,
            frame=Frame.worldXY,
            geometry_simplified=Line(Point(-width, 0, 0), Point(width, 0, 0)),
            geometry=mesh,
        )
        if frame:
            element.transform_to_frame(frame)
        return element

    @classmethod
    def from_plate(cls, polylines):
        """method create a plate element at the origin point with the frame at worldXY"""
        return Element(
            name="PLATE",
            id=0,
            frame=Frame.worldXY,
            geometry_simplified=polylines,
            geometry=polylines,
        )

    @classmethod
    def from_plate_points(cls, points0, points1, id=0, insertion=None):
        """method create a plate element at the origin point with the frame at worldXY"""

        # --------------------------------------------------------------------------
        # close polyline
        # --------------------------------------------------------------------------
        points0_copy = [Point(*point) for point in points0]
        points1_copy = [Point(*point) for point in points1]

        if distance_point_point(points0_copy[0], points0_copy[-1]) > 1e-3:
            points0_copy.append(points0_copy[0])
            points1_copy.append(points1_copy[0])

        # --------------------------------------------------------------------------
        # create mesh by lofting two outlines
        # --------------------------------------------------------------------------
        mesh, frame = _.Triagulator.from_loft_two_point_lists(
            points0_copy, points1_copy
        )

        # --------------------------------------------------------------------------
        # return the element
        # --------------------------------------------------------------------------
        return Element(
            name="PLATE",
            id=id,
            frame=frame,
            geometry_simplified=[Polyline(points0_copy), Polyline(points1_copy)],
            geometry=mesh,
        )

    @classmethod
    def from_plate_planes(
        cls, base_plane, side_planes, thickness, id=None, insertion=None
    ):
        """method create a plate element at the origin point with the frame at worldXY"""

        # --------------------------------------------------------------------------
        # intersect side planes with base plane to get a polyline)
        # --------------------------------------------------------------------------
        points0 = _.PlaneUtil.points_from_side_plane(base_plane, side_planes, 0, True)
        points1 = _.PlaneUtil.points_from_side_plane(
            base_plane, side_planes, thickness, True
        )

        # --------------------------------------------------------------------------
        # create mesh by lofting two outlines
        # --------------------------------------------------------------------------
        mesh, frame = _.Triagulator.from_loft_two_point_lists(points0, points1)

        # --------------------------------------------------------------------------
        # return the element
        # --------------------------------------------------------------------------
        return Element(
            name="PLATE",
            id=id,
            frame=frame,
            geometry_simplified=[Polyline(points0), Polyline(points1)],
            geometry=mesh,
            insertion=insertion,
        )

    # ==========================================================================
    # OPTIONAL PROPERTIES - FABRICATION AND STRUCTUTRE
    # ==========================================================================

    @property
    def fabrication(self):
        """Fabrication information e.g. subtractive, additive, nesting and etc"""

        # define this property dynamically in the class
        if not hasattr(self, "_fabrication"):
            self._fabrication = {}
        return self._fabrication

    @property
    def structure(self):
        """Structure information e.g. force vectors, minimal representation and etc"""

        # define this property dynamically in the class
        if not hasattr(self, "_structure"):
            self._structure = {}
        return self._structure

    # ==========================================================================
    # OPTIONAL PROPERTIES - MEASURE
    # ==========================================================================
    @property
    def key(self):
        """Key: guid of the Element object stored in the base Node class attributes dictionary "my_object" property
        Returns
        -------
        str
        """
        return str(self.guid)

    @property
    def dimensions(self):
        """Compute the dimensions from oriented bounding-box.

        Returns
        -------
        [float, float, float]

        """
        if hasattr(self, "_dimensions"):
            return self._dimensions
        else:
            eight_points = self.oobb()
            width = distance_point_point(eight_points[0], eight_points[1])  # type: ignore
            length = distance_point_point(eight_points[0], eight_points[3])  # type: ignore
            height = distance_point_point(eight_points[0], eight_points[4])  # type: ignore
            self._dimensions = [width, length, height]
        return self._dimensions

    @property
    def area(self):
        """Compute the area of an element by multiplying the boundingbox width and height.
        If you need surface area instead, refer to the surface_area method instead

        Returns
        -------
        float

        """
        if hasattr(self, "_area"):
            return self._area
        else:
            eight_points = self.oobb()
            width = distance_point_point(eight_points[0], eight_points[1])  # type: ignore
            length = distance_point_point(eight_points[0], eight_points[3])  # type: ignore
            self._area = width * length
        return self._area

    @property
    def surface_area(self):
        """Compute surface area of a geometry geometry.

        Returns
        -------
        float

        """

        # --------------------------------------------------------------------------
        # sanity check
        # --------------------------------------------------------------------------
        if hasattr(self, "_surface_area"):
            return self._surface_area

        if len(self.geometry) == 0:
            raise AssertionError("You must assign geometry to the element")

        if not isinstance(self.geometry[0], Mesh):
            raise AssertionError("The geometry must be a mesh")

        # --------------------------------------------------------------------------
        # assign it to the class property and return it
        # --------------------------------------------------------------------------
        self._surface_area = self.geometry[0].area()
        return self._surface_area

    @property
    def volume(self):
        """Compute the volume.

        Returns
        -------
        float
            The volume of the geometry.

        """
        # --------------------------------------------------------------------------
        # sanity check
        # --------------------------------------------------------------------------
        if hasattr(self, "_surface_area"):
            return self._volume

        if len(self.geometry) == 0:
            raise AssertionError("You must assign geometry to the element")

        if not isinstance(self.geometry[0], Mesh):
            raise AssertionError("The geometry must be a mesh")

        # --------------------------------------------------------------------------
        # compute the volume from the mesh
        # --------------------------------------------------------------------------
        vertex_index = {
            vertex: index for index, vertex in enumerate(self.geometry[0].vertices())
        }
        vertices = [
            self.geometry[0].vertex_coordinates(vertex)
            for vertex in self.geometry[0].vertices()
        ]
        faces = [
            [vertex_index[vertex] for vertex in self.geometry[0].face_vertices(face)]
            for face in self.geometry[0].faces()
        ]
        self._volume = volume_polyhedron((vertices, faces))
        return self._volume

    # ==========================================================================
    # OPTIONAL PROPERTIES - ORIENTATION
    # ==========================================================================

    @property
    def center_of_mass(self):
        """Compute the center of mass of the geometry.

        Returns
        -------
        :class:`compas.geometry.Point`

        """

        # --------------------------------------------------------------------------
        # sanity check
        # --------------------------------------------------------------------------
        if hasattr(self, "_centroid"):
            return self._center

        if len(self.geometry) == 0:
            raise AssertionError("You must assign geometry geometry to the element")

        if not isinstance(self.geometry[0], Mesh):
            raise AssertionError("The geometry must be a mesh")

        # --------------------------------------------------------------------------
        # get vertices and faces of the first mesh
        # --------------------------------------------------------------------------
        vertex_index = {
            vertex: index for index, vertex in enumerate(self.geometry[0].vertices())
        }
        vertices = [
            self.geometry[0].vertex_coordinates(vertex)
            for vertex in self.geometry[0].vertices()
        ]
        faces = [
            [vertex_index[vertex] for vertex in self.geometry[0].face_vertices(face)]
            for face in self.geometry[0].faces()
        ]

        # --------------------------------------------------------------------------
        # compute the centroid
        # --------------------------------------------------------------------------
        x, y, z = centroid_polyhedron((vertices, faces))

        # --------------------------------------------------------------------------
        # assign it to the class property and return it
        # --------------------------------------------------------------------------
        self._center = Point(x, y, z)
        return self._center

    @property
    def centroid(self):
        """Compute the centroid of the geometry.

        Returns
        -------
        :class:`compas.geometry.Point`

        """

        # --------------------------------------------------------------------------
        # sanity check
        # --------------------------------------------------------------------------
        if hasattr(self, "_centroid"):
            return self._centroid

        if len(self.geometry) == 0:
            raise AssertionError("You must assign geometry geometry to the element")

        if not isinstance(self.geometry[0], Mesh):
            raise AssertionError("The geometry must be a mesh")

        # --------------------------------------------------------------------------
        # compute the centroid
        # --------------------------------------------------------------------------
        x, y, z = centroid_points(
            [
                self.geometry[0].vertex_coordinates(key)
                for key in self.geometry[0].vertices()
            ]
        )

        # --------------------------------------------------------------------------
        # assign it to the class property and return it
        # --------------------------------------------------------------------------
        self._centroid = Point(x, y, z)
        return self._centroid

    @property
    def frame_global(self):
        """Frame that gives orientation of the element in the larger group of Elements"""

        # define this property dynamically in the class
        if not hasattr(self, "_frame_global"):
            self._frame_global = Frame([0, 0, 0], [1, 0, 0], [0, 1, 0])
        return self._frame_global

    @frame_global.setter
    def frame_global(self, value):
        """Frame that gives orientation of the element in the larger group of Elements"""
        self._frame_global = value

    # ==========================================================================
    # METHODS - COLLIDE
    # ==========================================================================
    @property
    def aabb_mesh(self):
        """Compute axis-aligned-bounding-box of all objects"""
        aabb = self.aabb()
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
        """Compute axis-aligned-bounding-box of all objects"""
        oobb = self.oobb()
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

    def aabb(self, inflate=0.00):
        """Compute bounding box based on geometry geometries points"""

        # define this property dynamically in the class
        if not hasattr(self, "_aabb"):
            self._aabb = []  # XYZ coordinates of 8 points defining a box

        # if the aabb is already computed return it
        # and the user does not give another inflation value
        if self._aabb and abs(inflate) < 0.001:
            return self._aabb

        # iterate geometry  and get the bounding box by geometry name
        # Mesh, Polyline, Box, Line
        points_bbox = []

        for i in range(len(self.geometry)):
            if isinstance(self.geometry[i], Mesh):
                corners = mesh_bounding_box(self.geometry[i])
                points_bbox.extend([corners[0], corners[6]])
            elif isinstance(self.geometry[i], Polyline):
                corners = bounding_box(self.geometry[i])
                points_bbox.extend([corners[0], corners[6]])
            elif isinstance(self.geometry[i], Line):
                points_bbox.extend([self.geometry[i].start, self.geometry[i].end])
            elif isinstance(self.geometry[i], Box):
                corners = bounding_box(self.geometry[i].points)
                points_bbox.extend([corners[0], corners[6]])
            elif isinstance(self.geometry[i], Pointcloud):
                corners = bounding_box(self.geometry[i].points)
                points_bbox.extend([corners[0], corners[6]])
            elif isinstance(self.geometry[i], Point):
                points_bbox.extend(
                    [
                        [
                            self.geometry[i][0] - (inflate + 0.001),
                            self.geometry[i][1] - (inflate + 0.001),
                            self.geometry[i][2] - (inflate + 0.001),
                        ],
                        [
                            self.geometry[i][0] + (inflate + 0.001),
                            self.geometry[i][1] + (inflate + 0.001),
                            self.geometry[i][2] + (inflate + 0.001),
                        ],
                    ]
                )

        # if no points found, return
        if len(points_bbox) < 2:
            if inflate > 0.00:
                self._aabb = bounding_box(
                    [
                        self.frame.point + Vector(inflate, inflate, inflate),  # type: ignore
                        self.frame.point - Vector(inflate, inflate, inflate),  # type: ignore
                    ]
                )
                return self._aabb
            else:
                return None

        # compute axis-aligned-bounding-box of all objects
        points_bbox = bounding_box(points_bbox)

        # inflate the box
        self._aabb = bounding_box(
            [
                [
                    points_bbox[0][0] - inflate,
                    points_bbox[0][1] - inflate,
                    points_bbox[0][2] - inflate,
                ],
                [
                    points_bbox[6][0] + inflate,
                    points_bbox[6][1] + inflate,
                    points_bbox[6][2] + inflate,
                ],
            ]
        )

        # return the aabb (8 points)
        return self._aabb

    def oobb(self, inflate=0.00):
        """Compute the oriented bounding box based on geometry geometries points"""

        # define this property dynamically in the class
        if not hasattr(self, "_oobb"):
            self._oobb = []  # XYZ coordinates of 8 points defining a box

        # if the oobb is already computed return it
        # and the user does not give another inflation value
        if self._oobb and abs(inflate) < 0.001:
            return self._oobb

        # iterate geometry and get the bounding box by geometry name
        # Mesh, Polyline, Box, Line
        points = []

        for i in range(len(self.geometry)):
            if isinstance(self.geometry[i], Mesh):
                points.extend(list(self.geometry[i].vertices_attributes("xyz")))
            elif isinstance(self.geometry[i], Polyline):
                points.extend(self.geometry[i])
            elif isinstance(self.geometry[i], Line):
                points.extend([self.geometry[i].start, self.geometry[i].end])
            elif isinstance(self.geometry[i], Box):
                points.extend(self.geometry[i].points)
            elif isinstance(self.geometry[i], Pointcloud):
                points.extend(self.geometry[i].points)

        # if no points found, return
        if len(points) < 2:
            if inflate > 0.00:
                self._oobb = bounding_box(
                    [
                        self.frame.point + Vector(inflate, inflate, inflate),  # type: ignore
                        self.frame.point - Vector(inflate, inflate, inflate),  # type: ignore
                    ]
                )
                return self._oobb
            else:
                return None

        # compute the object-oriented-bounding-box
        # transforming points from local frame to worldXY
        # compute the bbox
        # orient the points back to the local frame
        xform = Transformation.from_frame_to_frame(self.frame, Frame.worldXY())
        xform_inv = xform.inverse()

        self._oobb = []
        for i in range(len(points)):
            point = Point(*points[i])
            point.transform(xform)
            self._oobb.append(point)
        self._oobb = bounding_box(self._oobb)

        # inflate the oobb
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

        # orient the points back to the local frame
        for i in range(len(self._oobb)):
            point = Point(*self._oobb[i])
            point.transform(xform_inv)
            self._oobb[i] = list(point)

        # return the oobb  (8 points)
        return self._oobb

    def aabb_center(self, inflate=0.001):
        points = self.aabb(inflate)
        return Point(
            (points[0][0] + points[6][0]) / 2,
            (points[0][1] + points[6][1]) / 2,
            (points[0][2] + points[6][2]) / 2,
        )

    @property
    def convex_hull(self):
        """Compute convex hull from geometry points"""

        # define this property dynamically in the class
        if not hasattr(self, "_convex_hull"):
            self._convex_hull = Mesh()

        # if the convex hull is already computed return it
        if self._convex_hull.is_empty() is False:
            return self._convex_hull

        # iterate geometry and get the bounding box by geometry name
        # Mesh, Polyline, Box, Line
        points = []

        for i in range(len(self.geometry)):
            if isinstance(self.geometry[i], Mesh):
                points.extend(list(self.geometry[i].vertices_attributes("xyz")))
            elif isinstance(self.geometry[i], Polyline):
                points.extend(self.geometry[i])
            elif isinstance(self.geometry[i], Line):
                points.extend([self.geometry[i].start, self.geometry[i].end])
            elif isinstance(self.geometry[i], Box):
                points.extend(self.geometry[i].points)
            elif isinstance(self.geometry[i], Pointcloud):
                points.extend(self.geometry[i].points)

        # if no points found, return
        if len(points) < 2:
            return Mesh()

        # compute the convex hull
        # use it with caution, it does not work, specially with coplanar points

        if len(points) > 2:
            faces = convex_hull(points)
            self._convex_hull = Mesh.from_vertices_and_faces(points, faces)
            return self._convex_hull
        else:
            self._convex_hull = Mesh()
            return self._convex_hull

    def has_collision(self, other):
        """check collision using aabb and oobb
        this function is often intermediate between high-performance tree searches
        then this collision is computed
        and then the interface can be found"""

        # --------------------------------------------------------------------------
        # sanity check
        # --------------------------------------------------------------------------
        if (not self.aabb()) or (not other.aabb()):
            return False

        # --------------------------------------------------------------------------
        # aabb collision
        # --------------------------------------------------------------------------
        collision_x_axis = self._aabb[6][0] < other._aabb[0][0] or other._aabb[6][0] < self._aabb[0][0]  # type: ignore
        collision_y_axis = self._aabb[6][1] < other._aabb[0][1] or other._aabb[6][1] < self._aabb[0][1]  # type: ignore
        collision_z_axis = self._aabb[6][2] < other._aabb[0][2] or other._aabb[6][2] < self._aabb[0][2]  # type: ignore
        aabb_collision = not (collision_x_axis or collision_y_axis or collision_z_axis)
        # print("aabb_collison", aabb_collision)
        if not aabb_collision:
            return False

        # --------------------------------------------------------------------------
        # oobb collision
        # https://discourse.mcneel.com/t/box-contains-box-check-for-coincident-boxes/59642/19
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

        # print("oobb_collison", result)
        return result

    # ==========================================================================
    # METHODS - FACE-TO-FACE DETECTION
    # ==========================================================================

    @property
    def face_polygons(self):
        """Get Polygons from the geometry
        WARNING: currently the face polygons do not consider elements with holes"""

        # --------------------------------------------------------------------------
        # sanity check
        # --------------------------------------------------------------------------
        if hasattr(self, "_face_polygons"):
            return self._face_polygons

        if len(self.geometry) == 0:
            raise AssertionError("You must assign geometry geometry to the element")

        if not isinstance(self.geometry[0], Mesh):
            raise AssertionError("The geometry must be a mesh")

        # --------------------------------------------------------------------------
        # get polylines from the mesh faces
        # --------------------------------------------------------------------------

        temp = self.geometry[0].to_polygons()
        self._face_polygons = []
        for point_list in temp:
            self._face_polygons.append(Polygon(point_list))

        return self._face_polygons

    @property
    def face_frames(self):
        """Get Frames from the geometry
        WARNING: currently the face polylines do not consider elements with holes
        for this you need to add face attributes to conside the holes"""
        # --------------------------------------------------------------------------
        # sanity check
        # --------------------------------------------------------------------------
        if hasattr(self, "_face_frames"):
            return self._face_frames

        if len(self.geometry) == 0:
            raise AssertionError("You must assign geometry geometry to the element")

        if not isinstance(self.geometry[0], Mesh):
            raise AssertionError("The geometry must be a mesh")

        # --------------------------------------------------------------------------
        # compute the frames of each mesh face
        # --------------------------------------------------------------------------
        self._face_frames = []

        mesh = self.geometry[0]

        for fkey in mesh.faces():
            xyz = mesh.face_coordinates(fkey)
            o = mesh.face_center(fkey)
            w = mesh.face_normal(fkey)
            u = [
                xyz[1][i] - xyz[0][i] for i in range(3)
            ]  # align with longest edge instead?
            v = cross_vectors(w, u)
            frame = Frame(o, u, v)
            self._face_frames.append(frame)

        # return [self.face_coordinates(fkey) for fkey in self.faces()]

        # for i in range(self.geometry[0].number_of_faces()):
        #     xyz = self.geometry[0].face_coordinates(i)
        #     o = self.geometry[0].face_center(i)
        #     w = self.geometry[0].face_normal(i)
        #     u = [xyz[1][i] - xyz[0][i] for i in range(3)]  # align with longest edge instead?
        #     v = cross_vectors(w, u)
        #     frame = Frame(o, u, v)
        #     self._face_frames.append(frame)

        return self._face_frames

    # def face_to_face(self, other, tmax=1e-6, amin=1e-1):
    #     """construct intefaces by intersecting coplanar mesh faces
    #     Parameters
    #     ----------
    #     assembly : compas_assembly.datastructures.Assembly
    #         An assembly of discrete blocks.
    #     nmax : int, optional
    #         Maximum number of neighbours per block.
    #     tmax : float, optional
    #         Maximum deviation from the perfectly flat interface plane.
    #     amin : float, optional
    #         Minimum area of a "face-face" interface.

    #     Returns
    #     -------
    #     Polygon of the Interface - :class:`compas.geometry.Polygon`
    #     Current Element ID - list[int]
    #     Other Element ID - list[int]
    #     Current Element Face Index - int
    #     Other Element Face Index - int
    #     """

    #     # --------------------------------------------------------------------------
    #     # sanity check
    #     # --------------------------------------------------------------------------
    #     if shapely_available is False:
    #         return []

    #     if len(self.geometry) == 0 or len(other.geometry) == 0:
    #         raise AssertionError("You must assign geometry geometry to the element")

    #     if not isinstance(self.geometry[0], Mesh) or not isinstance(other.geometry[0], Mesh):
    #         raise AssertionError("The geometry must be a mesh")

    #     # --------------------------------------------------------------------------
    #     # iterate face polygons and get intersection area
    #     # DEPENDENCY: shapely library
    #     # --------------------------------------------------------------------------

    #     def to_shapely_polygon(matrix, polygon, tmax=1e-6, amin=1e-1):
    #         """convert a compas polygon to shapely polygon on xy plane"""

    #         # orient points to the xy plane
    #         projected = transform_points(polygon.points, matrix)

    #         # check if the oriented point is on the xy plane within the tolerance
    #         # then return the shapely polygon
    #         if not all(fabs(point[2]) < tmax for point in projected):
    #             return None
    #         elif polygon.area < amin:
    #             return None
    #         else:
    #             return ShapelyPolygon(projected)

    #     def to_compas_polygon(matrix, shapely_polygon):
    #         """convert a shapely polygon to compas polygon back to the frame"""

    #         # convert coordiantes to 3D by adding the z coordinate
    #         coords = [[x, y, 0.0] for x, y, _ in intersection.exterior.coords]

    #         # orient points to the original first mesh frame
    #         coords = transform_points(coords, matrix.inverted())[:-1]

    #         # convert to compas polygon
    #         return Polygon(coords)

    #     joints = []

    #     for id_0, face_polygon_0 in enumerate(self.face_polygons):
    #         # get the transformation matrix
    #         matrix = Transformation.from_change_of_basis(Frame.worldXY(), self.face_frames[id_0])

    #         # get the shapely polygon
    #         shapely_polygon_0 = to_shapely_polygon(matrix, face_polygon_0)
    #         if shapely_polygon_0 is None:
    #             continue

    #         for id_1, face_polygon_1 in enumerate(other.face_polygons):
    #             # get the shapely polygon
    #             shapely_polygon_1 = to_shapely_polygon(matrix, face_polygon_1)
    #             if shapely_polygon_1 is None:
    #                 continue

    #             # check if polygons intersect
    #             if not shapely_polygon_0.intersects(shapely_polygon_1):
    #                 continue

    #             # get intersection area and check if it is big enough within the given tolerance
    #             intersection = shapely_polygon_0.intersection(shapely_polygon_1)
    #             area = intersection.area
    #             if area < amin:
    #                 continue

    #             # convert shapely polygon to compas polygon
    #             polygon = to_compas_polygon(matrix, intersection)

    #             # construct joint
    #             joint = Joint(
    #                 type=JOINT_NAME.FACE_TO_FACE,
    #                 polygon=polygon,
    #                 frame=self.face_frames[id_0],
    #                 surface_area=area,
    #             )

    #             # there can be more than one interface so store them in a list
    #             joints.append(joint)

    #     # output
    #     return joints

    # ==========================================================================
    # METHODS - AXIS-TO-AXIS DETECTION
    # ==========================================================================

    def axis_to_axis(self, other, tmax=1e-6, amin=1e-1):
        pass

    # ==========================================================================
    # METHODS - FRAME-TO-FACE DETECTION
    # ==========================================================================

    def frame_to_face(self, other, tmax=1e-6, amin=1e-1):
        pass

    # ==========================================================================
    # METHODS - OBJECT-MINUS-OBJECT DETECTION
    # ==========================================================================
    def object_minus_object(self, other, tmax=1e-6, amin=1e-1):
        pass

    # ==========================================================================
    # COPY
    # ==========================================================================
    def copy(self):
        # copy main properties
        new_instance = self.__class__(
            name=self.name,
            id=self.id,
            frame=self.frame,
            geometry_simplified=self.geometry_simplified,
            geometry=self.geometry,
            **self.attributes,
        )

        # deepcopy of the fabrication, and structural information
        new_instance.frame_global = self.frame_global.copy()
        new_instance._aabb = copy.deepcopy(self.aabb())
        new_instance._oobb = copy.deepcopy(self.oobb())
        new_instance._convex_hull = copy.deepcopy(self.convex_hull)
        new_instance._fabrication = copy.deepcopy(self.fabrication)
        new_instance._structure = copy.deepcopy(self.structure)

        return new_instance

    # ==========================================================================
    # TRANSFORMATIONS
    # ==========================================================================

    def transform(self, transformation):
        """
        Transforms the geometry , local frame, and global frame of the Element.

        Parameters:
            transformation (Transformation): The transformation to be applied to the Element's geometry and frames.

        Returns:
            None
        """

        # transorm the geometry
        self.frame.transform(transformation)
        self.frame_global.transform(transformation)

        for i in range(len(self.geometry_simplified)):
            self.geometry_simplified[i].transform(transformation)

        for i in range(len(self.geometry)):
            self.geometry[i].transform(transformation)

        # recompute the bounding-box
        self._aabb.clear()
        self.aabb()

        # transform the oobb and convex-hull
        self.oobb()
        for i in range(len(self._oobb)):
            p = Point(self._oobb[i][0], self._oobb[i][1], self._oobb[i][2]).transformed(
                transformation
            )
            self._oobb[i] = [p.x, p.y, p.z]

        if self.convex_hull:
            if self.convex_hull.number_of_vertices() > 0:
                self.convex_hull.transform(transformation)

    def transformed(self, transformation):
        """
        Creates a transformed copy of the Element.

        Parameters:
            transformation (Transformation): The transformation to be applied to the copy.

        Returns:
            Element: A new instance of the Element with the specified transformation applied.
        """
        new_instance = self.copy()
        new_instance.transform(transformation)
        return new_instance

    def transform_to_frame(self, frame):
        """
        Applies frame_to_frame transformation to the geometry , local frame, and global frame of the Element.

        Parameters:
            frame (Frame): The target frame to which  the Element will be transformed.

        Returns:
            None
        """
        xform = Transformation.from_frame_to_frame(self.frame, frame)
        self.transform(xform)

    def transform_from_frame_to_frame(self, source_frame, target_frame):
        """
        Applies frame_to_frame transformation to the geometry , local frame, and global frame of the Element.

        Parameters:
            frame (Frame): The target frame to which  the Element will be transformed.

        Returns:
            None
        """
        xform = Transformation.from_frame_to_frame(source_frame, target_frame)
        self.transform(xform)

    def transformed_to_frame(self, frame):
        """
        Creates an oriented copy of the Element.

        Parameters:
            frame (Frame): The target frame to which the Element will be transformed.

        Returns:
            Element: A new instance of the Element with the specified orientation applied.
        """
        new_instance = self.copy()
        new_instance.transform_to_frame(frame)
        return new_instance

    def transformed_from_frame_to_frame(self, source_frame, target_frame):
        """
        Creates an oriented copy of the Element.

        Parameters:
            frame (Frame): The target frame to which the Element will be transformed.

        Returns:
            Element: A new instance of the Element with the specified orientation applied.
        """
        new_instance = self.copy()
        new_instance.transform_from_frame_to_frame(source_frame, target_frame)
        return new_instance

    # ==========================================================================
    # DESCRIPTION
    # ==========================================================================

    def __repr__(self):
        """
        Return a string representation of the Element.

        Returns:
            str: The string representation of the Element.
        """
        return """{0} {1} {2}""".format(
            self.name, "_".join(map(str, self.id)), self.guid
        )
        # return self.name


class _:
    """Internal geometry utilities"""

    class Ear:
        """
        Represents an ear of a polygon. An ear is a triangle formed by three consecutive vertices of the polygon.
        """

        def __init__(self, points, indexes, ind):
            """
            Initialize an Ear instance.

            Args:
                points (list): List of vertex coordinates.
                indexes (list): List of vertex indexes.
                ind (int): Index of the current vertex.
            """
            self.index = ind
            self.coords = points[ind]
            length = len(indexes)
            index_in_indexes_arr = indexes.index(ind)
            self.next = indexes[(index_in_indexes_arr + 1) % length]
            if index_in_indexes_arr == 0:
                self.prew = indexes[length - 1]
            else:
                self.prew = indexes[index_in_indexes_arr - 1]
            self.neighbour_coords = [points[self.prew], points[self.next]]

        def is_inside(self, point):
            """
            Check if a given point is inside the triangle formed by the ear.

            Args:
                point (list): Coordinates of the point to check.

            Returns:
                bool: True if the point is inside the triangle, False otherwise.
            """
            p1 = self.coords
            p2 = self.neighbour_coords[0]
            p3 = self.neighbour_coords[1]
            p0 = point

            d = [
                (p1[0] - p0[0]) * (p2[1] - p1[1]) - (p2[0] - p1[0]) * (p1[1] - p0[1]),
                (p2[0] - p0[0]) * (p3[1] - p2[1]) - (p3[0] - p2[0]) * (p2[1] - p0[1]),
                (p3[0] - p0[0]) * (p1[1] - p3[1]) - (p1[0] - p3[0]) * (p3[1] - p0[1]),
            ]

            if d[0] * d[1] >= 0 and d[2] * d[1] >= 0 and d[0] * d[2] >= 0:
                return True
            return False

        def is_ear_point(self, p):
            """
            Check if a given point is one of the vertices of the ear triangle.

            Args:
                p (list): Coordinates of the point to check.

            Returns:
                bool: True if the point is a vertex of the ear triangle, False otherwise.
            """
            if p == self.coords or p in self.neighbour_coords:
                return True
            return False

        def validate(self, points, indexes, ears):
            """
            Validate if the ear triangle is a valid ear by checking its convexity and that no points lie inside.

            Args:
                points (list): List of vertex coordinates.
                indexes (list): List of vertex indexes.
                ears (list): List of other ear triangles.

            Returns:
                bool: True if the ear triangle is valid, False otherwise.
            """
            not_ear_points = [
                points[i]
                for i in indexes
                if points[i] != self.coords and points[i] not in self.neighbour_coords
            ]
            insides = [self.is_inside(p) for p in not_ear_points]
            if self.is_convex() and True not in insides:
                for e in ears:
                    if e.is_ear_point(self.coords):
                        return False
                return True
            return False

        def is_convex(self):
            """
            Check if the ear triangle is convex.

            Returns:
                bool: True if the ear triangle is convex, False otherwise.
            """
            a = self.neighbour_coords[0]
            b = self.coords
            c = self.neighbour_coords[1]
            ab = [b[0] - a[0], b[1] - a[1]]
            bc = [c[0] - b[0], c[1] - b[1]]
            if ab[0] * bc[1] - ab[1] * bc[0] <= 0:
                return False
            return True

        def get_triangle(self):
            """
            Get the indices of the vertices forming the ear triangle.

            Returns:
                list: List of vertex indices forming the ear triangle.
            """
            return [self.prew, self.index, self.next]

    class Earcut:
        """
        A class for triangulating a simple polygon using the ear-cutting algorithm.
        """

        def __init__(self, points):
            """
            Initialize an Earcut instance with the input points.

            Args:
                points (list): List of vertex coordinates forming the polygon.
            """
            self.vertices = points
            self.ears = []
            self.neighbours = []
            self.triangles = []
            self.length = len(points)

        def update_neighbours(self):
            """
            Update the list of neighboring vertices.
            """
            neighbours = []
            self.neighbours = neighbours

        def add_ear(self, new_ear):
            """
            Add a new ear to the list of ears and update neighboring vertices.

            Args:
                new_ear (Ear): The new ear triangle to be added.
            """
            self.ears.append(new_ear)
            self.neighbours.append(new_ear.prew)
            self.neighbours.append(new_ear.next)

        def find_ears(self):
            """
            Find valid ear triangles among the vertices and add them to the ears list.
            """
            i = 0
            indexes = list(range(self.length))
            while True:
                if i >= self.length:
                    break
                new_ear = _.Ear(self.vertices, indexes, i)
                if new_ear.validate(self.vertices, indexes, self.ears):
                    self.add_ear(new_ear)
                    indexes.remove(new_ear.index)
                i += 1

        def triangulate(self):
            """
            Triangulate the polygon using the ear-cutting algorithm.
            """
            indexes = list(range(self.length))
            self.find_ears()

            num_of_ears = len(self.ears)

            if num_of_ears == 0:
                raise ValueError("No ears found for triangulation.")
            if num_of_ears == 1:
                self.triangles.append(self.ears[0].get_triangle())
                return

            while True:
                if len(self.ears) == 2 and len(indexes) == 4:
                    self.triangles.append(self.ears[0].get_triangle())
                    self.triangles.append(self.ears[1].get_triangle())
                    break

                if len(self.ears) == 0:
                    raise IndexError("Unable to find more ears for triangulation.")
                current = self.ears.pop(0)

                indexes.remove(current.index)
                self.neighbours.remove(current.prew)
                self.neighbours.remove(current.next)

                self.triangles.append(current.get_triangle())

                # Check if prew and next vertices form new ears
                prew_ear_new = _.Ear(self.vertices, indexes, current.prew)
                next_ear_new = _.Ear(self.vertices, indexes, current.next)
                if (
                    prew_ear_new.validate(self.vertices, indexes, self.ears)
                    and prew_ear_new.index not in self.neighbours
                ):
                    self.add_ear(prew_ear_new)
                    continue
                if (
                    next_ear_new.validate(self.vertices, indexes, self.ears)
                    and next_ear_new.index not in self.neighbours
                ):
                    self.add_ear(next_ear_new)
                    continue

    class Triagulator:
        @staticmethod
        def get_frame(_points, _orientation_point=None):
            """create a frame from a polyline"""

            # create a normal by averaging the cross-products of a polyline
            normal = Vector(0, 0, 0)
            count = len(_points)
            center = Point(0, 0, 0)
            is_closed = (
                distance_point_point(Point(*_points[0]), Point(*_points[-1])) < 0.01
            )
            sign = 1 if is_closed else 0

            for i in range(count - sign):
                num = ((i - 1) + count - sign) % (count - sign)
                item1 = ((i + 1) + count - sign) % (count - sign)
                point3d = _points[num]
                point3d1 = _points[item1]
                item2 = _points[i]
                normal += cross_vectors(item2 - point3d, point3d1 - item2)
                center = center + point3d
            normal.unitize()
            center = center / count

            # get the longest edge
            longest_segment_length = 0.0
            longest_segment_start = None
            longest_segment_end = None

            for i in range(len(_points) - sign):
                point1 = _points[i]
                point2 = _points[
                    (i + 1) % len(_points)
                ]  # To create a closed polyline, connect the last point to the first one.

                segment_length = distance_point_point(point1, point2)

                if segment_length > longest_segment_length:
                    longest_segment_length = segment_length
                    longest_segment_start = point1
                    longest_segment_end = point2

            # create x and y-axes for the frame
            x_axis = Vector.from_start_end(longest_segment_start, longest_segment_end)
            x_axis.unitize()
            y_axis = cross_vectors(normal, x_axis)
            y_axis = Vector(y_axis[0], y_axis[1], y_axis[2])
            # create the frame
            center = centroid_points(_points)
            frame = Frame(center, x_axis, y_axis)

            # orient the from the orientation point to the opposite direction
            reversed = False
            if _orientation_point is not None:
                signed_distance = distance_point_plane_signed(
                    _orientation_point, Plane.from_frame(frame)
                )
                if signed_distance > 0.001:
                    frame = Frame(frame.point, -x_axis, y_axis)
                    reversed = True
            # output
            return frame, reversed

        @staticmethod
        def from_points(points):
            polygon = Polygon(points=points)
            frame = _.Triagulator.get_frame(points)
            xform, reversed = Transformation.from_frame_to_frame(frame, Frame.worldXY())
            polygon.transform(xform)
            ear_cut = _.Earcut(polygon.points)
            ear_cut.triangulate()

            return Mesh.from_vertices_and_faces(polygon.points, ear_cut.triangles)

        @staticmethod
        def from_loft_two_point_lists(_points0, _points1):
            n = len(_points0)

            is_closed = (
                distance_point_point(Point(*_points0[0]), Point(*_points0[-1])) < 0.01
            )
            sign = 1 if is_closed else 0
            n = n - sign

            # create a polygon from the first set of points
            # orient to worldXY
            # triangulate

            # points0.reverse()
            frame, reversed = _.Triagulator.get_frame(_points0, _points1[0])
            points0 = list(_points0)
            points1 = list(_points1)
            xform = Transformation.from_frame_to_frame(frame, Frame.worldXY())
            if reversed:
                points0.reverse()
                points1.reverse()
            polygon = Polygon(points=points0)
            polygon.transform(xform)
            ear_cut = _.Earcut(polygon.points)
            ear_cut.triangulate()
            polygon.transform(xform.inverse())
            triangles = ear_cut.triangles

            # create mesh loft
            vertices = points0[:n] + points1[0:n]
            faces = []

            # top and bottom faces
            triangles = ear_cut.triangles
            if reversed:
                for triangle in triangles:
                    faces.append([triangle[0] + n, triangle[1] + n, triangle[2] + n])

                for triangle in triangles:
                    faces.append([triangle[2], triangle[1], triangle[0]])
            else:
                for triangle in triangles:
                    faces.append([triangle[0], triangle[1], triangle[2]])

                for triangle in triangles:
                    faces.append([triangle[2] + n, triangle[1] + n, triangle[0] + n])

            # side faces
            for i in range(n):
                next = (i + 1) % n
                faces.append([i, next, next + n, i + n])

            # check cycles
            mesh = Mesh.from_vertices_and_faces(vertices, faces)
            # print(mesh.face_neighbors(1))
            return mesh, frame

        @staticmethod
        def mesh_box_from_eight_points(vertices):
            # define the faces with the ccw winding
            faces = [
                [0, 3, 2, 1],
                [4, 5, 6, 7],
                [0, 1, 5, 4],
                [1, 2, 6, 5],
                [2, 3, 7, 6],
                [3, 0, 4, 7],
            ]

            mesh = Mesh.from_vertices_and_faces(vertices, faces)
            p0 = Point(vertices[0][0], vertices[0][1], vertices[0][2])
            p1 = Point(vertices[6][0], vertices[6][1], vertices[6][2])
            center = (p0 + p1) * 0.5

            return mesh, center

    class PlaneUtil:
        @staticmethod
        def points_from_side_plane(plane, side_planes, offset=0.0, close=True):
            points = []
            plane_offset = (
                Plane(plane.point + plane.normal * offset, plane.normal)
                if abs(offset) > 0.01
                else plane
            )
            for i in range(len(side_planes)):
                p0 = intersection_plane_plane_plane(
                    plane_offset,
                    side_planes[i],
                    side_planes[(i + 1) % len(side_planes)],
                )
                if p0 is None:
                    raise Exception("Could not find intersection point")
                points.append(Point(p0[0], p0[1], p0[2]))

            if close:
                points.append(points[0])

            return points
