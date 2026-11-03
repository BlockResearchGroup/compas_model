import pytest

from compas.data import json_dumps
from compas.data import json_loads
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Frame
from compas_model.elements import BrepElement
from compas_model.elements import MeshElement
from compas_model.modifiers import BrepDifferenceModifier
from compas_model.modifiers import Modifier
from compas_model.models import Model


def test_brep_difference_modifier_serializes_without_a_backend_operation():
    restored = json_loads(json_dumps(BrepDifferenceModifier(name="cut")))

    assert isinstance(restored, BrepDifferenceModifier)
    assert restored.name == "cut"


def test_brep_difference_modifier_rejects_mesh_target_before_evaluating_source():
    model = Model()
    source, target = model.add_elements([MeshElement(Box().to_mesh()), MeshElement(Box().to_mesh())])
    modifier = BrepDifferenceModifier()

    with pytest.raises(TypeError, match="target geometry should be a BRep"):
        modifier.apply(source, target.final_geometry)


def test_brep_difference_modifier_rejects_mesh_source():
    pytest.importorskip("compas_occ")
    model = Model()
    source = model.add_element(MeshElement(Box().to_mesh()))
    target = model.add_element(BrepElement(Box().to_brep()))

    with pytest.raises(TypeError, match="source geometry should be a BRep"):
        BrepDifferenceModifier().apply(source, target.final_geometry)


@pytest.mark.parametrize(
    ("tool", "expected_volume"),
    [
        (Box(1, 1, 1, frame=Frame([0.75, 0, 0])), 7.25),
        (Box(1, 1, 1, frame=Frame([10, 0, 0])), 8.0),
        (Box(2, 2, 2), 0.0),
        (Box(2, 2, 2, frame=Frame([2, 0, 0])), 8.0),
    ],
    ids=["overlap", "separate", "identical", "touching"],
)
def test_brep_difference_modifier_boundary_cases(tool, expected_volume):
    pytest.importorskip("compas_occ")
    model = Model()
    source = model.add_element(BrepElement(tool.to_brep()))
    target = model.add_element(BrepElement(Box(2, 2, 2).to_brep()))
    model.add_modifier(source, target, BrepDifferenceModifier())

    assert target.final_geometry.volume == pytest.approx(expected_volume, abs=1e-6)


def test_empty_brep_difference_result_is_a_valid_terminal_geometry():
    pytest.importorskip("compas_occ")

    class UnexpectedModifier(Modifier):
        def apply(self, source, target_geometry):
            raise AssertionError("Modifiers after an empty result should not run.")

    model = Model()
    cutter = model.add_element(BrepElement(Box(2).to_brep()))
    unused_source = model.add_element(BrepElement(Box().to_brep()))
    target = model.add_element(BrepElement(Box(1).to_brep()))
    model.add_modifier(cutter, target, BrepDifferenceModifier())
    model.add_modifier(unused_source, target, UnexpectedModifier())

    assert target.is_empty
    assert model.bvh.root is not None
    assert all(obj.payload is not target for leaf in model.bvh.leaves for obj in leaf.objects)
    assert target.is_collision(cutter) is False
    assert target.compute_contacts(cutter) == []


def test_empty_brep_difference_source_is_a_noop():
    pytest.importorskip("compas_occ")
    empty = Brep.from_boolean_difference(Box(1).to_brep(), Box(2).to_brep())
    model = Model()
    source = model.add_element(BrepElement(empty))
    target = model.add_element(BrepElement(Box(2).to_brep()))

    result = BrepDifferenceModifier().apply(source, target.final_geometry)

    assert result.volume == pytest.approx(target.final_geometry.volume)


def test_brep_difference_modifier_roundtrips_with_model():
    pytest.importorskip("compas_occ")
    model = Model()
    source = model.add_element(BrepElement(Box(1, 1, 1, frame=Frame([0.75, 0, 0])).to_brep()))
    target = model.add_element(BrepElement(Box(2, 2, 2).to_brep()))
    record = model.add_modifier(source, target, BrepDifferenceModifier())

    restored = json_loads(json_dumps(model))
    restored_target = restored.element_by_guid(str(target.guid))
    restored_record = next(restored.modifier_records())

    assert str(restored_record.guid) == str(record.guid)
    assert isinstance(restored_record.modifier, BrepDifferenceModifier)
    assert restored_target.final_geometry.volume == pytest.approx(7.25, abs=1e-6)


def test_brep_difference_modifier_propagates_backend_failure(monkeypatch):
    pytest.importorskip("compas_occ")
    model = Model()
    source = model.add_element(BrepElement(Box().to_brep()))
    target = model.add_element(BrepElement(Box().to_brep()))

    def fail(cls, target_geometry, source_geometry):
        raise RuntimeError("boolean failure")

    monkeypatch.setattr(Brep, "from_boolean_difference", classmethod(fail))

    with pytest.raises(RuntimeError, match="boolean failure"):
        BrepDifferenceModifier().apply(source, target.final_geometry)
