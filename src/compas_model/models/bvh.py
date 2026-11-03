from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from typing import TYPE_CHECKING
from typing import Optional

from compas.geometry import Box
from compas_model.datastructures import BVH
from compas_model.datastructures import AABBNode
from compas_model.datastructures import BVHNode
from compas_model.datastructures import BVHObject
from compas_model.datastructures import OBBNode
from compas_model.geometry import aabb_from_points
from compas_model.geometry import pca_box

if TYPE_CHECKING:
    from compas_model.elements import Element


class ElementAABBNode(AABBNode["Element"]):
    def compute_box(self) -> Box:
        return aabb_from_points(point for obj in self.objects for point in obj.points)


class ElementOBBNode(OBBNode["Element"]):
    def compute_box(self) -> Box:
        return pca_box(point for obj in self.objects for point in obj.points)


class ElementBVH(BVH["Element"]):
    def __init__(
        self,
        nodetype: type[BVHNode["Element"]] = ElementAABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> None:
        super().__init__(nodetype, max_depth, leafsize)

    @classmethod
    def from_elements(
        cls,
        elements: Iterable["Element"],
        nodetype: type[BVHNode["Element"]] = ElementAABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
        bounds: Optional[Callable[["Element"], Box]] = None,
    ) -> "ElementBVH":
        if bounds is None:
            bounds = (lambda element: element.obb) if issubclass(nodetype, OBBNode) else (lambda element: element.aabb)
        objects = []
        for index, element in enumerate(elements):
            box = bounds(element)
            objects.append(BVHObject(key=index, centroid=box.frame.point, payload=element, points=box.points))

        tree = cls(nodetype=nodetype, max_depth=max_depth, leafsize=leafsize)
        tree._add_objects(objects)
        return tree

    def overlap_elements(
        self,
        other: "ElementBVH",
        *,
        self_collision: bool = False,
    ) -> Iterator[tuple["Element", "Element"]]:
        """Yield element pairs from overlapping BVH leaves.

        Parameters
        ----------
        other
            The other element hierarchy.
        self_collision
            Enable comparison of the hierarchy with itself.

        Yields
        ------
        tuple[Element, Element]
            Broad-phase element collision candidates.

        Notes
        -----
        Candidate bounding volumes overlap, but the element geometries may not.
        Result ordering is not part of the public contract.

        """
        for object_a, object_b in self.overlap_pairs(other, self_collision=self_collision):
            yield object_a.payload, object_b.payload

    def nearby_elements(self, element: "Element", tolerance: float = 0.0) -> Iterator["Element"]:
        """Yield elements whose bounds are within an absolute distance of an element.

        Parameters
        ----------
        element
            The element around which to search.
        tolerance
            The absolute search distance.

        Yields
        ------
        Element
            Broad-phase proximity candidates, excluding ``element`` itself.

        Raises
        ------
        ValueError
            If ``tolerance`` is negative.

        Notes
        -----
        The query expands the element's axis-aligned bounding box by
        ``tolerance`` in every direction. The results are conservative: an
        element may be yielded even when its geometry is farther away.

        """
        if tolerance < 0:
            raise ValueError("The tolerance should be greater than or equal to zero.")
        bounds = element.aabb
        query = Box(
            bounds.xsize + 2 * tolerance,
            bounds.ysize + 2 * tolerance,
            bounds.zsize + 2 * tolerance,
            frame=bounds.frame,
        )
        seen = set()
        for node in self.intersect_box(query):
            if not node.is_leaf:
                continue
            for obj in node.objects:
                neighbor = obj.payload
                if neighbor is element or id(neighbor) in seen:
                    continue
                seen.add(id(neighbor))
                yield neighbor
