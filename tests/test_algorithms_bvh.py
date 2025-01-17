import random
import pytest
from compas.geometry import Line
from compas.geometry import Sphere
from compas_model.geometry import intersection_ray_triangle
from compas_model.datastructures import BVH
from compas_model.datastructures import OBBNode
from compas_model.datastructures import AABBNode


@pytest.mark.parametrize("N", [1, 2, 3, 4, 5])
def test_bvh_leafsize(N):
    sphere = Sphere(1)
    mesh = sphere.to_mesh(triangulated=True, u=32, v=32)
    bvh = BVH.from_mesh(mesh, leafsize=N)
    for node in bvh.leaves:
        assert len(node.objects) <= N


@pytest.mark.parametrize(
    ["N", "nodetype"],
    [
        [10, OBBNode],
        [10, AABBNode],
        [100, OBBNode],
        [100, AABBNode],
        # [1000, OBBNode],
        # [1000, AABBNode],
    ],
)
def test_bvh_intersections_sphere(N, nodetype):
    sphere = Sphere(5)
    mesh = sphere.to_mesh(triangulated=True, u=32, v=32)
    bvh = BVH.from_mesh(mesh, nodetype=nodetype)

    lines = []
    for i in range(N):
        direction = [
            random.choice([-1, +1]) * random.random(),
            random.choice([-1, +1]) * random.random(),
            random.choice([-1, +1]) * random.random(),
        ]
        lines.append(
            Line.from_point_direction_length(
                point=[0, 0, 0],
                direction=direction,
                length=7,
            )
        )

    count = 0
    for line in lines:
        found = []
        for node in bvh.intersect_line(line):
            if not node.is_leaf:
                continue
            for index, centroid, triangle in node.objects:
                if index in found:
                    continue
                result = intersection_ray_triangle(line, triangle)
                if result is None:
                    continue
                found.append(index)
                count += 1

    assert count == N
