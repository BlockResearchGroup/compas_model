from typing import Generator
from typing import Optional
from typing import Type
from typing import Union

from compas.datastructures import Mesh
from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import centroid_points
from compas_model.algorithms import is_intersection_box_box
from compas_model.algorithms import is_intersection_line_aabb
from compas_model.algorithms import is_intersection_line_box
from compas_model.algorithms import pca_box


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

    def compute_box(self) -> Box:
        raise NotImplementedError

    def intersect_line(self, line: Line) -> Generator["BVHNode", None, None]:
        raise NotImplementedError

    def intersect_box(self, box: Box) -> Generator["BVHNode", None, None]:
        raise NotImplementedError


class AABBNode(BVHNode):
    """BVH tree node with an axis-aligned bounding box as bounding volume."""

    def compute_box(self) -> Box:
        """Compute the bounding volume as an oriented bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`

        """
        points = [point for o in self.objects for point in o[2]]
        return Box.from_points(points)

    def intersect_line(self, line: Line) -> Generator["AABBNode", None, None]:
        """"""
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_line_aabb(line, node.box):
                yield node
                queue.extend(node.children)


class OBBNode(BVHNode):
    """BVH tree node with an axis-aligned bounding box as bounding volume."""

    def compute_box(self) -> Box:
        """"""
        points = [point for o in self.objects for point in o[2]]
        return pca_box(points)

    def intersect_line(self, line: Line) -> Generator["OBBNode", None, None]:
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_line_box(line, node.box):
                yield node
                queue.extend(node.children)

    def intersect_box(self, box: Box) -> Generator["OBBNode", None, None]:
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_box_box(box, node.box):
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

    root: BVHNode

    def __init__(
        self,
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.nodetype = nodetype
        self.max_depth = max_depth
        self.leafsize = leafsize

    def _add_objects(
        self,
        objects: list[tuple[int, Point, list[Point]]],
        parent: BVHNode,
    ) -> None:
        if not objects:
            return

        node = self.nodetype(objects)
        parent.add(node)

        if node.is_root:
            node.depth = 0
        else:
            node.depth = parent.depth + 1

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

    @classmethod
    def from_triangles(
        cls,
        triangles: list[list[Point]],
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH":
        objects = [(index, centroid_points(abc), abc) for index, abc in enumerate(triangles)]

        tree = cls(nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects, parent=tree)
        return tree

    @classmethod
    def from_mesh(
        cls,
        mesh: Mesh,
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH":
        faces = list(mesh.faces())
        objects = list(zip(faces, [mesh.face_centroid(face) for face in faces], [mesh.face_points(face) for face in faces]))

        tree = cls(nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects, parent=tree)
        return tree

    def intersect_line(self, line: Line) -> Generator[BVHNode, None, None]:
        if self.root:
            for node in self.root.intersect_line(line):
                yield node

    def intersect_box(self, box: Box) -> Generator[BVHNode, None, None]:
        if self.root:
            for node in self.root.intersect_box(box):
                yield node
