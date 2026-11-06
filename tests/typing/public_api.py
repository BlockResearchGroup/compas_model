import numpy as np

from compas.geometry import Frame
from compas.geometry import Point
from compas_model.algorithms.contacts import is_opposite_normal_normal
from compas_model.algorithms.contacts import is_opposite_vector_vector
from compas_model.algorithms.contacts import polygon_polygon_overlap
from compas_model.geometry import SectionResult


tuple_result: bool | np.bool_ = is_opposite_vector_vector((1, 0, 0), (-1, 0, 0))
array_result: bool | np.bool_ = is_opposite_normal_normal(np.array([1.0, 0.0, 0.0]), np.array([-1.0, 0.0, 0.0]))
regions = polygon_polygon_overlap(
    np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    np.array([0.0, 0.0, 1.0]),
    tolerance=1e-6,
    minimum_area=0.0,
)
distance: float = SectionResult(Frame.worldXY()).signed_distance(Point(0, 0, 1))

assert tuple_result
assert array_result
assert regions
assert distance == 1.0
