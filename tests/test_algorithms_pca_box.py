import random
import math
from compas.geometry import Pointcloud
from compas.geometry import Translation
from compas.geometry import Rotation
from compas_model.geometry import pca_box


def test_point_containment():
    cloud = Pointcloud.from_bounds(8, 3, 1, 53)
    T = Translation.from_vector([10 * random.random(), 10 * random.random(), 10 * random.random()])
    R = Rotation.from_axis_and_angle([random.random(), random.random(), random.random()], math.radians(random.random() * 180))
    cloud.transform(T * R)
    box = pca_box(cloud)
    for point in cloud:
        assert box.contains_point(point)
