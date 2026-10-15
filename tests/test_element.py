import pytest

from compas.data import json_dumps
from compas.data import json_loads
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Translation
from compas_model.elements import BrepElement
from compas_model.elements import MeshElement
from compas_model.elements import PrimitiveElement
from compas_model.models import Model


def test_mesh_element_geometry_bounds_and_serialization():
    element = MeshElement(Box(2, 4, 6).to_mesh(), transformation=Translation.from_vector([1, 2, 3]), name="mesh")
    model = Model()
    model.add_element(element)

    assert isinstance(element.elementgeometry, Mesh)
    assert element.elementgeometry is not element.geometry
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


def test_primitive_element_evaluates_to_mesh_and_serializes_primitive():
    element = PrimitiveElement(Box(2, 3, 4), name="box")
    model = Model()
    model.add_element(element)

    assert isinstance(element.elementgeometry, Mesh)
    assert element.aabb.xsize == pytest.approx(2)

    restored = json_loads(json_dumps(element))
    assert isinstance(restored, PrimitiveElement)
    assert isinstance(restored.primitive, Box)
    assert restored.primitive.xsize == pytest.approx(2)


def test_primitive_element_rejects_non_shape_geometry():
    with pytest.raises(TypeError, match="should be a Shape"):
        PrimitiveElement(Box().to_mesh())  # type: ignore[arg-type]


def test_brep_element_geometry_bounds_and_surface_mesh():
    pytest.importorskip("compas_occ")
    element = BrepElement(Box(2, 4, 6).to_brep(), name="brep")
    model = Model()
    model.add_element(element)

    assert isinstance(element.elementgeometry, Brep)
    assert isinstance(element.surface_mesh, Mesh)
    assert element.aabb.xsize == pytest.approx(2, abs=1e-6)
    assert element.point == [0, 0, 0]


def test_brep_element_rejects_non_brep_geometry():
    with pytest.raises(TypeError, match="should be a Brep"):
        BrepElement(Box().to_mesh())  # type: ignore[arg-type]
