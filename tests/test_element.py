import pytest

from compas.data import json_dumps
from compas.data import json_loads
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Translation
from compas_model.elements import BrepElement
from compas_model.elements import Feature
from compas_model.elements import MeshElement
from compas_model.elements import PrimitiveElement
from compas_model.models import Model


def test_mesh_element_geometry_bounds_and_serialization():
    element = MeshElement(Box(2, 4, 6).to_mesh(), transformation=Translation.from_vector([1, 2, 3]), name="mesh")
    model = Model()
    model.add_element(element)

    assert isinstance(element.local_geometry, Mesh)
    assert element.base_geometry is not element.geometry
    assert element.aabb.xsize == pytest.approx(2)
    assert element.aabb.ysize == pytest.approx(4)
    assert element.aabb.zsize == pytest.approx(6)
    assert element.point == [1, 2, 3]

    restored = json_loads(json_dumps(element))
    assert isinstance(restored, MeshElement)
    assert restored.name == "mesh"
    assert isinstance(restored.geometry, Mesh)


def test_mesh_element_rejects_non_mesh_geometry():
    with pytest.raises(TypeError, match="should be a Mesh"):
        MeshElement(Box())  # type: ignore[arg-type]


def test_empty_mesh_element_has_no_bounds_or_spatial_results():
    model = Model()
    empty = model.add_element(MeshElement(Mesh()))
    solid = model.add_element(MeshElement(Box().to_mesh()))

    assert empty.is_empty
    assert not solid.is_empty
    with pytest.raises(ValueError, match="no axis-aligned bounding box"):
        _ = empty.aabb
    with pytest.raises(ValueError, match="no oriented bounding box"):
        _ = empty.obb
    assert empty.is_collision(solid) is False
    assert empty.compute_contacts(solid) == []
    assert [obj.payload for leaf in model.bvh.leaves for obj in leaf.objects] == [solid]
    assert list(model.collisions()) == []


def test_primitive_element_evaluates_to_mesh_and_serializes_primitive():
    element = PrimitiveElement(Box(2, 3, 4), name="box")
    model = Model()
    model.add_element(element)

    assert isinstance(element.local_geometry, Mesh)
    assert element.aabb.xsize == pytest.approx(2)

# def test_is_dirty_setter():
#     model = Model()
#     a = MyElement(name="a")
#     b = MyElement(name="b")
#     c = MyElement(name="c")
#     d = MyElement(name="d")
#     model.add_element(a)
#     model.add_element(b)
#     model.add_element(c)
#     model.add_element(d)
#     model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c
#     model.add_interaction(a, b, interaction=Interaction(name="i_b_c"))  # a affects b
#     a.is_dirty = False
#     b.is_dirty = False
#     c.is_dirty = False
#     d.is_dirty = False


def test_primitive_element_rejects_non_shape_geometry():
    with pytest.raises(TypeError, match="should be a Shape"):
        PrimitiveElement(Box().to_mesh())  # type: ignore[arg-type]


def test_brep_element_geometry_bounds_and_surface_mesh():
    pytest.importorskip("compas_occ")
    element = BrepElement(Box(2, 4, 6).to_brep(), name="brep")
    model = Model()
    model.add_element(element)

    assert isinstance(element.local_geometry, Brep)
    assert isinstance(element.surface_mesh, Mesh)
    assert element.aabb.xsize == pytest.approx(2, abs=1e-6)
    assert element.point == [0, 0, 0]


def test_brep_element_rejects_non_brep_geometry():
    with pytest.raises(TypeError, match="should be a Brep"):
        BrepElement(Box().to_mesh())  # type: ignore[arg-type]


def test_feature_mutation_apis_and_explicit_invalidation_update_revision():
    element = MeshElement(Box().to_mesh())
    feature = Feature(name="feature")

    element.add_feature(feature)
    assert element.features == (feature,)
    assert element.geometry_revision == 1

    element.remove_feature(feature)
    assert element.features == ()
    assert element.geometry_revision == 2

    assert isinstance(element.geometry, Mesh)
    element.geometry.vertex_attribute(0, "x", 2.0)
    assert element.geometry_revision == 2
    element.invalidate_geometry()
    assert element.geometry_revision == 3
