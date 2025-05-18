from typing import Generator
from typing import Optional
from typing import Type
from typing import Union

from compas.datastructures import Mesh
from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polyhedron
from compas.geometry import Sphere
from compas.geometry import centroid_points
from compas_model.geometry import is_intersection_box_box
from compas_model.geometry import is_intersection_line_aabb
from compas_model.geometry import is_intersection_line_box
from compas_model.geometry import is_intersection_sphere_box
from compas_model.geometry import pca_box


class BVHNode(TreeNode):
    """Base BVH tree node.

    Parameters
    ----------
    objects : list[tuple[int, :class:`compas.geometry.Point`, list[:class:`compas.geometry.Point`]]]
        The objects contained by the node.

    Attributes
    ----------
    box : :class:`compas.geometry.Box`
        The bounding volume box.
        The type of box depends on the type of node.

    """

    def __init__(self, objects: list[tuple[int, Point, list[Point]]], **kwargs):
        super().__init__(**kwargs)
        self.objects = objects
        self.depth = 0
        self._box = None

    @property
    def box(self) -> Box:
        if not self._box:
            self._box = self.compute_box()
        return self._box

    def add(self, node):
        if self.parent is None:
            self.depth = 0
        else:
            self.depth = self.parent.depth + 1
        return super().add(node)

    def compute_box(self) -> Box:
        """Compute the bounding box of the node.

        Returns
        -------
        :class:`comaps.geometry.Box`

        """
        raise NotImplementedError

    def intersect_line(self, line: Line) -> Generator["BVHNode", None, None]:
        """Intersect this node with a line to find all intersected descending nodes.

        Parameters
        ----------
        line : :class:`compas.geometry.Line`

        Yields
        ------
        :class:`BVHNode`

        """
        raise NotImplementedError

    def intersect_box(self, box: Box) -> Generator["BVHNode", None, None]:
        """Intersect this node with a box to find all intersected descending nodes.

        Parameters
        ----------
        box : :class:`compas.geometry.Box`

        Yields
        ------
        :class:`BVHNode`

        """
        raise NotImplementedError

    def intersect_sphere(self, sphere: Sphere) -> Generator["BVHNode", None, None]:
        """Intersect this node with a sphere to find all intersected descending nodes.

        Parameters
        ----------
        sphere : :class:`compas.geometry.Sphere`

        Yields
        ------
        :class:`BVHNode`

        """
        raise NotImplementedError


class AABBNode(BVHNode):
    """BVH tree node with an axis-aligned bounding box as bounding volume."""

    def compute_box(self) -> Box:
        """Compute the axis-aligned box of the collections of primitives in this node.

        Returns
        -------
        :class:`compas.geometry.Box`

        """
        points = [point for o in self.objects for point in o[2]]
        return Box.from_points(points)

    def intersect_line(self, line: Line) -> Generator["AABBNode", None, None]:
        """Intersect this node with a line to find all intersected descending nodes.

        Parameters
        ----------
        line : :class:`compas.geometry.Line`

        Yields
        ------
        :class:`AABBNode`

        """
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_line_aabb(line, node.box):
                yield node
                queue.extend(node.children)


class OBBNode(BVHNode):
    """BVH tree node with an axis-aligned bounding box as bounding volume."""

    def compute_box(self) -> Box:
        """Compute the oriented box of the collections of primitives in this node.

        Returns
        -------
        :class:`compas.geometry.Box`

        """
        # if each primitive can compute its own OBB
        # this can be simplified and generalised
        # and the OBB of combinations of objects could be calculated from pre-calculated objects OBBs
        points = [point for o in self.objects for point in o[2]]
        return pca_box(points)

    def intersect_line(self, line: Line) -> Generator["OBBNode", None, None]:
        """Intersect this node with a line to find all intersected descending nodes.

        Parameters
        ----------
        line : :class:`compas.geometry.Line`

        Yields
        ------
        :class:`OBBNode`

        """
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_line_box(line, node.box):
                yield node
                queue.extend(node.children)

    def intersect_box(self, box: Box) -> Generator["OBBNode", None, None]:
        """Intersect this node with a box to find all intersected descending nodes.

        Parameters
        ----------
        box : :class:`compas.geometry.Box`

        Yields
        ------
        :class:`OBBNode`

        """
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_box_box(box, node.box):
                yield node
                queue.extend(node.children)

    def intersect_sphere(self, sphere: Sphere) -> Generator["OBBNode", None, None]:
        """Intersect this node with a line to find all intersected descending nodes.

        Parameters
        ----------
        sphere : :class:`compas.geometry.Sphere`

        Yields
        ------
        :class:`OBBNode`

        """
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_sphere_box(sphere, node.box):
                yield node
                queue.extend(node.children)


class BVH(Tree):
    """Bounding Volume Hierarchy as a special case of a (binary) tree.

    Parameters
    ----------
    nodetype : Type[:class:`AABBNode`] | Type[:class:`OBBNode`], optional
        The type of boundng volume node to use in the tree.
    max_depth : int, optional
        The maximum depth of the tree.
    leafsize : int, optional
        The number of objects contained by a leaf.

    Notes
    -----
    This class has the following constructors:

    * :meth:`BVH.from_triangles`
    * :meth:`BVH.from_mesh`

    References
    ----------
    ...

    Examples
    --------
    >>>

    """

    root: BVHNode  # type: ignore

    def __init__(
        self,
        nodetype: Union[Type[AABBNode], Type[OBBNode]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.nodetype = nodetype
        self.max_depth = max_depth
        self.leafsize = leafsize

    # =============================================================================
    # Building
    # =============================================================================

    # reorganise the objects sucht that the geometrical dta can be stored in numpy arrays
    # projections will be much faster

    def _add_objects(
        self,
        objects: list[tuple[int, Point, list[Point]]],
        parent: Union["BVH", BVHNode],
    ) -> None:
        if not objects:
            return

        node = self.nodetype(objects)
        parent.add(node)

        if len(objects) <= self.leafsize:
            return

        if self.max_depth and node.depth >= self.max_depth:
            return

        # sort objects according to xaxis box
        # (use the xaxis because it has the largest spread/variance)
        # perhaps axes should be rotated like in a KdTree?
        # also, lots of literature exists about splitting strategies for BVH trees
        # a common criterion is SAH (surface area heuristic)
        center = node.box.frame.point
        axis = node.box.frame.xaxis
        objects.sort(key=lambda o: (o[1] - center).dot(axis))
        median = len(objects) // 2

        # perhaps it woould make sense to make a specific binary tree
        # with left/right instead of a list of children

        # "left" objects
        self._add_objects(objects[:median], parent=node)

        # "right" objects
        self._add_objects(objects[median:], parent=node)

    # =============================================================================
    # Rebuilding & Refitting
    # =============================================================================

    def rebuild(self):
        """Rebuild the tree using the current objects."""
        raise NotImplementedError

    def refit(self):
        """Refit the tree to the current objects."""
        raise NotImplementedError

    # =============================================================================
    # Factory methods (aka "Constructors")
    # =============================================================================

    @classmethod
    def from_triangles(
        cls,
        triangles: list[list[Point]],
        nodetype: Union[Type[AABBNode], Type[OBBNode]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH":
        """Construct a BVH from a collection of triangles.

        Parameters
        ----------
        triangles : list[list[:class:`compas.geometry.Point`]]
            A list of triangles, with each triangle represented by three points.
        nodetype : Type[:class:`AABBNode`] | Type[:class:`OBBNode`], optional
            The type of node to use during construction.
        max_depth : int, optional
            The maximum depth of the tree.
        leafsize : int, optional
            The maximum number of triangles contained in a leaf node.

        Returns
        -------
        :class:`BVH`

        """
        objects = [(index, Point(*centroid_points(abc)), abc) for index, abc in enumerate(triangles)]

        tree = cls(nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects, parent=tree)
        return tree

    @classmethod
    def from_mesh(
        cls,
        mesh: Mesh,
        nodetype: Union[Type[AABBNode], Type[OBBNode]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH":
        """Construct a BVH from a mesh.

        Parameters
        ----------
        mesh : :class:`compas.datastructures.Mesh`
            A mesh data structure.
        nodetype : Type[:class:`AABBNode`] | Type[:class:`OBBNode`], optional
            The type of node to use during construction.
        max_depth : int, optional
            The maximum depth of the tree.
        leafsize : int, optional
            The maximum number of mesh faces contained in a leaf node.

        Returns
        -------
        :class:`BVH`

        """
        faces = list(mesh.faces())
        objects = []
        for face in faces:
            objects.append((face, mesh.face_centroid(face), mesh.face_points(face)))

        tree = cls(nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects, parent=tree)
        return tree

    @classmethod
    def from_polyhedrons(
        cls,
        polyhedrons: list[Polyhedron],
        nodetype: Union[Type[AABBNode], Type[OBBNode]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH":
        """Construct a BVH from a mesh.

        Parameters
        ----------
        polyhedrons : list[:class:`compas.geometry.Polyhedron`]
            A list of polyhedron objects.
        nodetype : Type[:class:`AABBNode`] | Type[:class:`OBBNode`], optional
            The type of node to use during construction.
        max_depth : int, optional
            The maximum depth of the tree.
        leafsize : int, optional
            The maximum number of polyhedrons contained in a leaf node.

        Returns
        -------
        :class:`BVH`

        """
        raise NotImplementedError

    @classmethod
    def from_meshes(
        cls,
        meshes: list[Mesh],
        nodetype: Union[Type[AABBNode], Type[OBBNode]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH":
        """Construct a BVH from a collection of meshes.

        Parameters
        ----------
        meshes : list[:class:`compas.datastructure.Mesh`]
            A list of mesh objects.
        nodetype : Type[:class:`AABBNode`] | Type[:class:`OBBNode`], optional
            The type of node to use during construction.
        max_depth : int, optional
            The maximum depth of the tree.
        leafsize : int, optional
            The maximum number of meshes contained in a leaf node.

        Returns
        -------
        :class:`BVH`

        """
        raise NotImplementedError

    @classmethod
    def from_breps(
        cls,
        triangles: list[Brep],
        nodetype: Union[Type[AABBNode], Type[OBBNode]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH":
        """Construct a BVH from a mesh.

        Parameters
        ----------
        breps : list[:class:`compas.geometry.Brep`]
            A list of brep objects.
        nodetype : Type[:class:`AABBNode`] | Type[:class:`OBBNode`], optional
            The type of node to use during construction.
        max_depth : int, optional
            The maximum depth of the tree.
        leafsize : int, optional
            The maximum number of breps contained in a leaf node.

        Returns
        -------
        :class:`BVH`

        """
        raise NotImplementedError

    # =============================================================================
    # Intersection Queries
    # =============================================================================

    def intersect_line(self, line: Line) -> Generator[BVHNode, None, None]:
        """Intersect the tree with a line to find all intersected nodes in descending order.

        Parameters
        ----------
        line : :class:`compas.geometry.Line`

        Yields
        ------
        :class:`BVHNode`

        """
        if self.root:
            for node in self.root.intersect_line(line):
                yield node

    def intersect_box(self, box: Box) -> Generator[BVHNode, None, None]:
        """Intersect the tree with a box to find all intersected nodes in descending order.

        Parameters
        ----------
        box : :class:`compas.geometry.Box`

        Yields
        ------
        :class:`BVHNode`

        """
        if self.root:
            for node in self.root.intersect_box(box):
                yield node

    def intersect_sphere(self, sphere: Sphere) -> Generator[BVHNode, None, None]:
        """Intersect the tree with a sphere to find all intersected nodes in descending order.

        Parameters
        ----------
        sphere : :class:`compas.geometry.Sphere`

        Yields
        ------
        :class:`BVHNode`

        """
        if self.root:
            for node in self.root.intersect_sphere(sphere):
                yield node

    # =============================================================================
    # NNBRS
    # =============================================================================

    def point_nnbrs(self, point):
        pass

    def object_nnbrs(self, object):
        pass

    def nnbrs(self, points: list[Point], k: int = 1, max_distance=None):
        pass
