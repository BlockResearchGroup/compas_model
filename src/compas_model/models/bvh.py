from typing import TYPE_CHECKING
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
        nodetype: Optional[Union[ElementAABBNode, ElementOBBNode]] = ElementAABBNode,
        max_depth=None,
        leafsize=1,
        **kwargs,
    ):
        super().__init__(nodetype, max_depth, leafsize, **kwargs)

    @classmethod
    def from_elements(
        cls,
        elements: list["Element"],
        nodetype: Optional[Union[Type[ElementAABBNode], Type[ElementOBBNode]]] = AABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> "ElementBVH":
        objects: list[tuple[int, Point, "Element"]] = [(index, element.aabb.frame.point, element) for index, element in enumerate(elements)]

        tree = cls(nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects, parent=tree)
        return tree
