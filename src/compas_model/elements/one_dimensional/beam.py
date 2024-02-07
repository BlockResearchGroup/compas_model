from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import add_vectors
from compas.geometry import Box
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import Frame
from compas.geometry import cross_vectors
from compas.datastructures import Mesh
from compas.geometry import angle_vectors
from compas.tolerance import Tolerance
from compas_model.elements.element import Element


class Beam(Element):
    """A beam representation of a Line and a Box.

    Parameters
    ----------
    frame : :class:`compas.geometry.Frame`
        The frame of the beam.
    length : float
        Length of the beam.
    width : float
        Width of the cross-section.
    height : float
        Height of the cross-section.
    **kwargs : dict, optional
        Additional keyword arguments.

    Attributes
    ----------
    guid : str, read-only
        The globally unique identifier of the object.
        The guid is generated with ``uuid.uuid4()``.
    name : str
        The name of the object.
        This name is not necessarily unique and can be set by the user.
        The default value is the object's class name: ``self.__class__.__name__``.
    frame : :class:`compas.geometry.Frame`, read-only
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry : :class:`compas.geometry.Box`, read-only
        A box representing the solid shape of the beam.
    geometry_simplified : :class:`compas.geometry.Line`, read-only
        The central axis of the beam.
    aabb : :class:`compas.geometry.Box`, read-only
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`, read-only
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`, read-only
        The collision geometry of the element.
    dimensions : list, read-only, read-only
        The dimensions of the element.
    features : dict
        These are custom geometrical objects added to the elements through operations made by the user.
        For example, a cutting shape for boolean difference operations, text identifiers.
    insertion : :class:`compas.geometry.Vector`
        The insertion vector of the element. Default is (0, 0, -1), representing a downwards insertion.
        This attribute is often used for simulating an assembly sequence.
    node : :class:`compas_model.model.ElementNode`
        The node in the model tree containing the element.
    face_polygons : list, read-only
        Flat area list of the face polygons of the element, used for interface detection.

    """

    DATASCHEMA = None

    @property
    def __data__(self):
        return {
            "name": self.name,
            "frame": self.frame,
            "geometry": self.geometry,
            "geometry_simplified": [
                self.geometry_simplified.start,
                self.geometry_simplified.end,
            ],
            "aabb": self.aabb,
            "obb": self.obb,
            "collision_mesh": self.collision_mesh,
            "dimensions": self.dimensions,
            "features": self.features,
            "insertion": self.insertion,
            "face_polygons": self.face_polygons,
            "attributes": self.attributes,
        }

    @classmethod
    def __from_data__(cls, data):
        element = cls(
            data["frame"],
            data["dimensions"][0],
            data["geometry"][1],
            data["geometry"][2],
        )
        element._name = data["name"]
        element._aabb = data["aabb"]
        element._obb = data["obb"]
        element._collision_mesh = data["collision_mesh"]
        element._dimensions = data["dimensions"]
        element._features = data["features"]
        element._insertion = data["insertion"]
        element._face_polygons = data["face_polygons"]
        element.attributes.update(data["attributes"])
        return element

    def __init__(self, frame, length, width, height, **kwargs):
        if length <= 0:
            raise ValueError("Length should be greater than zero.")
        elif width <= 0:
            raise ValueError("Width should be greater than zero.")
        elif height <= 0:
            raise ValueError("Height should be greater than zero.")

        super(Beam, self).__init__(
            frame=frame,
            geometry_simplified=Line(
                frame.point, Point(*add_vectors(frame.point, frame.xaxis * length))
            ),
            geometry=self._create_box(frame, width, height, length),
            **kwargs,
        )

        self._face_polygons = None

    def _create_box(self, frame, xsize, ysize, zsize):
        """Create box from frame.
        This method is needed, because compas box is create from center, not by domains.
        """
        boxframe = frame.copy()
        boxframe.point += boxframe.xaxis * zsize * 0.5
        return Box(zsize, xsize, ysize, frame=boxframe)

    @classmethod
    def from_line(cls, center_axis, width, height, z_vector=None, **kwargs):
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
        **kwargs : dict, optional
            Additional keyword arguments.

        Returns
        -------
        :class:`compas_timber.parts.Beam`

        """
        tol = Tolerance()
        x_vector = center_axis.vector

        if not z_vector:
            z_vector = Vector(0, 0, 1)
            angle = angle_vectors(z_vector, x_vector)

            if angle < tol.angular or angle > 3.141592 - tol.angular:
                z_vector = Vector(1, 0, 0)
        else:
            z_vector = z_vector

        y_vector = Vector(*cross_vectors(x_vector, z_vector)) * -1.0
        if y_vector.length < tol.approximation:
            raise ValueError(
                "The given z_vector seems to be parallel to the given center_axis."
            )
        frame = Frame(center_axis.start, x_vector, y_vector)
        length = center_axis.length

        return cls(frame, length, width, height, **kwargs)

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
        return [self.geometry.width, self.geometry.height, self.geometry.depth]

    def compute_aabb(self, inflate=0.0):
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
        self._aabb = Box.from_bounding_box([self.geometry.corner(i) for i in range(8)])
        self._aabb.xsize *= (self._aabb.width + inflate) / self._aabb.width
        self._aabb.ysize *= (self._aabb.depth + inflate) / self._aabb.depth
        self._aabb.zsize *= (self._aabb.height + inflate) / self._aabb.height
        return self._aabb

    def compute_obb(self, inflate=0.0):
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
        self._obb = self.geometry.copy()
        self._obb.xsize *= (self._obb.width + inflate) / self._obb.width
        self._obb.ysize *= (self._obb.depth + inflate) / self._obb.depth
        self._obb.zsize *= (self._obb.height + inflate) / self._obb.height
        return self._obb

    def compute_collision_mesh(self):
        """Computes the collision geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """
        self._collision_mesh = Mesh.from_vertices_and_faces(
            *self.geometry.to_vertices_and_faces()
        )
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
            # If the transformation is a scale:
            # a) the box xsize, ysize, zsize has to be adjusted
            # b) then the rest of transformation can be applied to the frame
            self.obb.xsize *= transformation[0, 0]
            self.obb.ysize *= transformation[1, 1]
            self.obb.zsize *= transformation[2, 2]
            self.obb.transform(transformation)

        if self._collision_mesh:
            self.collision_mesh.transform(transformation)

        if self._face_polygons:
            for polygon in self.face_polygons:
                polygon.transform(transformation)

    # ==========================================================================
    # Custom Parameters and methods specific to this class.
    # ==========================================================================

    @property
    def mid_point(self):
        return Point(
            *add_vectors(self.frame.point, self.frame.xaxis * self.dimensions[2] * 0.5)
        )

    @property
    def face_polygons(self):
        if not self._face_polygons:
            self._face_polygons = self.compute_face_polygons()
        return self._face_polygons

    def compute_face_polygons(self):
        """Computes the face polygons of the element.

        Returns
        -------
        list
            The face polygons of the element.

        """

        self._face_polygons = [
            Polygon(
                [
                    self.geometry.corner(0),
                    self.geometry.corner(1),
                    self.geometry.corner(2),
                    self.geometry.corner(3),
                ]
            ),
            Polygon(
                [
                    self.geometry.corner(4),
                    self.geometry.corner(5),
                    self.geometry.corner(6),
                    self.geometry.corner(7),
                ]
            ),
            Polygon(
                [
                    self.geometry.corner(0),
                    self.geometry.corner(1),
                    self.geometry.corner(5),
                    self.geometry.corner(4),
                ]
            ),
            Polygon(
                [
                    self.geometry.corner(3),
                    self.geometry.corner(2),
                    self.geometry.corner(6),
                    self.geometry.corner(7),
                ]
            ),
            Polygon(
                [
                    self.geometry.corner(3),
                    self.geometry.corner(0),
                    self.geometry.corner(4),
                    self.geometry.corner(7),
                ]
            ),
            Polygon(
                [
                    self.geometry.corner(2),
                    self.geometry.corner(1),
                    self.geometry.corner(5),
                    self.geometry.corner(6),
                ]
            ),
        ]

        return self._face_polygons
