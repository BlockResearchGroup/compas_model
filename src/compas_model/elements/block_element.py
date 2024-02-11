from compas_model.elements import Element
from compas.datastructures import Mesh
from compas.geometry import convex_hull_numpy
from compas.geometry import Box
from compas.geometry import Polygon


class BlockElement(Element):

    """Block element model.

    Parameters
    ----------
    geometry : Mesh
        The geometry of the element.
    is_support : bool, default False
        Whether the element is a support.
    frame : None, default WorldXY
        The frame of the element.
    name : None
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

    """

    @property
    def __data__(self) -> dict:
        base_data = super().__data__  # not to repeat the same code for base properties
        base_data["is_support"] = self.is_support
        return base_data

    @classmethod
    def __from_data__(cls, data):
        return cls(**data)

    def __init__(self, geometry: Mesh, is_support=False, frame=None, name=None):
        super().__init__(geometry=geometry, frame=frame, name=name)
        self.is_support = is_support

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
        return [self.aabb.width, self.aabb.height, self.aabb.depth]

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
        self._aabb = Box.from_points(self.geometry.aabb())
        self._aabb.xsize += inflate
        self._aabb.ysize += inflate
        self._aabb.zsize += inflate
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
        self._obb = Box.from_points(self.geometry.obb())

        self._obb.xsize += inflate
        self._obb.ysize += inflate
        self._obb.zsize += inflate
        return self._obb

    def compute_collision_mesh(self):
        """Computes the collision geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """
        points, faces = self.geometry.to_vertices_and_faces()
        vertices, faces = convex_hull_numpy(points)

        i_index = {i: index for index, i in enumerate(vertices)}
        vertices = [points[index] for index in vertices]
        faces = [[i_index[i] for i in face] for face in faces]

        self._collision_mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return Mesh.from_vertices_and_faces(points, faces)

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

    # ==========================================================================
    # Custom Parameters and methods specific to this class.
    # ==========================================================================

    @property
    def face_polygons(self):
        points_lists = self.geometry.to_polygons()
        return [Polygon(points) for points in points_lists]
