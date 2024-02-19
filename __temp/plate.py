from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_model.elements.element import Element

from compas.geometry import Point
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Line
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import Transformation, Translation
from compas.geometry import distance_point_point
from compas.geometry import distance_point_plane_signed
from compas.geometry import earclip_polygon
from compas.geometry import distance_point_point_sqrd
from compas.geometry import bounding_box
from compas.geometry import transform_points
from compas.geometry import convex_hull
from compas.geometry import cross_vectors
from compas.geometry import Box
from compas.datastructures import Mesh


class PlateElement(Element):
    """A block represented by a central point and a mesh.

    The implementation is inspired by the compas_assembly block class:
    https://github.com/BlockResearchGroup/compas_assembly/blob/main/src/compas_assembly/datastructures/block.py

    Parameters
    ----------
    polygon : :class:`compas.geometry.Polygon`
        The outline of the plate.
    thickness : float
        The thickness of the plate.
    compute_loft : bool
        If True, the geometry is set as a mesh from lofting the two outlines, otherwise the geometry is set as two outlines.
    name : str
        The name of the element.

    Attributes
    ----------
    guid : uuid
        The unique identifier of the element.
    geometry : Union[Geometry, Mesh]
        The geometry of the element.
    frame : :class:`compas.geometry.Frame`
        The frame of the element.
    name : str
        The name of the element.
    graph_node : :class:`compas.datastructures.GraphNode`
        The graph node of the element.
    tree_node : :class:`compas.datastructures.TreeNode`
        The tree node of the element.
    dimensions : list
        The dimensions of the element.
    aabb : :class:`compas.geometry.Box`
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`
        The collision geometry of the element.
    features : dict
        These are custom geometrical objects added to the elements through operations made by the user.
        For example, a cutting shape for boolean difference operations, text identifiers.
    insertion : :class:`compas.geometry.Vector`
        The insertion vector of the element. Default is (0, 0, -1), representing a downwards insertion.
        This attribute is often used for simulating an assembly sequence.
    face_polygons : list, read-only
        Flat area list of the face polygons of the element, used for interface detection.

    """

    @property
    def __data__(self) -> dict:
        base_data = super().__data__  # not to repeat the same code for base properties
        base_data["features"] = self.features
        base_data["insertion"] = self.insertion
        base_data["face_polygons"] = self.face_polygons
        base_data["thickness"] = self.thickness
        return base_data

    @classmethod
    def __from_data__(cls, data):
        element = cls.from_two_polygons(
            data["face_polygons"][0],
            data["face_polygons"][1],
            compute_loft=False,
        )

        element._geometry = data["geometry"]
        element._features = data["features"]
        element._insertion = data["insertion"]
        element._face_polygons = data["face_polygons"]
        return element

    def __init__(self, polygon, thickness, compute_loft=True, name=None):
        # --------------------------------------------------------------------------
        # Safety check.
        # --------------------------------------------------------------------------
        if len(polygon.points) < 3:
            raise ValueError(
                "A polygon must have at least three points. No plate is created."
            )

        if thickness < 1e-3:
            raise ValueError(
                "Provided thickness is smaller than 1e-3. No plate is created."
            )

        # --------------------------------------------------------------------------
        # Create geometry.
        # --------------------------------------------------------------------------
        frame = self.get_average_frame(
            polygon
        )  # default polygon.frame does not consider the winding order.
        polygon0 = polygon.copy()
        polygon1 = polygon.copy()

        polygon0.transform(Translation.from_vector(frame.zaxis * -0.5 * thickness))
        polygon1.transform(Translation.from_vector(frame.zaxis * 0.5 * thickness))
        geometry = (
            [PlateElement.mesh_from_loft(polygon0, polygon1)]
            if compute_loft
            else [polygon0, polygon1]
        )

        # --------------------------------------------------------------------------
        # Call the default Element constructor with the given parameters.
        # --------------------------------------------------------------------------
        super(PlateElement, self).__init__(
            geometry=geometry,
            frame=frame,
            name=name,
        )

        self._thickness = thickness

        # --------------------------------------------------------------------------
        # Create face frames.
        # --------------------------------------------------------------------------
        frame0 = Frame(
            self.frame.point + self.frame.zaxis * -thickness * 0.5,
            self.frame.xaxis,
            -self.frame.yaxis,
        )
        frame1 = Frame(
            self.frame.point + self.frame.zaxis * thickness * 0.5,
            self.frame.xaxis,
            self.frame.yaxis,
        )

        face_frames = [frame0, frame1]

        n = len(polygon0.points)
        for i in range(n):
            point = (polygon0[i] + polygon0[(i + 1) % n]) * 0.5
            xaxis = polygon0[(i + 1) % n] - polygon0[i]
            yaxis = self.frame.zaxis
            face_frames.append(Frame(point, xaxis, yaxis))

        # --------------------------------------------------------------------------
        # Set the face outlines.
        # --------------------------------------------------------------------------
        self._face_polygons = [polygon0, polygon1]
        polygon0.translate(Vector(1, 0, 0))

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

        self.features = {}
        self.insertion = Vector(0, 0, 1)

    @classmethod
    def from_two_polygons(cls, polygon0, polygon1, compute_loft=True, name=None):
        """Create a plate from two polygons.¨

        Parameters
        ----------
        polygon0 : :class:`compas.geometry.Polygon`
            The first outline of the plate.
        polygon1 : :class:`compas.geometry.Polygon`
            The second outline of the plate.
        compute_loft : bool
            If True, the plate is created from a lofted mesh.
        **kwargs : dict, optional
            Additional keyword arguments.

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
            polygon1.plane.closest_point(polygon0[0]),
        )

        # --------------------------------------------------------------------------
        # Create an empty object.
        # --------------------------------------------------------------------------
        plate = cls(average_polygon, thickness, compute_loft=False, name=name)

        # if compute_loft:
        #     plate._geometry = [PlateElement.mesh_from_loft(polygon0, polygon1)]

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
                plate.geometry[0].points[i] + plate.geometry[0].points[(i + 1) % n]
            ) * 0.5
            xaxis = plate.geometry[0].points[(i + 1) % n] - plate.geometry[0].points[i]
            yaxis0 = (
                top_and_bottom_polygons[1].points[i] - top_and_bottom_polygons[0][i]
            )
            yaxis1 = (
                top_and_bottom_polygons[1].points[(i + 1) % n]
                - top_and_bottom_polygons[0].points[(i + 1) % n]
            )
            yaxis = yaxis0 + yaxis1
            face_frames.append(Frame(point=origin, xaxis=xaxis, yaxis=yaxis))

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

    # ==========================================================================
    # Templated methods to provide minimal information for:
    # aabb
    # obb
    # geometry_collision
    # transform
    # ==========================================================================

    @property
    def dimensions(self):
        if not isinstance(self.obb, Box):
            self.compute_obb()
        return [self.obb.width, self.obb.height, self.obb.depth]

    def compute_aabb(self, inflate=0.0):
        """Computes the Oriented Bounding Box (OBB) of the element.

        Parameters
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """
        points = []
        for g in self.geometry:
            if type(g) is Polygon:
                points += g.points
            else:
                vertices, faces = g.to_vertices_and_faces()
                points += vertices

        self._aabb = Box.from_points(points)
        self._aabb.xsize += inflate
        self._aabb.ysize += inflate
        self._aabb.zsize += inflate
        return self._aabb

    def compute_obb(self, inflate=0.0):
        """Computes the Axis Aligned Bounding Box (AABB) of the element.

        Parameters
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """
        points = []
        for g in self.geometry:
            if type(self.geometry[0]) is Polygon:
                points += g.points
            else:
                vertices, faces = g.to_vertices_and_faces()
                points += vertices

        # Find the longest point pair in the first polygon.
        longest_edge_index = 0
        longest_edge_length = distance_point_point_sqrd(
            self.geometry[0][0], self.geometry[0][1]
        )
        n = len(self.geometry[0].points)
        for i in range(1, n):
            length = distance_point_point_sqrd(
                self.geometry[0][i], self.geometry[0][(i + 1) % n]
            )
            if length > longest_edge_length:
                longest_edge_length = length
                longest_edge_index = i
        longest_edge_line = Line(
            self.geometry[0][longest_edge_index],
            self.geometry[0][(longest_edge_index + 1) % n],
        )

        # Create a frame from the longest edge as x-axis, and y-axis is the cross_product of the longest edge and z-axis.
        xaxis = longest_edge_line.direction
        zaxis = self.geometry[0].normal
        yaxis = Vector(*cross_vectors(xaxis, zaxis))
        yaxis.unitize()
        frame = Frame(longest_edge_line.midpoint, xaxis, yaxis)

        # Orient polygon to the new frame.
        xform = Transformation.from_frame_to_frame(frame, Frame.worldXY())
        transformed_points = transform_points(points, xform)

        # Create a box from transformed and inflate the box.
        self._obb = Box.from_points(bounding_box(transformed_points))
        self._obb.xsize += inflate
        self._obb.ysize += inflate
        self._obb.zsize += inflate

        # Orient the box back to the original frame.
        self._obb.transform(xform.inverse())
        return self._obb

    def compute_collision_mesh(self):
        """Computes the collision geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """

        points = []
        for g in self.geometry:
            if type(self.geometry[0]) is Polygon:
                points += g.points
            else:
                vertices, faces = g.to_vertices_and_faces()
                points += vertices
        faces = convex_hull(points)

        return Mesh.from_vertices_and_faces(points, faces)

    def compute_loft(self):
        """Computes the lofted mesh of the element.

        Returns
        -------
        Any
            The lofted mesh of the element.

        """
        return PlateElement.mesh_from_loft(self.geometry[0], self.geometry[1])

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
        for g in self.geometry:
            g.transform(transformation)

        for g in self.geometry:
            g.transform(transformation)

        # I do not see the other way than to check the private property.
        # Otherwise it gets computed and transformed twice.
        # Also, we do not want to have these properties computed, unless needed.
        # It can be done above geometry transformations, but they will be computed.
        if self._aabb:
            self.compute_aabb()

        if self._obb:
            # If the transformation is a scale:
            # a) the box xsize, ysize, zsize has to be adjusted
            # b) then the rest of transformation can be applied to the frame
            self.obb.xsize *= transformation[0, 0]
            self.obb.ysize *= transformation[1, 1]
            self.obb.zsize *= transformation[2, 2]
            self.obb.transform(transformation)

        if self._collision_mesh:
            self.collision_mesh.transform(transformation)

        # When the geometry property is set to two outlines do not transform them twice.
        # This condition needs to be implemented in the future for the holes.
        if self._face_polygons:
            if type(self.geometry[0]) is Polygon:
                for i in range(2, len(self._face_polygons)):
                    self._face_polygons[i].transform(transformation)
            else:
                for polygon in self.face_polygons:
                    polygon.transform(transformation)

    # ==========================================================================
    # Custom Parameters and methods specific to this class.
    # ==========================================================================

    @property
    def face_polygons(self):
        if not self._face_polygons:
            self._face_polygons = self.compute_face_polygons()
        return self._face_polygons

    @face_polygons.setter
    def face_polygons(self, value):
        self._face_polygons = value

    @property
    def face_frames(self):
        frames = []
        for polygon in self.face_polygons:
            frames.append(PlateElement.get_average_frame(polygon))
        frames[0] = Frame(
            point=frames[0].point, xaxis=frames[0].xaxis, yaxis=-frames[0].yaxis
        )
        return frames

    @property
    def thickness(self):
        if not self._thickness:
            self._thickness = distance_point_point(
                self.geometry[0][0],
                self.geometry[1].plane.closest_point(self.geometry[0][0]),
            )
        return self._thickness

    @property
    def top_and_bottom_polygons(self):
        return [self.face_polygons[0], self.face_polygons[1]]

    @staticmethod
    def mesh_from_loft(polygon0, polygon1):
        """Create a mesh from two lists of points.

        Parameters
        ----------
        polygon0 : :class:`compas.geometry.Polygon`
            The first outline of the plate.

        Returns
        -------
        Tuple : Mesh, Frame
            Tuple containing the mesh and the frame of the first polyline.

        """

        # Check the orientation of the polygon in relation to the other polygon.
        frame = polygon0.frame
        reversed = False
        signed_distance = distance_point_plane_signed(
            polygon1[0], Plane.from_frame(frame)
        )
        if signed_distance > 1e-3:
            frame = Frame(frame.point, -frame.xaxis, frame.yaxis)
            reversed = True

        points0 = list(polygon0)
        points1 = list(polygon1)
        if reversed:
            points0.reverse()
            points1.reverse()

        # Triangulate one polygon.
        triangles = earclip_polygon(Polygon(points0))

        # Input values for the mesh.
        n = len(polygon0)
        vertices = points0 + points1
        faces = []

        # Add top and bottom faces.
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

        # Add side faces.
        for i in range(n):
            next = (i + 1) % n
            faces.append([i, next, next + n, i + n])

        mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    @staticmethod
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
