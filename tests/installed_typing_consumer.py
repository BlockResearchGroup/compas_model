import numpy as np

from compas.geometry import Frame
from compas.geometry import Point
from compas_model.algorithms.contacts import is_opposite_vector_vector
from compas_model.geometry import SectionResult


opposite: bool | np.bool_ = is_opposite_vector_vector((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0))
distance: float = SectionResult(Frame.worldXY()).signed_distance(Point(0.0, 0.0, 1.0))

assert opposite
assert distance == 1.0
