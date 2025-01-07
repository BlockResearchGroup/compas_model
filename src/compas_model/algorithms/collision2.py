from typing import Union

from compas.geometry import Polygon
from compas.geometry import is_point_in_convex_polygon_xy

from .minkowski2 import minkdiff2


def is_collision2(A: Polygon, B: Polygon, return_diff: bool = False) -> Union[bool, tuple[bool, Polygon]]:
    C = minkdiff2(A, B)
    result = is_point_in_convex_polygon_xy([0, 0, 0], C)
    if not return_diff:
        return result
    return result, C
