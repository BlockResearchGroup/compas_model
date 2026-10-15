import os
from types import SimpleNamespace
from typing import Any
from typing import cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("compas_viewer")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Point
from compas_model.elements import Element
from compas_model.elements import Group
from compas_model.models import Model
from compas_model.materials import Material
from compas_model.interactions import Contact
from compas_model.viewer import InteractionTreeForm
from compas_model.viewer import ElementInspector
from compas_model.viewer import ElementObject
from compas_model.viewer import ModelObject
from compas_model.viewer import ModelTreeForm
from compas_model.viewer import ModelViewer
from compas_model.viewer import inspect_elements


class MeshElement(Element):
    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["span"] = self.span
        return data

    def __init__(self, mesh: Mesh, name: str | None = None, span: float = 1.0) -> None:
        super().__init__(geometry=mesh, name=name)
        self.span = span

    def compute_elementgeometry(self, include_features: bool = False) -> Mesh | Brep:
        assert self.geometry is not None
        return self.geometry


class FakeScene:
    def add(self, item: Any, parent: Any = None, **kwargs: Any) -> Any:
        if isinstance(item, Model):
            scene_object = ModelObject(item=item, context="Viewer", **kwargs)
        elif isinstance(item, Element):
            scene_object = ElementObject(item=item, context="Viewer", **kwargs)
        else:
            scene_object = SimpleNamespace(item=item, show=kwargs.get("show", True), is_selected=kwargs.get("is_selected", False), children=[])
        if parent is not None:
            if hasattr(parent, "add"):
                parent.add(scene_object)
            else:
                parent.children.append(scene_object)
        return scene_object

    def add_group(self, name: str, show: bool = True) -> Any:
        group = SimpleNamespace(name=name, show=show, is_selected=False, children=[])
        return group


class FakeViewer:
    def __init__(self) -> None:
        self.scene = FakeScene()
        self.running = False
        display = SimpleNamespace(linewidth=1.0, pointsize=1.0, opacity=1.0)
        self.config = SimpleNamespace(ui=SimpleNamespace(display=display))


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return cast(QApplication, QApplication.instance()) if QApplication.instance() else QApplication([])


@pytest.fixture
def controller(monkeypatch, qt_app) -> tuple[ModelViewer, Group, MeshElement, MeshElement]:
    viewer = FakeViewer()
    monkeypatch.setattr("compas_viewer.viewer.Viewer", lambda: viewer)
    model = Model()
    group = cast(Group, model.add_element(Group(name="Assembly")))
    child = cast(MeshElement, model.add_element(MeshElement(Box().to_mesh(), name="Child"), parent=group))
    root = cast(MeshElement, model.add_element(MeshElement(Box().to_mesh(), name="Root element")))
    return ModelViewer(model, viewer=viewer, install_tree=False), group, child, root


def test_model_tree_form_uses_model_hierarchy_and_element_metadata(controller):
    model_viewer, group, child, root = controller
    tree = ModelTreeForm(model_viewer)

    assert tree.widget.topLevelItemCount() == 2
    assert tree.item_for_element(group).text(0) == "Assembly"
    assert tree.item_for_element(group).text(1) == "Group"
    assert tree.item_for_element(group).child(0) is tree.item_for_element(child)
    assert tree.item_for_element(root).parent() is None


def test_model_tree_selection_updates_scene_and_supports_multiple_items(controller, qt_app):
    model_viewer, _, child, root = controller
    tree = ModelTreeForm(model_viewer)

    tree.item_for_element(child).setSelected(True)
    tree.item_for_element(root).setSelected(True)
    qt_app.processEvents()

    assert model_viewer.selected == [model_viewer.object_for_element(child), model_viewer.object_for_element(root)]

    model_viewer.select([root], clear=True)
    tree.update()

    assert not tree.item_for_element(child).isSelected()
    assert tree.item_for_element(root).isSelected()


def test_model_tree_group_visibility_applies_to_descendants(controller, qt_app):
    model_viewer, group, child, root = controller
    tree = ModelTreeForm(model_viewer)

    tree.item_for_element(group).setCheckState(2, Qt.CheckState.Unchecked)
    qt_app.processEvents()

    assert not model_viewer.object_for_element(group).show
    assert not model_viewer.object_for_element(child).show
    assert model_viewer.object_for_element(root).show

    tree.item_for_element(group).setCheckState(2, Qt.CheckState.Checked)
    qt_app.processEvents()

    assert model_viewer.object_for_element(group).show
    assert model_viewer.object_for_element(child).show


def test_model_tree_reports_selected_elements_to_callback(controller, qt_app):
    model_viewer, _, child, _ = controller
    reported: list[list[Element]] = []
    tree = ModelTreeForm(model_viewer, selection_changed=reported.append)

    tree.item_for_element(child).setSelected(True)
    qt_app.processEvents()

    assert reported[-1] == [child]


def test_model_tree_rejects_unknown_guid(controller):
    tree = ModelTreeForm(controller[0])

    with pytest.raises(KeyError, match="Unknown element GUID"):
        tree.item_for_guid("missing")


def test_element_inspection_reports_identity_parameters_attributes_material_and_geometry(controller):
    model_viewer, _, child, _ = controller
    material = Material(name="Example material")
    model_viewer.model.add_material(material)
    child.material = material
    child.treenode.attributes["discipline"] = "structure"

    sections = {section.title: dict(section.rows) for section in inspect_elements(model_viewer, [child])}

    assert sections["Identity"]["Name"] == "Child"
    assert sections["Parameters"]["span"] == "1.0"
    assert sections["Attributes"]["discipline"] == "structure"
    assert sections["Material"]["name"] == "Example material"
    assert sections["Geometry"]["Representation"] == "Mesh"
    assert sections["Geometry"]["Render triangles"] == "12"


def test_element_inspection_summarizes_multiple_and_empty_selection(controller):
    model_viewer, group, child, root = controller

    empty = inspect_elements(model_viewer, [])
    multiple = inspect_elements(model_viewer, [group, child, root])

    assert dict(empty[0].rows)["Status"] == "No elements selected"
    assert dict(multiple[0].rows)["Elements"] == "3"
    assert dict(multiple[0].rows)["Types"] == "Group: 1, MeshElement: 2"


def test_element_inspector_widget_tracks_controller_selection(controller, qt_app):
    model_viewer, _, child, _ = controller
    inspector = ElementInspector(model_viewer)
    model_viewer.inspector = inspector

    model_viewer.select([child], clear=True)
    qt_app.processEvents()

    identity = inspector.tree.topLevelItem(0)
    parameters = inspector.tree.topLevelItem(1)
    assert identity is not None
    assert parameters is not None
    assert identity.text(0) == "Identity"
    assert parameters.text(0) == "Parameters"


def test_model_tree_supports_type_and_collection_projections(controller, qt_app):
    model_viewer, group, child, root = controller
    primary = model_viewer.model.add_collection("Primary")
    primary.add_elements([child, root])
    overlap = model_viewer.model.add_collection("Overlap")
    overlap.add_element(root)
    types = ModelTreeForm(model_viewer, projection="types")
    collections = ModelTreeForm(model_viewer, projection="collections")

    assert types.widget.topLevelItemCount() == 2
    child_type = types.item_for_element(child).parent()
    root_type = types.item_for_element(root).parent()
    assert child_type is not None
    assert root_type is not None
    assert child_type.text(0) == "MeshElement"
    assert root_type.text(0) == "MeshElement"
    assert collections.widget.topLevelItemCount() == 3
    child_collection = collections.item_for_element(child).parent()
    group_collection = collections.item_for_element(group).parent()
    overlap_item = collections.widget.topLevelItem(1)
    assert child_collection is not None
    assert group_collection is not None
    assert overlap_item is not None
    overlap_member = overlap_item.child(0)
    assert overlap_member is not None
    assert child_collection.text(0) == "Primary"
    assert group_collection.text(0) == "Uncollected"
    assert overlap_member.text(0) == "Root element"

    mesh_type = types.item_for_element(child).parent()
    assert mesh_type is not None
    mesh_type.setSelected(True)
    qt_app.processEvents()
    assert {scene_object.element for scene_object in model_viewer.selected} == {child, root}

    mesh_type.setCheckState(2, Qt.CheckState.Unchecked)
    qt_app.processEvents()
    assert not model_viewer.object_for_element(child).show
    assert not model_viewer.object_for_element(root).show
    assert model_viewer.object_for_element(group).show

    model_viewer.show([child])
    types.update()
    assert mesh_type.checkState(2) == Qt.CheckState.PartiallyChecked


def test_interaction_tree_projects_contact_pairs_and_regions(controller, qt_app):
    model_viewer, _, child, root = controller
    edge = model_viewer.model.add_interaction(child, root)
    contacts = [
        Contact(
            [
                Point(0, 0, 0),
                Point(1, 0, 0),
                Point(1, 1, 0),
                Point(0, 1, 0),
            ]
        )
    ]
    model_viewer.model.graph.edge_attribute(edge, name="contacts", value=contacts)
    reported = []
    tree = InteractionTreeForm(model_viewer, selection_changed=reported.append)

    assert tree.widget.topLevelItemCount() == 1
    interaction_root = tree.widget.topLevelItem(0)
    assert interaction_root is not None
    pair = interaction_root.child(0)
    assert pair is not None
    assert pair.text(0) == "Child ↔ Root element"
    assert pair.childCount() == 1
    assert pair.child(0).text(2) == "1"

    pair.child(0).setSelected(True)
    qt_app.processEvents()

    assert reported[-1].elements == (child, root)
    assert reported[-1].contacts == tuple(contacts)
    assert {scene_object.element for scene_object in model_viewer.selected} == {child, root}


def test_element_inspector_displays_contact_data(controller):
    model_viewer, _, child, root = controller
    contact = Contact(
        [
            Point(0, 0, 0),
            Point(1, 0, 0),
            Point(1, 1, 0),
            Point(0, 1, 0),
        ]
    )
    from compas_model.viewer import ContactSelection

    inspector = ElementInspector(model_viewer)
    inspector.inspect_contact(ContactSelection((child.graphnode, root.graphnode), (child, root), (contact,)))

    pair = inspector.tree.topLevelItem(0)
    region = inspector.tree.topLevelItem(1)
    assert pair is not None
    assert region is not None
    assert pair.text(0) == "Contact pair"
    assert pair.child(2).text(1) == "1"
    assert region.text(0) == "Region 1"
    assert region.child(1).text(1) == "4"


def test_contact_layer_uses_individual_objects_and_tree_visibility(qt_app, monkeypatch):
    model = Model()
    a, b = model.add_elements([MeshElement(Box().to_mesh(), name="A"), MeshElement(Box().to_mesh(), name="B")])
    edge = model.add_interaction(a, b)
    contacts = [Contact([Point(0, 0, z), Point(1, 0, z), Point(1, 1, z), Point(0, 1, z)]) for z in (0.0, 1.0)]
    model.graph.edge_attribute(edge, name="contacts", value=contacts)
    viewer = FakeViewer()
    monkeypatch.setattr("compas_viewer.viewer.Viewer", lambda: viewer)
    model_viewer = ModelViewer(model, viewer=viewer, install_tree=False)
    assert model_viewer.contact_layer is not None
    assert len(model_viewer.contact_layer) == 2
    assert model_viewer.contact_layer.view((*edge, 0)).scene_object is not model_viewer.contact_layer.view((*edge, 1)).scene_object

    tree = InteractionTreeForm(model_viewer)
    interaction_root = tree.widget.topLevelItem(0)
    assert interaction_root is not None
    pair = interaction_root.child(0)
    first = pair.child(0)

    first.setCheckState(3, Qt.CheckState.Unchecked)
    qt_app.processEvents()
    assert not model_viewer.contact_layer.view((*edge, 0)).scene_object.show
    assert model_viewer.contact_layer.view((*edge, 1)).scene_object.show

    interaction_root.setCheckState(3, Qt.CheckState.Unchecked)
    qt_app.processEvents()
    assert not model_viewer.contact_layer.group.show
    assert all(not view.scene_object.show for view in model_viewer.contact_layer)

    second = pair.child(1)
    second.setSelected(True)
    qt_app.processEvents()
    assert model_viewer.contact_layer.selected_keys == ((*edge, 1),)
