import pytest
from typing import cast

from compas.data import json_dumps
from compas.data import json_loads
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Translation
from compas_model.elements import BrepElement
from compas_model.elements import Element
from compas_model.elements import Group
from compas_model.elements import MeshElement
from compas_model.models import Model
from compas_model.models import Collection


class BoxElement(Element):
    def __init__(self, box):
        super().__init__()
        self.box = box

    def compute_aabb(self, inflate=1.0):
        return self.box


def test_import():
    assert True


def test_model_collections_are_overlapping_nonhierarchical_sets():
    model = Model()
    a = model.add_element(Group(name="A"))
    b = model.add_element(Group(name="B"), parent=a)
    facade = model.add_collection("Facade", attributes={"discipline": "architecture"})
    phase = model.add_collection(Collection(name="Phase 1"))

    facade.add_elements([a, b])
    phase.add_element(b)

    assert list(facade) == [a, b]
    assert list(phase) == [b]
    assert model.collections_for_element(b) == [facade, phase]
    assert b.parent is a
    assert facade.attributes == {"discipline": "architecture"}


def test_model_collections_roundtrip_and_cleanup_removed_elements():
    model = Model()
    a, b = model.add_elements([Group(name="A"), Group(name="B")])
    collection = model.add_collection("Selection")
    collection.add_elements([a, b])

    restored = cast(Model, json_loads(json_dumps(model)))
    restored_collection = restored.find_collection_with_name("Selection")

    assert restored_collection is not None
    assert [element.name for element in restored_collection] == ["A", "B"]
    restored.remove_element(next(element for element in restored.elements() if element.name == "A"))
    assert [element.name for element in restored_collection] == ["B"]


def test_collection_rejects_foreign_elements_and_removal_preserves_members():
    model = Model()
    element = model.add_element(Group(name="Member"))
    foreign = Group(name="Foreign")
    collection = model.add_collection("Set")

    with pytest.raises(ValueError, match="not part"):
        collection.add_element(foreign)

    collection.add_element(element)
    model.remove_collection(collection)
    assert model.has_element(element)
    assert collection.model is None


def test_model_collision_candidates_returns_unique_overlapping_pairs():
    model = Model()
    elements = [BoxElement(Box(frame=Frame([offset, 0, 0]))) for offset in [0, 0.25, 3]]
    model.add_elements(elements)

    assert set(model.collision_candidates()) == {(elements[0], elements[1])}


def test_model_collision_candidates_with_fewer_than_two_elements_is_empty():
    model = Model()
    assert list(model.collision_candidates()) == []

    model.add_element(BoxElement(Box()))
    assert list(model.collision_candidates()) == []


def test_model_spatial_indices_are_invalidated_when_elements_change():
    model = Model()
    element = model.add_element(BoxElement(Box()))
    original_bvh = model.bvh

    neighbor = model.add_element(BoxElement(Box(frame=Frame([0.25, 0, 0]))))
    assert model.bvh is not original_bvh

    current_bvh = model.bvh
    model.remove_element(neighbor)
    assert model.bvh is not current_bvh

    current_bvh = model.bvh
    element.transform(Translation.from_vector([1, 0, 0]))
    assert model.bvh is not current_bvh


def test_model_spatial_indices_are_invalidated_by_model_transformation():
    model = Model()
    model.add_element(BoxElement(Box()))
    original_bvh = model.bvh

    model.transform(Translation.from_vector([1, 0, 0]))

    assert model.bvh is not original_bvh


def test_model_fast_collisions_dispatch_geometry_checks():
    model = Model()
    elements = [MeshElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).to_mesh()) for offset in [0, 0.25, 3]]
    model.add_elements(elements)

    assert set(model.collisions()) == {(elements[0], elements[1])}


def test_model_compute_contacts_uses_absolute_tolerance_for_small_elements():
    model = Model()
    elements = [MeshElement(Box(0.001, 0.001, 0.001, frame=Frame([offset, 0, 0])).to_mesh()) for offset in [0, 0.0015]]
    model.add_elements(elements)

    model.compute_contacts(tolerance=0.0005, minimum_area=1e-8)

    edge = (elements[0].graphnode, elements[1].graphnode)
    contacts = model.graph.edge_attribute(edge, name="contacts")
    assert contacts is not None
    assert len(contacts) == 1
    assert model.graph.edge_attribute(edge, name="contacts_computed") is True
    assert model.graph.edge_attribute(edge, name="contact_edge") is True


def test_model_compute_contacts_removes_stale_generated_edge():
    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1, frame=Frame([1, 0, 0])).to_mesh()))

    model.compute_contacts()
    assert model.has_interaction(a, b)

    b.geometry = Box(1, 1, 1, frame=Frame([3, 0, 0])).to_mesh()
    model.compute_contacts()

    assert not model.has_interaction(a, b)
    assert list(model.contacts()) == []


def test_model_compute_contacts_preserves_explicit_edge_when_contact_disappears():
    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1, frame=Frame([1, 0, 0])).to_mesh()))
    edge = model.add_interaction(a, b)

    model.compute_contacts()
    assert model.graph.edge_attribute(edge, name="contacts")
    assert model.graph.edge_attribute(edge, name="contact_edge") is False

    b.geometry = Box(1, 1, 1, frame=Frame([3, 0, 0])).to_mesh()
    model.compute_contacts()

    assert model.has_interaction(a, b)
    assert model.graph.edge_attribute(edge, name="contacts") is None


def test_model_compute_contacts_replaces_existing_derived_contacts():
    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1, frame=Frame([1, 0.25, 0])).to_mesh()))
    edge = model.add_interaction(a, b)

    model.compute_contacts()
    first = model.graph.edge_attribute(edge, name="contacts")
    assert first is not None
    assert first[0].size == pytest.approx(0.75)

    b.geometry = Box(1, 1, 1, frame=Frame([1, 0.5, 0])).to_mesh()
    model.compute_contacts()
    second = model.graph.edge_attribute(edge, name="contacts")

    assert second is not None
    assert second[0].size == pytest.approx(0.5)
    assert second is not first


def test_model_compute_contacts_does_not_mutate_graph_when_computation_fails(monkeypatch):
    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1, frame=Frame([1, 0, 0])).to_mesh()))

    model.compute_contacts()
    edge = (a.graphnode, b.graphnode)
    original = model.graph.edge_attribute(edge, name="contacts")

    def fail(*args: object, **kwargs: object) -> list:
        raise RuntimeError("contact failure")

    monkeypatch.setattr(MeshElement, "compute_contacts", fail)

    with pytest.raises(RuntimeError, match="contact failure"):
        model.compute_contacts()

    assert model.graph.has_edge(edge)
    assert model.graph.edge_attribute(edge, name="contacts") is original


def test_model_compute_contacts_validates_options_when_empty():
    model = Model()

    with pytest.raises(ValueError, match="tolerance"):
        model.compute_contacts(tolerance=-1)
    with pytest.raises(ValueError, match="minimum area"):
        model.compute_contacts(minimum_area=-1)


def test_model_fast_collisions_honor_positive_tolerance_outside_bvh_candidates():
    model = Model()
    elements = [MeshElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).to_mesh()) for offset in [0, 1.01]]
    model.add_elements(elements)

    assert list(model.collision_candidates()) == []
    assert list(model.collisions(tolerance=0.02)) == [(elements[0], elements[1])]


def test_element_collision_rejects_unknown_precision():
    a = MeshElement(Box(1, 1, 1).to_mesh())
    b = MeshElement(Box(1, 1, 1).to_mesh())
    model = Model()
    model.add_elements([a, b])

    with pytest.raises(ValueError, match="Unsupported collision precision"):
        a.is_collision(b, precision="invalid")


def test_model_collision_rejects_invalid_options_when_empty():
    model = Model()

    with pytest.raises(ValueError, match="Unsupported collision precision"):
        list(model.collisions(precision="invalid"))
    with pytest.raises(ValueError, match="greater than or equal to zero"):
        list(model.collisions(tolerance=-1))


def test_element_collision_rejects_mixed_representations():
    pytest.importorskip("compas_occ")

    mesh_element = MeshElement(Box(1, 1, 1).to_mesh())
    brep_element = BrepElement(Box(1, 1, 1).to_brep())
    model = Model()
    model.add_elements([mesh_element, brep_element])

    with pytest.raises(TypeError, match="mixed representations"):
        mesh_element.is_collision(brep_element)


def test_model_precise_mesh_collisions():
    pytest.importorskip("coal")
    model = Model()
    elements = [MeshElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).to_mesh()) for offset in [0, 0.25, 3]]
    model.add_elements(elements)

    assert set(model.collisions(precision="precise")) == {(elements[0], elements[1])}


def test_model_precise_brep_collisions():
    pytest.importorskip("compas_occ")
    model = Model()
    elements = [BrepElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).to_brep()) for offset in [0, 0.25, 3]]
    model.add_elements(elements)

    assert set(model.collisions(precision="precise")) == {(elements[0], elements[1])}


def test_precise_collision_prepares_each_element_once(monkeypatch):
    pytest.importorskip("coal")
    import compas_model.elements.element as element_module

    prepare = element_module.prepare_mesh_collision
    calls = []

    def counting_prepare(mesh):
        calls.append(mesh)
        return prepare(mesh)

    monkeypatch.setattr(element_module, "prepare_mesh_collision", counting_prepare)

    model = Model()
    elements = [MeshElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).to_mesh()) for offset in [0, 0.25, 0.5]]
    model.add_elements(elements)

    assert len(list(model.collisions(precision="precise"))) == 3
    assert len(calls) == 3

    assert len(list(model.collisions(precision="precise"))) == 3
    assert len(calls) == 3


def test_precise_collision_cache_is_invalidated_by_geometry_changes(monkeypatch):
    pytest.importorskip("coal")
    import compas_model.elements.element as element_module

    prepare = element_module.prepare_mesh_collision
    calls = []

    def counting_prepare(mesh):
        calls.append(mesh)
        return prepare(mesh)

    monkeypatch.setattr(element_module, "prepare_mesh_collision", counting_prepare)

    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1).to_mesh()))

    assert a.is_collision(b, precision="precise")
    assert len(calls) == 2

    a.transform(Translation.from_vector([0.1, 0, 0]))
    assert a.is_collision(b, precision="precise")
    assert len(calls) == 4

    model.transform(Translation.from_vector([0.1, 0, 0]))
    assert a.is_collision(b, precision="precise")
    assert len(calls) == 6

    a.geometry = Box(1, 1, 1).to_mesh()
    assert a.is_collision(b, precision="precise")
    assert len(calls) == 8
