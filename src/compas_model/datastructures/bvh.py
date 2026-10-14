from collections import deque
from collections.abc import Generator
from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any
from typing import Generic
from typing import Optional
from typing import TypeVar
from typing import cast

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polyhedron
from compas.geometry import Sphere
from compas.geometry import centroid_points
from compas_model.geometry import aabb_from_points
from compas_model.geometry import is_intersection_aabb_aabb
from compas_model.geometry import is_intersection_box_box
from compas_model.geometry import is_intersection_line_aabb
from compas_model.geometry import is_intersection_line_box
from compas_model.geometry import is_intersection_sphere_box
from compas_model.geometry import pca_box

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class BVHObject(Generic[T]):
    """Object record stored in a bounding volume hierarchy.

    Parameters
    ----------
    key
        Identifier of the object in its source collection.
    centroid
        Representative point used to partition the hierarchy.
    payload
        The application-specific object.
    points
        Points used to compute bounding volumes.

    """

    key: Hashable
    centroid: Point
    payload: T
    points: list[Point]


class BVHNode(Generic[T]):
    """Base BVH tree node.

    Parameters
    ----------
    objects
        The objects contained by the node.

    """

    def __init__(self, objects: list[BVHObject[T]]) -> None:
        self.objects = objects
        self.depth = 0
        self.parent: Optional["BVHNode[T]"] = None
        self.left: Optional["BVHNode[T]"] = None
        self.right: Optional["BVHNode[T]"] = None
        self._box = None

    @property
    def children(self) -> list["BVHNode[T]"]:
        """The child nodes in left-to-right order."""
        return [child for child in (self.left, self.right) if child is not None]

    @property
    def is_leaf(self) -> bool:
        """Determine whether the node has no children."""
        return self.left is None and self.right is None

    @property
    def box(self) -> Box:
        if not self._box:
            self._box = self.compute_box()
        return self._box

    def add(self, node: "BVHNode[T]") -> None:
        """Add a child node and update its hierarchy metadata.

        Raises
        ------
        ValueError
            If the node already has two children or the child already has a parent.

        """
        if node.parent is not None:
            raise ValueError("The node already has a parent.")
        if self.left is None:
            self.left = node
        elif self.right is None:
            self.right = node
        else:
            raise ValueError("A BVH node cannot have more than two children.")
        node.parent = self
        node.depth = self.depth + 1

    def overlaps(self, other: "BVHNode[Any]") -> bool:
        """Determine whether this node overlaps another node.

        Parameters
        ----------
        other
            The other node.

        Returns
        -------
        bool
            ``True`` if the node bounding boxes overlap.

        """
        raise NotImplementedError

    def compute_box(self) -> Box:
        """Compute the bounding box of the node.

        Returns
        -------
        Box
            The bounding box.

        """
        raise NotImplementedError

    def intersect_line(self, line: Line) -> Generator["BVHNode", None, None]:
        """Intersect this node with a line to find all intersected descending nodes.

        Parameters
        ----------
        line

        Yields
        ------
        BVHNode
            Intersected descending nodes.

        """
        raise NotImplementedError

    def intersect_box(self, box: Box) -> Generator["BVHNode", None, None]:
        """Intersect this node with a box to find all intersected descending nodes.

        Parameters
        ----------
        box

        Yields
        ------
        BVHNode
            Intersected descending nodes.

        """
        raise NotImplementedError

    def intersect_sphere(self, sphere: Sphere) -> Generator["BVHNode", None, None]:
        """Intersect this node with a sphere to find all intersected descending nodes.

        Parameters
        ----------
        sphere

        Yields
        ------
        BVHNode
            Intersected descending nodes.

        """
        raise NotImplementedError


class AABBNode(BVHNode[T]):
    """BVH tree node with an axis-aligned bounding box as bounding volume."""

    def compute_box(self) -> Box:
        """Compute the axis-aligned box of the collections of primitives in this node.

        Returns
        -------
        Box
            The axis-aligned box.

        """
        return aabb_from_points(point for obj in self.objects for point in obj.points)

    def overlaps(self, other: BVHNode[Any]) -> bool:
        """Determine whether this node overlaps another node."""
        if isinstance(other, AABBNode):
            return is_intersection_aabb_aabb(self.box, other.box)
        return is_intersection_box_box(self.box, other.box)

    def intersect_line(self, line: Line) -> Generator[BVHNode[T], None, None]:
        """Intersect this node with a line to find all intersected descending nodes.

        Parameters
        ----------
        line

        Yields
        ------
        AABBNode
            Intersected descending nodes.

        """
        queue: deque[BVHNode[T]] = deque([self])
        while queue:
            node = queue.popleft()
            if is_intersection_line_aabb(line, node.box):
                yield node
                queue.extend(node.children)

    def intersect_box(self, box: Box) -> Generator[BVHNode[T], None, None]:
        """Intersect this node with a box to find all intersected descending nodes.

        Parameters
        ----------
        box

        Yields
        ------
        AABBNode
            Intersected descending nodes.

        """
        queue: deque[BVHNode[T]] = deque([self])
        while queue:
            node = queue.popleft()
            if is_intersection_box_box(box, node.box):
                yield node
                queue.extend(node.children)


class OBBNode(BVHNode[T]):
    """BVH tree node with an oriented bounding box as bounding volume."""

    def compute_box(self) -> Box:
        """Compute the oriented box of the collections of primitives in this node.

        Returns
        -------
        Box
            The oriented box.

        """
        # if each primitive can compute its own OBB
        # this can be simplified and generalised
        # and the OBB of combinations of objects could be calculated from pre-calculated objects OBBs
        points = [point for obj in self.objects for point in obj.points]
        return pca_box(points)

    def overlaps(self, other: BVHNode[Any]) -> bool:
        """Determine whether this node overlaps another node."""
        return is_intersection_box_box(self.box, other.box)

    def intersect_line(self, line: Line) -> Generator[BVHNode[T], None, None]:
        """Intersect this node with a line to find all intersected descending nodes.

        Parameters
        ----------
        line

        Yields
        ------
        OBBNode
            Intersected descending nodes.

        """
        queue: deque[BVHNode[T]] = deque([self])
        while queue:
            node = queue.popleft()
            if is_intersection_line_box(line, node.box):
                yield node
                queue.extend(node.children)

    def intersect_box(self, box: Box) -> Generator[BVHNode[T], None, None]:
        """Intersect this node with a box to find all intersected descending nodes.

        Parameters
        ----------
        box

        Yields
        ------
        OBBNode
            Intersected descending nodes.

        """
        queue: deque[BVHNode[T]] = deque([self])
        while queue:
            node = queue.popleft()
            if is_intersection_box_box(box, node.box):
                yield node
                queue.extend(node.children)

    def intersect_sphere(self, sphere: Sphere) -> Generator[BVHNode[T], None, None]:
        """Intersect this node with a line to find all intersected descending nodes.

        Parameters
        ----------
        sphere

        Yields
        ------
        OBBNode
            Intersected descending nodes.

        """
        queue: deque[BVHNode[T]] = deque([self])
        while queue:
            node = queue.popleft()
            if is_intersection_sphere_box(sphere, node.box):
                yield node
                queue.extend(node.children)


class BVH(Generic[T]):
    """Binary bounding volume hierarchy.

    Parameters
    ----------
    nodetype
        The type of bounding volume node to use in the tree.
    max_depth
        The maximum depth of the tree.
    leafsize
        The number of objects contained by a leaf.

    """

    def __init__(
        self,
        nodetype: type[BVHNode[T]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> None:
        if max_depth is not None and max_depth < 0:
            raise ValueError("The maximum depth should be greater than or equal to zero.")
        if leafsize < 1:
            raise ValueError("The leaf size should be greater than zero.")
        self.nodetype = nodetype
        self.max_depth = max_depth
        self.leafsize = leafsize
        self.root: Optional[BVHNode[T]] = None

    @property
    def nodes(self) -> list[BVHNode[T]]:
        """All nodes in breadth-first order."""
        if self.root is None:
            return []
        nodes = []
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            nodes.append(node)
            queue.extend(node.children)
        return nodes

    @property
    def leaves(self) -> list[BVHNode[T]]:
        """All leaf nodes in breadth-first order."""
        return [node for node in self.nodes if node.is_leaf]

    # =============================================================================
    # Building
    # =============================================================================

    # reorganise the objects such that the geometrical data can be stored in numpy arrays
    # projections will be much faster

    def _add_objects(
        self,
        objects: list[BVHObject[T]],
        parent: Optional[BVHNode[T]] = None,
    ) -> None:
        if not objects:
            return

        node = self.nodetype(objects)
        if parent is None:
            if self.root is not None:
                raise ValueError("The BVH already has a root node.")
            self.root = node
        else:
            parent.add(node)

        if len(objects) <= self.leafsize:
            return

        if self.max_depth is not None and node.depth >= self.max_depth:
            return

        # sort objects according to xaxis box
        # (use the xaxis because it has the largest spread/variance)
        # perhaps axes should be rotated like in a KdTree?
        # also, lots of literature exists about splitting strategies for BVH trees
        # a common criterion is SAH (surface area heuristic)
        center = node.box.frame.point
        axis = sorted(zip(node.box.dimensions, node.box.frame.axes()), key=lambda item: item[0])[-1][1]
        ordered = sorted(objects, key=lambda obj: (obj.centroid - center).dot(axis))
        median = len(ordered) // 2

        # perhaps it would make sense to make a specific binary tree
        # with left/right instead of a list of children

        # "left" objects
        self._add_objects(ordered[:median], parent=node)

        # "right" objects
        self._add_objects(ordered[median:], parent=node)

    # =============================================================================
    # Rebuilding & Refitting
    # =============================================================================

    def rebuild(self) -> None:
        """Rebuild the tree using the current objects."""
        raise NotImplementedError

    def refit(self) -> None:
        """Refit the tree to the current objects."""
        raise NotImplementedError

    # =============================================================================
    # Factory methods (aka "Constructors")
    # =============================================================================

    @staticmethod
    def from_triangles(
        triangles: list[list[Point]],
        nodetype: type[BVHNode[list[Point]]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH[list[Point]]":
        """Construct a BVH from a collection of triangles.

        Parameters
        ----------
        triangles
            A list of triangles, with each triangle represented by three points.
        nodetype
            The type of node to use during construction.
        max_depth
            The maximum depth of the tree.
        leafsize
            The maximum number of triangles contained in a leaf node.

        Returns
        -------
        BVH
            The constructed tree.

        """
        objects = [BVHObject(key=index, centroid=Point(*centroid_points(abc)), payload=abc, points=abc) for index, abc in enumerate(triangles)]

        tree = BVH[list[Point]](nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects)
        return tree

    @staticmethod
    def from_mesh(
        mesh: Mesh,
        nodetype: type[BVHNode[list[Point]]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH[list[Point]]":
        """Construct a BVH from a mesh.

        Parameters
        ----------
        mesh
            A mesh data structure.
        nodetype
            The type of node to use during construction.
        max_depth
            The maximum depth of the tree.
        leafsize
            The maximum number of mesh faces contained in a leaf node.

        Returns
        -------
        BVH
            The constructed tree.

        """
        faces = list(mesh.faces())
        objects = []
        for face in faces:
            points = mesh.face_points(face)
            objects.append(BVHObject(key=face, centroid=mesh.face_centroid(face), payload=points, points=points))

        tree = BVH[list[Point]](nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects)
        return tree

    @classmethod
    def from_polyhedrons(
        cls,
        polyhedrons: list[Polyhedron],
        nodetype: type[BVHNode[Polyhedron]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH[Polyhedron]":
        """Construct a BVH from a collection of polyhedrons.

        Parameters
        ----------
        polyhedrons
            A list of polyhedron objects.
        nodetype
            The type of node to use during construction.
        max_depth
            The maximum depth of the tree.
        leafsize
            The maximum number of polyhedrons contained in a leaf node.

        Returns
        -------
        BVH
            The constructed tree.

        """
        raise NotImplementedError

    @classmethod
    def from_meshes(
        cls,
        meshes: list[Mesh],
        nodetype: type[BVHNode[Mesh]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH[Mesh]":
        """Construct a BVH from a collection of meshes.

        Parameters
        ----------
        meshes
            A list of mesh objects.
        nodetype
            The type of node to use during construction.
        max_depth
            The maximum depth of the tree.
        leafsize
            The maximum number of meshes contained in a leaf node.

        Returns
        -------
        BVH
            The constructed tree.

        """
        raise NotImplementedError

    @classmethod
    def from_breps(
        cls,
        triangles: list[Brep],
        nodetype: type[BVHNode[Brep]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "BVH[Brep]":
        """Construct a BVH from a collection of breps.

        Parameters
        ----------
        triangles
            A list of brep objects.
        nodetype
            The type of node to use during construction.
        max_depth
            The maximum depth of the tree.
        leafsize
            The maximum number of breps contained in a leaf node.

        Returns
        -------
        BVH
            The constructed tree.

        """
        raise NotImplementedError

    # =============================================================================
    # Intersection Queries
    # =============================================================================

    def overlap_pairs(
        self,
        other: "BVH[U]",
        *,
        self_collision: bool = False,
    ) -> Generator[tuple[BVHObject[T], BVHObject[U]], None, None]:
        """Yield broad-phase object pairs from overlapping BVH leaves.

        Parameters
        ----------
        other
            The other bounding volume hierarchy.
        self_collision
            Enable comparison of a hierarchy with itself. This is ignored when
            comparing different hierarchies.

        Yields
        ------
        tuple[BVHObject[T], BVHObject[U]]
            Pairs of object records from overlapping leaf nodes.

        Raises
        ------
        ValueError
            If a hierarchy is compared with itself without enabling
            ``self_collision``.

        Notes
        -----
        The yielded pairs are broad-phase candidates. Their bounding volumes
        overlap, but the underlying geometry may not. Result ordering is not
        part of the public contract.

        During self-collision traversal, an object is never paired with itself
        and each unordered object pair is yielded at most once.

        """
        if self is other and not self_collision:
            raise ValueError("Comparing a BVH with itself requires self_collision=True.")

        if self.root is None or other.root is None:
            return

        stack = [(self.root, other.root)]
        visited: set[tuple[int, int]] = set()

        while stack:
            node_a, node_b = stack.pop()

            if self is other:
                node_a_id = id(node_a)
                node_b_id = id(node_b)
                pair_id = (node_a_id, node_b_id) if node_a_id <= node_b_id else (node_b_id, node_a_id)
            else:
                pair_id = (id(node_a), id(node_b))

            if pair_id in visited:
                continue
            visited.add(pair_id)

            if not node_a.overlaps(node_b):
                continue

            if node_a is node_b:
                if node_a.is_leaf:
                    for index, object_a in enumerate(node_a.objects):
                        for object_b in node_a.objects[index + 1 :]:
                            yield object_a, cast(BVHObject[U], object_b)
                    continue

                children = node_a.children
                for index, child_a in enumerate(children):
                    stack.append((child_a, cast(BVHNode[U], child_a)))
                    for child_b in children[index + 1 :]:
                        stack.append((child_a, cast(BVHNode[U], child_b)))
                continue

            if node_a.is_leaf and node_b.is_leaf:
                for object_a in node_a.objects:
                    for object_b in node_b.objects:
                        yield object_a, object_b
                continue

            if node_a.is_leaf:
                stack.extend((node_a, child) for child in node_b.children)
                continue

            if node_b.is_leaf:
                stack.extend((child, node_b) for child in node_a.children)
                continue

            volume_a = node_a.box.xsize * node_a.box.ysize * node_a.box.zsize
            volume_b = node_b.box.xsize * node_b.box.ysize * node_b.box.zsize

            if volume_a >= volume_b:
                stack.extend((child, node_b) for child in node_a.children)
            else:
                stack.extend((node_a, child) for child in node_b.children)

    def intersect_line(self, line: Line) -> Generator[BVHNode, None, None]:
        """Intersect the tree with a line to find all intersected nodes in descending order.

        Parameters
        ----------
        line

        Yields
        ------
        BVHNode
            Intersected nodes.

        """
        if self.root:
            for node in self.root.intersect_line(line):
                yield node

    def intersect_box(self, box: Box) -> Generator[BVHNode, None, None]:
        """Intersect the tree with a box to find all intersected nodes in descending order.

        Parameters
        ----------
        box

        Yields
        ------
        BVHNode
            Intersected nodes.

        """
        if self.root:
            for node in self.root.intersect_box(box):
                yield node

    def intersect_sphere(self, sphere: Sphere) -> Generator[BVHNode, None, None]:
        """Intersect the tree with a sphere to find all intersected nodes in descending order.

        Parameters
        ----------
        sphere

        Yields
        ------
        BVHNode
            Intersected nodes.

        """
        if self.root:
            for node in self.root.intersect_sphere(sphere):
                yield node

    # =============================================================================
    # NNBRS
    # =============================================================================

    def point_nnbrs(self, point: Point) -> None:
        pass

    def object_nnbrs(self, object: object) -> None:
        pass

    def nnbrs(self, points: list[Point], k: int = 1, max_distance: Optional[float] = None) -> None:
        pass
