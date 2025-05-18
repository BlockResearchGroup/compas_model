from typing import TYPE_CHECKING
from typing import Iterable
from typing import Optional
from typing import Type
from typing import Union

from compas.geometry import Box
from compas.geometry import Point
from compas_model.datastructures import BVH
from compas_model.datastructures import AABBNode
from compas_model.datastructures import OBBNode
from compas_model.geometry import combine_aabbs
from compas_model.geometry import combine_obbs

if TYPE_CHECKING:
    from compas_model.elements import Element


class ElementAABBNode(AABBNode):
    objects: list[tuple[int, Point, "Element"]]

    def compute_box(self) -> Box:
        if len(self.objects) == 1:
            return self.objects[0][2].aabb
        return combine_aabbs([o[2].aabb for o in self.objects])


class ElementOBBNode(OBBNode):
    objects: list[tuple[int, Point, "Element"]]

    def compute_box(self) -> Box:
        if len(self.objects) == 1:
            return self.objects[0][2].obb
        return combine_obbs([o[2].obb for o in self.objects])


class ElementBVH(BVH):
    def __init__(
        self,
        nodetype: Optional[Union[Type[ElementAABBNode], Type[ElementOBBNode]]] = ElementAABBNode,
        max_depth=None,
        leafsize=1,
        **kwargs,
    ):
        super().__init__(nodetype, max_depth, leafsize, **kwargs)

    @classmethod
    def from_elements(
        cls,
        elements: Iterable["Element"],
        nodetype: Optional[Union[Type[ElementAABBNode], Type[ElementOBBNode]]] = ElementAABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "ElementBVH":
        objects: list[tuple[int, Point, "Element"]] = [(index, element.aabb.frame.point, element) for index, element in enumerate(elements)]

        tree = cls(nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects, parent=tree)
        return tree

    def nearest_neighbors(
        self,
        element: "Element",
    ) -> list["Element"]:
        """Find the N nearest neighbors to a given point.

        Parameters
        ----------
        element : :class:`Element`
            The base point.
        number : int
            The number of nearest neighbors.
        distance_sort : bool, optional
            Sort the nearest neighbors by distance to the base point.

        Returns
        -------
        list[:class:`Element`]
            A list of N nearest neighbors.

        """
        nnbrs = []
        box = element.compute_obb(inflate=1.2)
        for node in self.intersect_box(box):
            if node.is_leaf:
                nbr = node.objects[0][2]
                if nbr != element:
                    nnbrs.append(nbr)
        return nnbrs
