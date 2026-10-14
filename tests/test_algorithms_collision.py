import pytest

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Sphere
from compas_model.algorithms import is_box_box_collision
from compas_model.algorithms import is_brep_brep_collision
from compas_model.algorithms import is_brep_brep_collision_fast
from compas_model.algorithms import is_mesh_mesh_collision
from compas_model.algorithms import is_mesh_mesh_collision_fast
from compas_model.geometry import aabb_from_points


def translated_box_mesh(x):
    return Box(1, 1, 1, frame=Frame([x, 0, 0])).to_mesh()


@pytest.mark.parametrize(
    ("offset", "include_touching", "expected"),
    [
        (0.25, True, True),
        (1.0, True, True),
        (1.0, False, False),
        (1.01, True, False),
    ],
)
def test_fast_mesh_collision_boundaries(offset, include_touching, expected):
    assert (
        is_mesh_mesh_collision_fast(
            translated_box_mesh(0),
            translated_box_mesh(offset),
            include_touching=include_touching,
        )
        is expected
    )


def test_fast_mesh_collision_tolerance_bridges_small_gap():
    assert is_mesh_mesh_collision_fast(translated_box_mesh(0), translated_box_mesh(1.01), tolerance=0.02)


def test_fast_mesh_collision_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="At least one point"):
        is_mesh_mesh_collision_fast(Mesh(), translated_box_mesh(0))

    with pytest.raises(ValueError, match="greater than or equal to zero"):
        is_mesh_mesh_collision_fast(translated_box_mesh(0), translated_box_mesh(0), tolerance=-1)


def test_fast_mesh_collision_is_conservative():
    frame_a = Frame([-1, 0, 0])
    frame_b = Frame([1, 0, 0])
    vertices = Box(1, 1, 1, frame=frame_a).points + Box(1, 1, 1, frame=frame_b).points
    disconnected = Mesh.from_vertices_and_faces(vertices, [])
    centered = translated_box_mesh(0)

    assert is_mesh_mesh_collision_fast(disconnected, centered)


def test_fast_brep_collision_boundaries():
    pytest.importorskip("compas_occ")
    a = Box(1, 1, 1).to_brep()
    touching = Box(1, 1, 1, frame=Frame([1, 0, 0])).to_brep()
    separate = Box(1, 1, 1, frame=Frame([1.01, 0, 0])).to_brep()

    assert is_brep_brep_collision_fast(a, touching)
    # OCC pads computed bounds, so physically touching BReps conservatively
    # overlap even when boundary-only AABB contact is excluded.
    assert is_brep_brep_collision_fast(a, touching, include_touching=False)
    assert not is_brep_brep_collision_fast(a, separate)
    assert is_brep_brep_collision_fast(a, separate, tolerance=0.02)


def test_fast_brep_collision_uses_curved_extents():
    pytest.importorskip("compas_occ")
    sphere = Sphere(1).to_brep()
    other = Box(1, 1, 1, frame=Frame([0.75, 0, 0])).to_brep()

    assert is_brep_brep_collision_fast(sphere, other)


def test_box_collision_uses_oriented_box_test():
    assert is_box_box_collision(Box(1, 1, 1), Box(1, 1, 1, frame=Frame([0.5, 0, 0])))
    assert not is_box_box_collision(Box(1, 1, 1), Box(1, 1, 1, frame=Frame([2, 0, 0])))


def test_precise_mesh_collision_detects_surface_intersection():
    pytest.importorskip("coal")
    assert is_mesh_mesh_collision(translated_box_mesh(0), translated_box_mesh(0.5))
    assert not is_mesh_mesh_collision(translated_box_mesh(0), translated_box_mesh(2))


@pytest.mark.parametrize("offset", [(1, 0, 0), (1, 1, 0), (1, 1, 1)])
def test_precise_mesh_collision_includes_boundary_contact(offset):
    pytest.importorskip("coal")
    a = Box(1, 1, 1).to_mesh()
    b = Box(1, 1, 1, frame=Frame(offset)).to_mesh()
    assert is_mesh_mesh_collision(a, b)


def test_precise_mesh_collision_supports_tolerance():
    pytest.importorskip("coal")
    assert not is_mesh_mesh_collision(translated_box_mesh(0), translated_box_mesh(1.01))
    assert is_mesh_mesh_collision(translated_box_mesh(0), translated_box_mesh(1.01), tolerance=0.02)


def test_precise_mesh_collision_treats_meshes_as_surfaces():
    pytest.importorskip("coal")
    outer = Box(2, 2, 2).to_mesh()
    inner = Box(0.5, 0.5, 0.5).to_mesh()
    assert not is_mesh_mesh_collision(outer, inner)


def test_precise_mesh_collision_triangulates_polygon_faces():
    pytest.importorskip("coal")
    assert is_mesh_mesh_collision(Box(1, 1, 1).to_mesh(), translated_box_mesh(0.5))


def test_precise_mesh_collision_rejects_unsupported_or_invalid_inputs():
    pytest.importorskip("coal")
    valid = translated_box_mesh(0)
    degenerate = Mesh.from_vertices_and_faces([[0, 0, 0], [1, 0, 0], [2, 0, 0]], [[0, 1, 2]])

    with pytest.raises(NotImplementedError, match="exclude boundary-only contact"):
        is_mesh_mesh_collision(valid, valid, include_touching=False)
    with pytest.raises(ValueError, match="greater than or equal to zero"):
        is_mesh_mesh_collision(valid, valid, tolerance=-1)
    with pytest.raises(ValueError, match="requires vertices and faces"):
        is_mesh_mesh_collision(Mesh(), valid)
    with pytest.raises(ValueError, match="Degenerate mesh triangles"):
        is_mesh_mesh_collision(degenerate, valid)


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        ((0.5, 0, 0), True),
        ((1, 0, 0), True),
        ((1, 1, 0), True),
        ((1, 1, 1), True),
        ((1.01, 0, 0), False),
    ],
)
def test_precise_brep_collision_boundaries(offset, expected):
    pytest.importorskip("compas_occ")
    a = Box(1, 1, 1).to_brep()
    b = Box(1, 1, 1, frame=Frame(offset)).to_brep()
    assert is_brep_brep_collision(a, b) is expected


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        ((0.5, 0, 0), True),
        ((1, 0, 0), False),
        ((1, 1, 0), False),
        ((1, 1, 1), False),
        ((1.01, 0, 0), False),
    ],
)
def test_precise_brep_collision_can_exclude_touching(offset, expected):
    pytest.importorskip("compas_occ")
    a = Box(1, 1, 1).to_brep()
    b = Box(1, 1, 1, frame=Frame(offset)).to_brep()
    assert is_brep_brep_collision(a, b, include_touching=False) is expected


def test_precise_brep_collision_detects_solid_containment():
    pytest.importorskip("compas_occ")
    outer = Box(2, 2, 2).to_brep()
    inner = Box(0.5, 0.5, 0.5).to_brep()
    assert is_brep_brep_collision(outer, inner)
    assert is_brep_brep_collision(outer, inner, include_touching=False)


def test_precise_brep_collision_supports_distance_tolerance():
    pytest.importorskip("compas_occ")
    a = Box(1, 1, 1).to_brep()
    b = Box(1, 1, 1, frame=Frame([1.01, 0, 0])).to_brep()
    assert not is_brep_brep_collision(a, b)
    assert is_brep_brep_collision(a, b, tolerance=0.02)


def test_precise_brep_collision_supports_curved_geometry():
    pytest.importorskip("compas_occ")
    sphere = Sphere(1).to_brep()
    box = Box(1, 1, 1, frame=Frame([0.75, 0, 0])).to_brep()
    assert is_brep_brep_collision(sphere, box)
    assert is_brep_brep_collision(sphere, box, include_touching=False)


def test_precise_brep_collision_handles_nearly_tangent_curved_geometry():
    pytest.importorskip("compas_occ")
    sphere_a = Sphere(1, frame=Frame([0, 0, 0])).to_brep()
    touching = Sphere(1, frame=Frame([2, 0, 0])).to_brep()
    separated = Sphere(1, frame=Frame([2.001, 0, 0])).to_brep()

    assert is_brep_brep_collision(sphere_a, touching)
    assert not is_brep_brep_collision(sphere_a, touching, include_touching=False)
    assert not is_brep_brep_collision(sphere_a, separated)
    assert is_brep_brep_collision(sphere_a, separated, tolerance=0.002)


def test_precise_brep_collision_detects_small_positive_common_volume():
    pytest.importorskip("compas_occ")
    a = Box(1, 1, 1).to_brep()
    b = Box(1, 1, 1, frame=Frame([0.999, 0, 0])).to_brep()

    assert is_brep_brep_collision(a, b, include_touching=False)


def test_precise_collisions_support_large_coordinates():
    pytest.importorskip("coal")
    pytest.importorskip("compas_occ")
    origin = 1_000_000
    box_a = Box(1, 1, 1, frame=Frame([origin, origin, origin]))
    box_b = Box(1, 1, 1, frame=Frame([origin + 0.5, origin, origin]))

    assert is_mesh_mesh_collision(box_a.to_mesh(), box_b.to_mesh())
    assert is_brep_brep_collision(box_a.to_brep(), box_b.to_brep())


def test_precise_brep_collision_rejects_unsupported_semantics():
    pytest.importorskip("compas_occ")
    from compas_occ.brep import OCCBrep
    from compas_occ.brep import OCCBrepFace

    a = Box(1, 1, 1).to_brep()
    b = Box(1, 1, 1).to_brep()
    with pytest.raises(ValueError, match="greater than or equal to zero"):
        is_brep_brep_collision(a, b, tolerance=-1)
    with pytest.raises(NotImplementedError, match="positive tolerance"):
        is_brep_brep_collision(a, b, tolerance=0.1, include_touching=False)

    face = OCCBrepFace.from_polygon(Polygon([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]))
    surface = OCCBrep.from_native(face.occ_shape)
    with pytest.raises(NotImplementedError, match="requires two solids"):
        is_brep_brep_collision(surface, surface, include_touching=False)


def test_precise_brep_collision_rejects_missing_native_shape():
    pytest.importorskip("compas_occ")
    from compas_occ.brep import OCCBrep

    with pytest.raises(ValueError, match="no native OCC shape"):
        is_brep_brep_collision(OCCBrep(), Box(1, 1, 1).to_brep())


def test_aabb_from_points_supports_degenerate_bounds():
    point_box = aabb_from_points([Point(1, 2, 3)])
    planar_box = aabb_from_points([Point(0, 0, 2), Point(3, 4, 2)])

    assert (point_box.xsize, point_box.ysize, point_box.zsize) == (0, 0, 0)
    assert (planar_box.xsize, planar_box.ysize, planar_box.zsize) == (3, 4, 0)


def test_aabb_from_points_rejects_empty_input():
    with pytest.raises(ValueError, match="At least one point"):
        aabb_from_points([])
