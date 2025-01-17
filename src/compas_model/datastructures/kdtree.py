from typing import TYPE_CHECKING
from typing import Optional

from compas.geometry import Point
from compas.geometry import distance_point_point_sqrd

if TYPE_CHECKING:
    from compas_model.elements import Element


class Node:
    def __init__(
        self,
        point: Point,
        axis: int,
        index: int,
        left: list[tuple["Element", int]],
        right: list[tuple["Element", int]],
    ):
        # point and axis define the splitting plane of the node
        # 0: xaxis, 1: yaxis, 2: zaxis
        self.point = point
        self.axis = axis
        # label identifies the median object
        # i.e. the index of the object at the splitting plane
        self.index = index
        # objects to the left of the splitting plane
        self.left = left
        # objects to the right og thr splitting plane
        self.right = right


class KDTree:
    """A tree for nearest neighbor search in a k-dimensional space.

    Parameters
    ----------
    objects : sequence[[float, float, float] | :class:`compas.geometry.Point`], optional
        A list of objects to populate the tree with.
        If objects are provided, the tree is built automatically.
        Otherwise, use :meth:`build`.

    Attributes
    ----------
    root : Node
        The root node of the built tree.
        This is the median with respect to the different dimensions of the tree.

    Notes
    -----
    For more info, see [1]_ and [2]_.

    References
    ----------
    .. [1] Wikipedia. *k-d tree*.
           Available at: https://en.wikipedia.org/wiki/K-d_tree.
    .. [2] Dell'Amico, M. *KD-Tree for nearest neighbor search in a K-dimensional space (Python recipe)*.
           Available at: http://code.activestate.com/recipes/577497-kd-tree-for-nearest-neighbor-search-in-a-k-dimensional-space/.

    """

    def __init__(self, elements: list["Element"]):
        self.elements = elements
        self.root = self._build([(element.aabb.frame.point, index) for index, element in enumerate(elements)])

    def _build(self, objects: list[tuple["Element", int]], axis: int = 0) -> Node:
        if not objects:
            # this is the start of the upward recursion traversal
            return
        objects.sort(key=lambda obj: obj[0][axis])
        median = len(objects) // 2
        point, index = objects[median]
        next_axis = (axis + 1) % 3
        return Node(
            point,
            axis,
            index,
            self._build(objects[:median], next_axis),
            self._build(objects[median + 1 :], next_axis),
        )

    def nearest_neighbor(self, point: Point, exclude: Optional[list["Element"]] = None) -> tuple["Element", float]:
        """Find the nearest neighbor to a given point,
        excluding neighbors that have already been found.

        Parameters
        ----------
        point : :class:`compas.geometry.Point`
            The base point.
        exclude : list[:class:`compas_model.elements.Element`], optional
            A sequence of point identified by their label to exclude from the search.

        Returns
        -------
        tuple[:class:`compas_model.elements.Element`, float]
            XYZ coordinates of the nearest neighbor.
            Label of the nearest neighbor.
            Distance to the base point.

        """

        def search(node: Node):
            if node is None:
                return

            d2 = distance_point_point_sqrd(point, node.point)
            if d2 < best[2]:
                if self.elements[node.index] not in exclude:
                    best[:] = node.point, node.index, d2

            d = point[node.axis] - node.point[node.axis]
            if d <= 0:
                close, far = node.left, node.right
            else:
                close, far = node.right, node.left

            search(close)
            if d**2 < best[2]:
                search(far)

        exclude = set(exclude or [])
        best = [None, None, float("inf")]
        search(self.root)
        return self.elements[best[1]], best[2] ** 0.5

    def nearest_neighbors(self, point: Point, number: int, distance_sort: bool = False) -> list[tuple["Element", float]]:
        """Find the N nearest neighbors to a given point.

        Parameters
        ----------
        point : :class:`compas.geometry.Point`
            The base point.
        number : int
            The number of nearest neighbors.
        distance_sort : bool, optional
            Sort the nearest neighbors by distance to the base point.

        Returns
        -------
        list[[[float, float, float], int or str, float]]
            A list of N nearest neighbors.

        """
        nnbrs = []
        exclude = set()
        for i in range(number):
            nnbr = self.nearest_neighbor(point, exclude)
            nnbrs.append(nnbr)
            exclude.add(nnbr[0])
        if distance_sort:
            return sorted(nnbrs, key=lambda nnbr: nnbr[1])
        return nnbrs
