import pytest
from typing import Any
from typing import cast

from compas.data import json_dumps
from compas.data import json_loads
from compas.geometry import Box
from compas.geometry import Native
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Translation
from compas_model.elements import BrepElement
from compas_model.elements import Element
from compas_model.elements import Feature
from compas_model.elements import Group
from compas_model.elements import MeshElement
from compas_model.interactions import Contact
from compas_model.interactions import ContactRecord
from compas_model.interactions import InteractionRecord
from compas_model.interactions import ModifierRecord
from compas_model.geometry import PlanarRegion
from compas_model.modifiers import Modifier
from compas_model.models import Model
from compas_model.models import Collection


class BoxElement(Element):
    def __init__(self, box):
        super().__init__()
        self.box = box

    def compute_aabb(self, inflate=1.0):
        return self.box


class TestModifier(Modifier):
    __test__ = False

    def apply(self, source, target_geometry):
        return target_geometry


EVALUATION_LOG = []


class RecordingFeature(Feature):
    def apply(self, shape):
        EVALUATION_LOG.append(self.name)
        return shape


class RecordingModifier(Modifier):
    def apply(self, source, target_geometry):
        EVALUATION_LOG.append(self.name)
        return target_geometry


class InvalidModifier(Modifier):
    def apply(self, source, target_geometry) -> Any:
        return Point(0, 0, 0)


class TranslationFeature(Feature):
    def __init__(self, vector):
        super().__init__()
        self.vector = vector

    def apply(self, shape):
        return shape.transformed(Translation.from_vector(self.vector))


class TranslationModifier(Modifier):
    def __init__(self, vector):
        super().__init__()
        self.vector = vector

    def apply(self, source, target_geometry):
        return target_geometry.transformed(Translation.from_vector(self.vector))


def test_import():
    assert True


#     mock_model: Model = json_loads(json_dumps(mock_model))


def test_interaction_records_roundtrip_with_graph_references():
    model = Model()
    a, b = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box(frame=Frame([1, 0, 0])).polygonize(Native()).to_mesh())])
    relationship = model.add_interaction(a, b)
    contact = Contact(PlanarRegion(Polygon([Point(0.5, -0.5, -0.5), Point(0.5, 0.5, -0.5), Point(0.5, 0.5, 0.5), Point(0.5, -0.5, 0.5)])))
    contact_record = model.set_contacts(a, b, [contact])
    assert contact_record is not None

    restored = cast(Model, json_loads(json_dumps(model)))
    records = list(restored.interaction_records())

    assert [type(record) for record in records] == [InteractionRecord, ContactRecord]
    assert [str(record.guid) for record in records] == [str(relationship.guid), str(contact_record.guid)]
    edge = next(iter(restored.graph.edges()))
    assert restored.graph.edge_attribute(edge, name="record_ids") == [str(record.guid) for record in records]
    assert [str(item.guid) for record in restored.contact_records() for item in record.contacts] == [str(contact.guid)]


def test_model_serializes_stable_relationships_instead_of_tree_and_graph_internals():
    model = Model()
    parent = model.add_element(Group(name="parent"))
    first = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh(), name="first"), parent=parent)
    second = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh(), name="second"), parent=parent)
    parent.treenode.name = "parent node"
    first.treenode.name = "custom node"
    second.treenode.name = "second node"
    first.treenode.attributes["discipline"] = "structure"
    record = model.add_interaction(first, second)

    data = model.__data__
    assert "tree" not in data
    assert "graph" not in data
    assert data["hierarchy"] == [
        {"element": str(parent.guid), "parent": None, "name": "parent node", "attributes": {}},
        {"element": str(first.guid), "parent": str(parent.guid), "name": "custom node", "attributes": {"discipline": "structure"}},
        {"element": str(second.guid), "parent": str(parent.guid), "name": "second node", "attributes": {}},
    ]

    restored = cast(Model, json_loads(json_dumps(model)))
    restored_parent = restored.element_by_guid(str(parent.guid))
    restored_first = restored.element_by_guid(str(first.guid))
    restored_second = restored.element_by_guid(str(second.guid))

    assert list(restored.graph.nodes()) == [str(parent.guid), str(first.guid), str(second.guid)]
    assert restored_first.graphnode == str(first.guid)
    assert restored_first.parent is restored_parent
    assert restored_parent.children == [restored_first, restored_second]
    assert restored_first.treenode.name == "custom node"
    assert restored_first.treenode.attributes == {"discipline": "structure"}
    assert restored.graph.edge_attribute((str(first.guid), str(second.guid)), name="record_ids") == [str(record.guid)]


def test_model_loads_legacy_nested_hierarchy_without_restoring_graph_ids():
    model = Model()
    parent = model.add_element(Group(name="parent"))
    child = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh(), name="child"), parent=parent)
    legacy_data = dict(model.__data__)
    legacy_data.pop("hierarchy")
    legacy_data["tree"] = model.tree.__data__
    legacy_data["graph"] = model.graph.__data__
    for element in model.elements():
        element.model = None  # type: ignore
        element.treenode = None  # type: ignore
        element.graphnode = None  # type: ignore

    restored = Model.__from_data__(legacy_data)
    restored_parent = restored.element_by_guid(str(parent.guid))
    restored_child = restored.element_by_guid(str(child.guid))

    assert restored_child.parent is restored_parent
    assert restored_child.graphnode == str(child.guid)
    assert set(restored.graph.nodes()) == {str(parent.guid), str(child.guid)}


def test_removing_one_interaction_record_preserves_other_pair_records():
    model = Model()
    a, b = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box(frame=Frame([1, 0, 0])).polygonize(Native()).to_mesh())])
    relationship = model.add_interaction(a, b)
    contact_record = model.set_contacts(
        a,
        b,
        [Contact(PlanarRegion(Polygon([Point(0.5, -0.5, -0.5), Point(0.5, 0.5, -0.5), Point(0.5, 0.5, 0.5), Point(0.5, -0.5, 0.5)])))],
    )
    assert contact_record is not None

    model.remove_interaction_record(contact_record)

    assert model.has_interaction(a, b)
    assert list(model.interaction_records()) == [relationship]
    assert list(model.contact_records()) == []


def test_modifier_record_preserves_explicit_direction():
    model = Model()
    source, target = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box(frame=Frame([1, 0, 0])).polygonize(Native()).to_mesh())])
    modifier = TestModifier()

    record = model.add_modifier(source, target, modifier)

    assert isinstance(record, ModifierRecord)
    assert record.source == str(source.guid)
    assert record.target == str(target.guid)
    assert model.modifier_records_for(source) == []
    assert model.modifier_records_for(target) == [record]


def test_geometry_evaluation_stages_are_distinct_and_cached():
    model = Model()
    source = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    target = model.add_element(
        MeshElement(
            Box().polygonize(Native()).to_mesh(),
            transformation=Translation.from_vector([0, 2, 0]),
            features=[TranslationFeature([1, 0, 0])],
        )
    )
    model.add_modifier(source, target, TranslationModifier([0, 0, 3]))

    assert target.base_geometry.centroid() == pytest.approx([0, 0, 0])
    assert target.local_geometry.centroid() == pytest.approx([1, 0, 0])
    assert target.model_geometry.centroid() == pytest.approx([1, 2, 0])
    assert target.final_geometry.centroid() == pytest.approx([1, 2, 3])
    assert len({id(target.base_geometry), id(target.local_geometry), id(target.model_geometry), id(target.final_geometry)}) == 4


def test_geometry_stage_invalidation_preserves_earlier_caches():
    model = Model()
    source = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    target = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    base = target.base_geometry
    local = target.local_geometry
    model_geometry = target.model_geometry
    final = target.final_geometry

    record = model.add_modifier(source, target, TestModifier())

    assert target.base_geometry is base
    assert target.local_geometry is local
    assert target.model_geometry is model_geometry
    assert target._final_geometry is None
    assert target.final_geometry is not final

    final = target.final_geometry
    target.transform(Translation.from_vector([1, 0, 0]))

    assert target.base_geometry is base
    assert target.local_geometry is local
    assert target._model_geometry is None
    assert target._final_geometry is None
    assert target.final_geometry is not final

    model.remove_interaction_record(record)
    model_geometry = target.model_geometry
    target.add_feature(TranslationFeature([0, 1, 0]))

    assert target.base_geometry is base
    assert target._local_geometry is None
    assert target._model_geometry is None
    assert target._final_geometry is None
    assert target.model_geometry is not model_geometry


def test_features_precede_ordered_modifiers_and_reordering_invalidates_geometry():
    EVALUATION_LOG.clear()
    model = Model()
    source = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    target = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh(), features=[RecordingFeature(name="feature")]))
    first = model.add_modifier(source, target, RecordingModifier(name="first"))
    second = model.add_modifier(source, target, RecordingModifier(name="second"))

    target.final_geometry
    assert EVALUATION_LOG == ["feature", "first", "second"]

    revision = target.geometry_revision
    EVALUATION_LOG.clear()
    model.reorder_modifier_records(target, [second, first])
    target.final_geometry

    assert target.geometry_revision == revision + 1
    assert EVALUATION_LOG == ["second", "first"]
    assert [record.order for record in model.modifier_records_for(target)] == [0, 1]


def test_modifier_reordering_preserves_independent_target_caches():
    model = Model()
    source = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    target = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    first = model.add_modifier(source, target, TestModifier())
    second = model.add_modifier(source, target, TestModifier())
    local_geometry = target.local_geometry
    model_transformation = target.modeltransformation
    target.final_geometry

    model.reorder_modifier_records(target, [second, first])

    assert target.local_geometry is local_geometry
    assert target.modeltransformation is model_transformation
    assert target._final_geometry is None


def test_replacing_modifier_invalidates_only_final_dependent_geometry():
    model = Model()
    source, target, downstream, unrelated = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()) for _ in range(4)])
    record = model.add_modifier(source, target, TestModifier(name="original"))
    model.add_modifier(target, downstream, TestModifier())
    local_geometry = target.local_geometry
    model_transformation = target.modeltransformation
    target.final_geometry
    downstream.final_geometry
    unrelated.final_geometry
    revisions = {element: element.geometry_revision for element in model.elements()}
    replacement = TestModifier(name="replacement")

    model.replace_modifier(record, replacement)

    assert record.modifier is replacement
    assert target.local_geometry is local_geometry
    assert target.modeltransformation is model_transformation
    assert target._final_geometry is None
    assert downstream._final_geometry is None
    assert unrelated._final_geometry is not None
    assert source.geometry_revision == revisions[source]
    assert target.geometry_revision == revisions[target] + 1
    assert downstream.geometry_revision == revisions[downstream] + 1
    assert unrelated.geometry_revision == revisions[unrelated]


def test_replacing_modifier_rejects_unmanaged_record():
    model = Model()
    source, target = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box().polygonize(Native()).to_mesh())])
    record = ModifierRecord(str(source.guid), str(target.guid), TestModifier())

    with pytest.raises(ValueError, match="not part of the model"):
        model.replace_modifier(record, TestModifier())


def test_modifier_order_roundtrips_with_records():
    model = Model()
    source = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    target = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    first = model.add_modifier(source, target, Modifier())
    second = model.add_modifier(source, target, Modifier())
    model.reorder_modifier_records(target, [second, first])

    restored = cast(Model, json_loads(json_dumps(model)))
    restored_target = restored.element_by_guid(str(target.guid))
    restored_records = restored.modifier_records_for(restored_target)

    assert [str(record.guid) for record in restored_records] == [str(second.guid), str(first.guid)]
    assert [record.order for record in restored_records] == [0, 1]


def test_reorder_modifiers_requires_the_complete_unique_target_sequence():
    model = Model()
    source = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    target = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    first = model.add_modifier(source, target, Modifier())
    second = model.add_modifier(source, target, Modifier())

    with pytest.raises(ValueError, match="every modifier record"):
        model.reorder_modifier_records(target, [first])
    with pytest.raises(ValueError, match="duplicated"):
        model.reorder_modifier_records(target, [first, first])
    with pytest.raises(ValueError, match="every modifier record"):
        model.reorder_modifier_records(source, [first, second])


def test_modifiers_reject_dependency_cycles():
    model = Model()
    a, b, c = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()) for _ in range(3)])
    model.add_modifier(a, b, Modifier())
    model.add_modifier(b, c, Modifier())

    with pytest.raises(ValueError, match="cyclic"):
        model.add_modifier(c, a, Modifier())


def test_modifier_should_preserve_target_representation():
    model = Model()
    source, target = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box().polygonize(Native()).to_mesh())])
    model.add_modifier(source, target, InvalidModifier())

    with pytest.raises(TypeError, match="should return a Mesh"):
        target.final_geometry


def test_element_invalidation_is_local_and_follows_modifier_direction():
    model = Model()
    source, target, downstream, unrelated = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()) for _ in range(4)])
    model.add_modifier(source, target, TestModifier())
    model.add_modifier(target, downstream, TestModifier())
    revisions = {element: element.geometry_revision for element in model.elements()}

    source.geometry = Box(2, 2, 2).polygonize(Native()).to_mesh()

    assert source.geometry_revision == revisions[source] + 1
    assert target.geometry_revision == revisions[target] + 1
    assert downstream.geometry_revision == revisions[downstream] + 1
    assert unrelated.geometry_revision == revisions[unrelated]


def test_source_change_preserves_independent_downstream_caches():
    model = Model()
    source, target = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box().polygonize(Native()).to_mesh())])
    model.add_modifier(source, target, TestModifier())
    target_local_geometry = target.local_geometry
    target_model_transformation = target.modeltransformation
    target.final_geometry

    source.geometry = Box(2, 2, 2).polygonize(Native()).to_mesh()

    assert target.local_geometry is target_local_geometry
    assert target.modeltransformation is target_model_transformation
    assert target._final_geometry is None


def test_contact_records_do_not_invalidate_element_geometry():
    model = Model()
    a, b = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box().polygonize(Native()).to_mesh())])
    revisions = (a.geometry_revision, b.geometry_revision)
    contact = Contact(PlanarRegion(Polygon([Point(0, 0, 0), Point(1, 0, 0), Point(1, 1, 0), Point(0, 1, 0)])))

    record = model.set_contacts(a, b, [contact])
    assert record is not None
    model.remove_interaction_record(record)

    assert (a.geometry_revision, b.geometry_revision) == revisions


def test_removing_modifier_invalidates_only_target_and_downstream_dependants():
    model = Model()
    source, target, downstream, unrelated = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()) for _ in range(4)])
    model.add_modifier(source, target, TestModifier())
    model.add_modifier(target, downstream, TestModifier())
    record = model.modifier_records_for(target)[0]
    revisions = {element: element.geometry_revision for element in model.elements()}

    model.remove_interaction_record(record)

    assert source.geometry_revision == revisions[source]
    assert target.geometry_revision == revisions[target] + 1
    assert downstream.geometry_revision == revisions[downstream] + 1
    assert unrelated.geometry_revision == revisions[unrelated]


def test_model_collections_are_overlapping_nonhierarchical_sets():
    model = Model()
    a = model.add_element(Group(name="A"))
    b = model.add_element(Group(name="B"), parent=a)
    facade = model.add_collection("Facade", attributes={"discipline": "architecture"})
    phase = model.add_collection(Collection(name="Phase 1"))


# def test_model_deepcopy(mock_model: Model):
#     c_model = mock_model.copy()


def test_add_element_rejects_foreign_ownership_and_parent_without_partial_mutation():
    first = Model()
    second = Model()
    parent = first.add_element(Group(name="parent"))
    child = MeshElement(Box().polygonize(Native()).to_mesh())

    with pytest.raises(ValueError, match="parent element is not part"):
        second.add_element(child, parent=parent)
    assert list(second.elements()) == []
    assert child.model is None

    first.add_element(child, parent=parent)
    with pytest.raises(ValueError, match="already belongs"):
        second.add_element(child)
    assert child.model is first
    assert child.parent is parent


def test_remove_element_is_leaf_only_and_clears_ownership_links():
    model = Model()
    parent = model.add_element(Group(name="parent"))
    child = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()), parent=parent)

    with pytest.raises(ValueError, match="with children"):
        model.remove_element(parent)
    assert model.has_element(parent)
    assert model.has_element(child)
    assert child.parent is parent

    model.remove_element(child)

    assert not model.has_element(child)
    assert child.model is None
    assert child.treenode is None
    assert child.graphnode is None
    assert parent.children == []

    other = Model()
    other.add_element(child)
    assert child.model is other


def test_reparent_element_updates_subtree_placement_and_modifier_dependants():
    model = Model()
    first = model.add_element(Group(transformation=Translation.from_vector([1, 0, 0]), name="first"))
    second = model.add_element(Group(transformation=Translation.from_vector([5, 0, 0]), name="second"))
    child = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()), parent=first)
    grandchild = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()), parent=child)
    downstream = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    unrelated = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    model.add_modifier(child, downstream, TestModifier())
    assert child.point == [1, 0, 0]
    child_local_geometry = child.local_geometry
    revisions = {element: element.geometry_revision for element in model.elements()}

    model.reparent_element(child, second)

    assert child.parent is second
    assert child.point == [5, 0, 0]
    assert child.local_geometry is child_local_geometry
    assert child.geometry_revision == revisions[child] + 1
    assert grandchild.geometry_revision == revisions[grandchild] + 1
    assert downstream.geometry_revision == revisions[downstream] + 1
    assert first.geometry_revision == revisions[first]
    assert second.geometry_revision == revisions[second]
    assert unrelated.geometry_revision == revisions[unrelated]


def test_reparent_element_rejects_foreign_parent_and_cycles():
    model = Model()
    parent = model.add_element(Group(name="parent"))
    child = model.add_element(Group(name="child"), parent=parent)
    grandchild = model.add_element(Group(name="grandchild"), parent=child)
    foreign = Group(name="foreign")

    with pytest.raises(ValueError, match="parent element is not part"):
        model.reparent_element(child, foreign)
    with pytest.raises(ValueError, match="hierarchy cycle"):
        model.reparent_element(parent, grandchild)

    assert child.parent is parent
    assert grandchild.parent is child


def test_remove_elements_of_type_removes_matching_subtrees_leaf_first():
    model = Model()
    parent = model.add_element(Group(name="parent"))
    child = model.add_element(Group(name="child"), parent=parent)

    removed = model.remove_elements_of_type(Group)

    assert removed == [parent, child]
    assert list(model.elements()) == []


def test_remove_elements_of_type_rejects_nonmatching_children_before_mutation():
    model = Model()
    parent = model.add_element(Group(name="parent"))
    child = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()), parent=parent)

    with pytest.raises(ValueError, match="non-matching children"):
        model.remove_elements_of_type(Group)

    assert model.has_element(parent)
    assert model.has_element(child)


def test_model_collections_roundtrip_and_cleanup_removed_elements():
    model = Model()
    a, b = model.add_elements([Group(name="A"), Group(name="B")])
    collection = model.add_collection("Selection")
    collection.add_elements([a, b])


def test_import():
    assert True


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
    elements = [MeshElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).polygonize(Native()).to_mesh()) for offset in [0, 0.25, 3]]
    model.add_elements(elements)

    assert set(model.collisions()) == {(elements[0], elements[1])}


def test_collision_geometry_stage_distinguishes_pre_and_post_modifier_geometry():
    model = Model()
    first = model.add_element(MeshElement(Box().polygonize(Native()).to_mesh()))
    second = model.add_element(MeshElement(Box(frame=Frame([3, 0, 0])).polygonize(Native()).to_mesh()))
    source = model.add_element(MeshElement(Box(frame=Frame([100, 0, 0])).polygonize(Native()).to_mesh()))
    model.add_modifier(source, second, TranslationModifier([-3, 0, 0]))

    assert not first.is_collision(second, geometry_stage="model")
    assert first.is_collision(second, geometry_stage="final")
    assert (first, second) not in set(model.collision_candidates(geometry_stage="model"))
    assert (first, second) in set(model.collision_candidates(geometry_stage="final"))
    assert (first, second) not in set(model.collisions(geometry_stage="model"))
    assert (first, second) in set(model.collisions(geometry_stage="final"))


def test_modifier_changes_invalidate_only_final_geometry_bvh():
    model = Model()
    source, target = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box(frame=Frame([3, 0, 0])).polygonize(Native()).to_mesh())])
    model_bvh = model.bvh_for("model")
    final_bvh = model.bvh_for("final")

    model.add_modifier(source, target, TranslationModifier([-3, 0, 0]))

    assert model.bvh_for("model") is model_bvh
    assert model.bvh_for("final") is not final_bvh


def test_collision_geometry_stage_is_validated():
    model = Model()
    first, second = model.add_elements([MeshElement(Box().polygonize(Native()).to_mesh()), MeshElement(Box().polygonize(Native()).to_mesh())])

    with pytest.raises(ValueError, match="geometry stage"):
        first.is_collision(second, geometry_stage="local")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="geometry stage"):
        list(model.collisions(geometry_stage="local"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="geometry stage"):
        list(model.collision_candidates(geometry_stage="local"))  # type: ignore[arg-type]


def test_model_compute_contacts_uses_absolute_tolerance_for_small_elements():
    model = Model()
    elements = [MeshElement(Box(0.001, 0.001, 0.001, frame=Frame([offset, 0, 0])).polygonize(Native()).to_mesh()) for offset in [0, 0.0015]]
    model.add_elements(elements)

    model.compute_contacts(tolerance=0.0005, minimum_area=1e-8)

    edge = (elements[0].graphnode, elements[1].graphnode)
    records = model.contact_records_between(elements[0], elements[1])
    assert len(records) == 1
    assert len(records[0].contacts) == 1
    record = records[0]
    assert model.graph.edge_attribute(edge, name="record_ids") == [str(record.guid)]


def test_model_compute_contacts_removes_stale_generated_edge():
    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1, frame=Frame([1, 0, 0])).polygonize(Native()).to_mesh()))

    model.compute_contacts()
    assert model.has_interaction(a, b)

    b.geometry = Box(1, 1, 1, frame=Frame([3, 0, 0])).polygonize(Native()).to_mesh()
    model.compute_contacts()

    assert not model.has_interaction(a, b)
    assert list(model.contact_records()) == []


def test_model_compute_contacts_preserves_explicit_edge_when_contact_disappears():
    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1, frame=Frame([1, 0, 0])).polygonize(Native()).to_mesh()))
    model.add_interaction(a, b)

    model.compute_contacts()
    assert model.contact_records_between(a, b)

    b.geometry = Box(1, 1, 1, frame=Frame([3, 0, 0])).polygonize(Native()).to_mesh()
    model.compute_contacts()

    assert model.has_interaction(a, b)
    assert model.contact_records_between(a, b) == []


def test_model_compute_contacts_replaces_existing_derived_contacts():
    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1, frame=Frame([1, 0.25, 0])).polygonize(Native()).to_mesh()))
    model.add_interaction(a, b)

    model.compute_contacts()
    first = model.contact_records_between(a, b)[0]
    assert first.contacts[0].size == pytest.approx(0.75)

    b.geometry = Box(1, 1, 1, frame=Frame([1, 0.5, 0])).polygonize(Native()).to_mesh()
    model.compute_contacts()
    second = model.contact_records_between(a, b)[0]

    assert second.contacts[0].size == pytest.approx(0.5)
    assert second is not first


def test_model_compute_contacts_does_not_mutate_graph_when_computation_fails(monkeypatch):
    model = Model()
    a = model.add_element(MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1, frame=Frame([1, 0, 0])).polygonize(Native()).to_mesh()))

    model.compute_contacts()
    edge = (a.graphnode, b.graphnode)
    original = next(model.contact_records())

    def fail(*args: object, **kwargs: object) -> list:
        raise RuntimeError("contact failure")

    monkeypatch.setattr(MeshElement, "compute_contacts", fail)

    with pytest.raises(RuntimeError, match="contact failure"):
        model.compute_contacts()

    assert model.graph.has_edge(edge)
    assert next(model.contact_records()) is original


def test_model_compute_contacts_validates_options_when_empty():
    model = Model()

    with pytest.raises(ValueError, match="tolerance"):
        model.compute_contacts(tolerance=-1)
    with pytest.raises(ValueError, match="minimum area"):
        model.compute_contacts(minimum_area=-1)


def test_model_fast_collisions_honor_positive_tolerance_outside_bvh_candidates():
    model = Model()
    elements = [MeshElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).polygonize(Native()).to_mesh()) for offset in [0, 1.01]]
    model.add_elements(elements)

    assert list(model.collision_candidates()) == []
    assert list(model.collisions(tolerance=0.02)) == [(elements[0], elements[1])]


def test_element_collision_rejects_unknown_precision():
    a = MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh())
    b = MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh())
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

    mesh_element = MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh())
    brep_element = BrepElement(Box(1, 1, 1).to_brep())
    model = Model()
    model.add_elements([mesh_element, brep_element])

    with pytest.raises(TypeError, match="mixed representations"):
        mesh_element.is_collision(brep_element)


def test_model_precise_mesh_collisions():
    pytest.importorskip("coal")
    model = Model()
    elements = [MeshElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).polygonize(Native()).to_mesh()) for offset in [0, 0.25, 3]]
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
    elements = [MeshElement(Box(1, 1, 1, frame=Frame([offset, 0, 0])).polygonize(Native()).to_mesh()) for offset in [0, 0.25, 0.5]]
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
    a = model.add_element(MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh()))
    b = model.add_element(MeshElement(Box(1, 1, 1).polygonize(Native()).to_mesh()))

    assert a.is_collision(b, precision="precise")
    assert len(calls) == 2

    a.transform(Translation.from_vector([0.1, 0, 0]))
    assert a.is_collision(b, precision="precise")
    assert len(calls) == 3

    model.transform(Translation.from_vector([0.1, 0, 0]))
    assert a.is_collision(b, precision="precise")
    assert len(calls) == 5

    a.geometry = Box(1, 1, 1).polygonize(Native()).to_mesh()
    assert a.is_collision(b, precision="precise")
    assert len(calls) == 6
