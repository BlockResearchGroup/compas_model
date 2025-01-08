from typing import Generator
from typing import Optional
from typing import Type
from typing import Union

from compas.datastructures import Mesh
from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import centroid_points
from compas.geometry import oriented_bounding_box_numpy
from compas_model.algorithms.intersections import is_intersection_box_box
from compas_model.algorithms.intersections import is_intersection_line_aabb
from compas_model.algorithms.intersections import is_intersection_line_box


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
        return Box.from_bounding_box(oriented_bounding_box_numpy(points))

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
    root: BVHNode

    def _add_objects(
        self,
        objects: list[tuple[int, Point, list[Point]]],
        parent: BVHNode,
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = OBBNode,
    ) -> None:
        if not objects:
            return

        if len(objects) == 1:
            parent.add(nodetype(objects[:1]))
            return

        node = nodetype(objects)
        parent.add(node)

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
        self._add_objects(objects[:median], parent=node, nodetype=nodetype)

        # "right" objects
        self._add_objects(objects[median:], parent=node, nodetype=nodetype)

    @classmethod
    def from_triangles(
        cls,
        triangles: list[list[Point]],
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = OBBNode,
    ) -> "BVH":
        objects = [(index, centroid_points(abc), abc) for index, abc in enumerate(triangles)]
        tree = cls()
        tree._add_objects(objects, parent=tree, nodetype=nodetype)
        return tree

    @classmethod
    def from_mesh(
        cls,
        mesh: Mesh,
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = OBBNode,
    ) -> "BVH":
        faces = list(mesh.faces())
        objects = list(zip(faces, [mesh.face_centroid(face) for face in faces], [mesh.face_points(face) for face in faces]))
        tree = cls()
        tree._add_objects(objects, parent=tree, nodetype=nodetype)
        return tree

    def intersect_line(self, line: Line) -> Generator[BVHNode, None, None]:
        if self.root:
            for node in self.root.intersect_line(line):
                yield node

    def intersect_box(self, box: Box) -> Generator[BVHNode, None, None]:
        if self.root:
            for node in self.root.intersect_box(box):
                yield node
