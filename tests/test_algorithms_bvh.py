import random

import pytest
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Sphere
from compas_model.datastructures import AABBNode
from compas_model.datastructures import BVH
from compas_model.datastructures import BVHObject
from compas_model.datastructures import OBBNode
from compas_model.elements import Element
from compas_model.geometry import intersection_ray_triangle
from compas_model.models.bvh import ElementBVH


class BoxElement(Element):
    def __init__(self, box):
        super().__init__()
        self.box = box

    def compute_aabb(self, inflate=1.0):
        return self.box


def sample_triangles():
    return [
        [Point(0, 0, 0), Point(1, 0, 0), Point(0, 1, 0)],
        [Point(2, 0, 0), Point(3, 0, 0), Point(2, 1, 0)],
        [Point(4, 0, 0), Point(5, 0, 0), Point(4, 1, 0)],
        [Point(6, 0, 0), Point(7, 0, 0), Point(6, 1, 0)],
        [Point(8, 0, 0), Point(9, 0, 0), Point(8, 1, 0)],
    ]


def shifted_triangles(offsets):
    return [[Point(x, 0, 0), Point(x + 1, 0, 0), Point(x, 1, 0)] for x in offsets]


def overlap_keys(a, b, self_collision=False):
    return {(object_a.key, object_b.key) for object_a, object_b in a.overlap_pairs(b, self_collision=self_collision)}


def test_bvh_empty_tree_queries_are_empty():
    bvh = BVH.from_triangles([])

    assert bvh.root is None
    assert list(bvh.intersect_line(Line([0, 0, 0], [1, 0, 0]))) == []
    assert list(bvh.intersect_box(Box())) == []
    assert list(bvh.intersect_sphere(Sphere(1))) == []


def test_bvh_overlap_pairs_with_empty_tree_is_empty():
    empty = BVH.from_triangles([])
    populated = BVH.from_triangles(sample_triangles())

    assert list(empty.overlap_pairs(populated)) == []
    assert list(populated.overlap_pairs(empty)) == []


def test_bvh_overlap_pairs_rejects_implicit_self_collision():
    bvh = BVH.from_triangles(sample_triangles())

    with pytest.raises(ValueError):
        list(bvh.overlap_pairs(bvh))


@pytest.mark.parametrize("leafsize", [1, 2, 4])
def test_bvh_overlap_pairs_finds_expected_candidates(leafsize):
    a = BVH.from_triangles(shifted_triangles([0, 2, 4]), leafsize=leafsize)
    b = BVH.from_triangles(shifted_triangles([0.5, 2.5, 10]), leafsize=leafsize)

    candidates = overlap_keys(a, b)

    assert {(0, 0), (1, 1)} <= candidates
    if leafsize == 1:
        assert (2, 2) not in candidates


def test_bvh_overlap_pairs_with_single_object_leaves_matches_brute_force():
    triangles_a = shifted_triangles([0, 2, 4])
    triangles_b = shifted_triangles([0.5, 2.5, 10])
    a = BVH.from_triangles(triangles_a, leafsize=1)
    b = BVH.from_triangles(triangles_b, leafsize=1)
    expected = set()

    for index_a, triangle_a in enumerate(triangles_a):
        for index_b, triangle_b in enumerate(triangles_b):
            object_a = BVHObject(key=index_a, centroid=Point(0, 0, 0), payload=triangle_a, points=triangle_a)
            object_b = BVHObject(key=index_b, centroid=Point(0, 0, 0), payload=triangle_b, points=triangle_b)
            if AABBNode([object_a]).overlaps(AABBNode([object_b])):
                expected.add((index_a, index_b))

    assert overlap_keys(a, b) == expected


def test_bvh_overlap_pairs_includes_touching_bounds():
    a = BVH.from_triangles(shifted_triangles([0]))
    b = BVH.from_triangles(shifted_triangles([1]))

    assert overlap_keys(a, b) == {(0, 0)}


def test_bvh_overlap_pairs_is_empty_for_separated_trees():
    a = BVH.from_triangles(shifted_triangles([0, 2]))
    b = BVH.from_triangles(shifted_triangles([10, 12]))

    assert overlap_keys(a, b) == set()


def test_bvh_overlap_pairs_reversed_tree_order_reverses_pairs():
    a = BVH.from_triangles(shifted_triangles([0, 2, 4]))
    b = BVH.from_triangles(shifted_triangles([0.5, 2.5, 10]))

    forward = overlap_keys(a, b)
    reverse = overlap_keys(b, a)

    assert forward == {(key_a, key_b) for key_b, key_a in reverse}


@pytest.mark.parametrize("nodetype_a", [AABBNode, OBBNode])
@pytest.mark.parametrize("nodetype_b", [AABBNode, OBBNode])
def test_bvh_overlap_pairs_supports_bounding_volume_combinations(nodetype_a, nodetype_b):
    a = BVH.from_mesh(Box().to_mesh(), nodetype=nodetype_a)
    b = BVH.from_mesh(Box(frame=Frame([0.25, 0, 0])).to_mesh(), nodetype=nodetype_b)

    assert list(a.overlap_pairs(b))


def test_bvh_self_collision_pairs_are_unique_and_exclude_identity():
    triangles = shifted_triangles([0, 0.25, 0.5])
    bvh = BVH.from_triangles(triangles, leafsize=1)
    candidates = overlap_keys(bvh, bvh, self_collision=True)

    assert candidates == {(0, 1), (0, 2), (1, 2)}
    assert all(key_a != key_b for key_a, key_b in candidates)


def test_bvh_self_collision_checks_all_objects_in_shared_leaf():
    bvh = BVH.from_triangles(shifted_triangles([0, 2, 4]), leafsize=3)

    assert overlap_keys(bvh, bvh, self_collision=True) == {(0, 1), (0, 2), (1, 2)}


@pytest.mark.parametrize("leafsize", [0, -1])
def test_bvh_rejects_invalid_leafsize(leafsize):
    with pytest.raises(ValueError):
        BVH(leafsize=leafsize)


def test_bvh_rejects_negative_max_depth():
    with pytest.raises(ValueError):
        BVH(max_depth=-1)


def test_bvh_node_enforces_binary_structure():
    parent = AABBNode([])
    left = AABBNode([])
    right = AABBNode([])

    parent.add(left)
    parent.add(right)

    assert parent.left is left
    assert parent.right is right
    assert parent.children == [left, right]
    assert left.parent is parent
    assert right.parent is parent
    assert not parent.is_leaf
    assert left.is_leaf

    with pytest.raises(ValueError):
        parent.add(AABBNode([]))


def test_bvh_node_rejects_child_with_existing_parent():
    parent = AABBNode([])
    other = AABBNode([])
    child = AABBNode([])
    parent.add(child)

    with pytest.raises(ValueError):
        other.add(child)


@pytest.mark.parametrize("max_depth", [0, 1, 2])
def test_bvh_respects_max_depth(max_depth):
    bvh = BVH.from_triangles(sample_triangles(), max_depth=max_depth)

    assert bvh.root is not None
    assert max(node.depth for node in bvh.nodes) == max_depth
    assert all(node.depth <= max_depth for node in bvh.nodes)


def test_bvh_assigns_child_depth_from_parent():
    bvh = BVH.from_triangles(sample_triangles())

    assert bvh.root is not None
    assert bvh.root.depth == 0
    assert all(child.depth == node.depth + 1 for node in bvh.nodes for child in node.children)


def test_bvh_construction_does_not_reorder_input_objects():
    triangles = sample_triangles()[:3]
    objects = [
        BVHObject(key=2, centroid=Point(4, 0, 0), payload=triangles[2], points=triangles[2]),
        BVHObject(key=0, centroid=Point(0, 0, 0), payload=triangles[0], points=triangles[0]),
        BVHObject(key=1, centroid=Point(2, 0, 0), payload=triangles[1], points=triangles[1]),
    ]
    original_order = [obj.key for obj in objects]

    bvh = BVH()
    bvh._add_objects(objects)

    assert [obj.key for obj in objects] == original_order


@pytest.mark.parametrize("nodetype", [AABBNode, OBBNode])
def test_bvh_node_overlap(nodetype):
    a = BVH.from_mesh(Box().to_mesh(), nodetype=nodetype)
    b = BVH.from_mesh(Box(frame=Frame([0.5, 0, 0])).to_mesh(), nodetype=nodetype)
    c = BVH.from_mesh(Box(frame=Frame([2, 0, 0])).to_mesh(), nodetype=nodetype)

    assert a.root is not None
    assert b.root is not None
    assert c.root is not None
    assert a.root.overlaps(b.root)
    assert b.root.overlaps(a.root)
    assert not a.root.overlaps(c.root)


def test_bvh_node_overlap_supports_mixed_bounding_volumes():
    a = BVH.from_mesh(Box().to_mesh(), nodetype=AABBNode)
    b = BVH.from_mesh(Box(frame=Frame([0.5, 0, 0])).to_mesh(), nodetype=OBBNode)

    assert a.root is not None
    assert b.root is not None
    assert a.root.overlaps(b.root)
    assert b.root.overlaps(a.root)


def test_element_bvh_nearest_neighbors_checks_every_object_in_leaf():
    element = BoxElement(Box())
    neighbor = BoxElement(Box(frame=Frame([0.25, 0, 0])))
    bvh = ElementBVH.from_elements([element, neighbor], leafsize=2)

    assert bvh.nearest_neighbors(element) == [neighbor]


def test_element_bvh_nearby_elements_uses_absolute_tolerance():
    element = BoxElement(Box(0.001, 0.001, 0.001))
    neighbor = BoxElement(Box(0.001, 0.001, 0.001, frame=Frame([0.0015, 0, 0])))
    bvh = ElementBVH.from_elements([element, neighbor])

    assert list(bvh.nearby_elements(element)) == []
    assert list(bvh.nearby_elements(element, tolerance=0.0005)) == [neighbor]


def test_element_bvh_nearby_elements_rejects_negative_tolerance():
    element = BoxElement(Box())
    bvh = ElementBVH.from_elements([element])

    with pytest.raises(ValueError, match="greater than or equal to zero"):
        list(bvh.nearby_elements(element, tolerance=-1))


def test_element_bvh_overlap_elements_returns_payloads():
    a0 = BoxElement(Box())
    a1 = BoxElement(Box(frame=Frame([3, 0, 0])))
    b0 = BoxElement(Box(frame=Frame([0.25, 0, 0])))
    b1 = BoxElement(Box(frame=Frame([6, 0, 0])))
    a = ElementBVH.from_elements([a0, a1])
    b = ElementBVH.from_elements([b0, b1])

    assert set(a.overlap_elements(b)) == {(a0, b0)}


def test_element_bvh_self_overlap_returns_unique_element_pairs():
    elements = [BoxElement(Box(frame=Frame([offset, 0, 0]))) for offset in [0, 0.25, 0.5]]
    bvh = ElementBVH.from_elements(elements)

    assert set(bvh.overlap_elements(bvh, self_collision=True)) == {
        (elements[0], elements[1]),
        (elements[0], elements[2]),
        (elements[1], elements[2]),
    }


@pytest.mark.parametrize("N", [1, 2, 3, 4, 5])
def test_bvh_leafsize(N):
    sphere = Sphere(1)
    mesh = sphere.to_mesh(triangulated=True, u=32, v=32)
    bvh = BVH.from_mesh(mesh, leafsize=N)
    for node in bvh.leaves:
        assert len(node.objects) <= N  # type: ignore


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
            for obj in node.objects:
                if obj.key in found:
                    continue
                result = intersection_ray_triangle(line, obj.payload)
                if result is None:
                    continue
                found.append(obj.key)
                count += 1

    assert count == N
