import os
from collections.abc import Iterator
from types import SimpleNamespace
from typing import cast

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("compas_viewer")

from PySide6.QtCore import Qt
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Point
from compas.geometry import Polygon
from compas_model.elements import Element
from compas_model.elements import Group
from compas_model.models import Model
from compas_model.materials import Material
from compas_model.interactions import Contact
from compas_model.geometry import PlanarRegion
from compas_model.viewer import InteractionTreeForm
from compas_model.viewer import ElementInspector
from compas_model.viewer import ModelNavigationForm
from compas_model.viewer import ModelTreeForm
from compas_model.viewer import ModelViewer
from compas_model.viewer import inspect_elements
from compas_model.viewer import install_model_tree
from compas_model.viewer.compat import highlight_active_tab
from compas_viewer import Viewer
from compas_viewer.components.boundcomponent import BoundComponent
from compas_viewer.components.component import Component
from compas_viewer.components.tabform import Tabform
from compas_viewer.scene import ViewerScene
from compas_viewer.selection import Selection
from compas_viewer.singleton import SingletonMeta


class MeshElement(Element):
    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["span"] = self.span
        return data

    def __init__(self, mesh: Mesh, name: str | None = None, span: float = 1.0) -> None:
        super().__init__(geometry=mesh, name=name)
        self.span = span

    def compute_base_geometry(self) -> Mesh | Brep:
        assert self.geometry is not None
        return self.geometry


class FakeViewer:
    def __init__(self) -> None:
        self.scene = ViewerScene()
        self.state = SimpleNamespace(selection=Selection(self.scene.object))
        self.renderer = SimpleNamespace(update=lambda: None)
        self.running = False
        self.config = SimpleNamespace(display=SimpleNamespace(linewidth=1.0, pointsize=1.0, opacity=1.0))


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return cast(QApplication, QApplication.instance()) if QApplication.instance() else QApplication([])


@pytest.fixture
def viewer(monkeypatch, qt_app, registered_viewer_scene_objects) -> Iterator[Viewer]:
    monkeypatch.setattr(SingletonMeta, "_instances", {})
    monkeypatch.setattr(BoundComponent, "start_watching", lambda self: None)
    viewer = Viewer()
    try:
        yield viewer
    finally:
        window = viewer.ui.window.widget
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qt_app.processEvents()


@pytest.fixture
def controller(monkeypatch, qt_app, registered_viewer_scene_objects) -> tuple[ModelViewer, Group, MeshElement, MeshElement]:
    viewer = FakeViewer()
    monkeypatch.setattr("compas_viewer.Viewer", lambda: viewer)
    monkeypatch.setattr("compas_viewer.viewer.Viewer", lambda: viewer)
    model = Model()
    group = cast(Group, model.add_element(Group(name="Assembly")))
    child = cast(MeshElement, model.add_element(MeshElement(Box().to_polygonal_surface().to_mesh(), name="Child"), parent=group))
    root = cast(MeshElement, model.add_element(MeshElement(Box().to_polygonal_surface().to_mesh(), name="Root element")))
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


def test_model_navigation_highlights_hierarchy_tab(monkeypatch, qt_app):
    class Projection(Component):
        def update(self, refresh: bool = False) -> None:
            pass

    monkeypatch.setattr("compas_model.viewer.navigation.ModelTreeForm", lambda *args, **kwargs: Projection())
    monkeypatch.setattr("compas_model.viewer.navigation.InteractionTreeForm", lambda *args, **kwargs: Projection())
    navigation = ModelNavigationForm(SimpleNamespace(inspector=None))

    assert navigation.get_current_tab_name() == "Hierarchy"
    assert "QTabBar::tab:selected" in navigation.widget.styleSheet()


def test_model_viewer_installs_navigation_and_inspector_in_scene_page(viewer):
    model = Model()
    element = model.add_element(MeshElement(Box().to_polygonal_surface().to_mesh()))
    model_viewer = ModelViewer(model, viewer=viewer)
    sidebar = viewer.ui.sidebar

    assert [sidebar.widget.tabText(i) for i in range(sidebar.widget.count())] == ["Scene", "Data", "Annotations"]
    assert sidebar.scene_splitter.widget(0) is model_viewer.tree_form.widget
    assert sidebar.scene_details.widget(0) is sidebar.object_setting.widget
    assert sidebar.scene_details.widget(1) is model_viewer.inspector.widget

    viewer.state.selection.add(model_viewer.object_for_element(element))
    assert model_viewer.tree_form.hierarchy.item_for_element(element).isSelected()
    assert model_viewer.inspector.tree.topLevelItem(0).text(0) == "Identity"


def test_install_model_tree_uses_scene_hierarchy_slot_and_keeps_selection_callback(viewer):
    model = Model()
    element = model.add_element(MeshElement(Box().to_polygonal_surface().to_mesh()))
    model_viewer = ModelViewer(model, viewer=viewer, install_tree=False)
    reported = []

    tree = install_model_tree(model_viewer, selection_changed=reported.append)
    tree.item_for_element(element).setSelected(True)

    assert viewer.ui.sidebar.sceneform is tree
    assert viewer.ui.sidebar.scene_splitter.widget(0) is tree.widget
    assert reported == [[element]]


def test_model_viewer_actions_ignore_element_deleted_from_the_viewer_scene(viewer):
    model = Model()
    element = model.add_element(MeshElement(Box().to_polygonal_surface().to_mesh()))
    model_viewer = ModelViewer(model, viewer=viewer)
    projection = model_viewer.object_for_element(element)
    viewer.state.selection.add(projection)

    viewer.commands["viewer.delete_selected"].callback(viewer)

    assert model.element_by_guid(str(element.guid)) is element
    row = model_viewer.tree_form.hierarchy.item_for_element(element)
    assert row.isDisabled()
    assert row.checkState(2) == Qt.CheckState.Unchecked
    model_viewer.select([element], clear=True)
    model_viewer.hide([element])
    model_viewer.show([element])
    assert model_viewer.refresh(element) is False
    assert model_viewer.refresh_all() == []
    sections = {section.title: dict(section.rows) for section in inspect_elements(model_viewer, [element])}
    assert sections["Identity"]["Visible"] == "False"
    assert "Render triangles" not in sections["Geometry"]
    assert projection.scene is None
    assert projection not in viewer.state.selection
    assert projection.guid not in viewer.scene.render_objects


def test_model_viewer_keeps_viewport_contact_inspector_and_ignores_deleted_contact(viewer):
    model = Model()
    a, b = model.add_elements([MeshElement(Box().to_polygonal_surface().to_mesh()) for _ in range(2)])
    contact = Contact(PlanarRegion(Polygon([Point(0, 0, 0), Point(1, 0, 0), Point(1, 1, 0), Point(0, 1, 0)])))
    model.set_contacts(a, b, [contact])
    model_viewer = ModelViewer(model, viewer=viewer)
    layer = model_viewer.contact_layer
    key = str(contact.guid)
    projection = layer.view(key).scene_object

    viewer.state.selection.add(projection)

    assert model_viewer.inspector.tree.topLevelItem(0).text(0) == "Contact pair"
    assert model_viewer.inspector.tree.topLevelItem(1).text(0) == "Region 1"

    viewer.commands["viewer.delete_selected"].callback(viewer)
    row = model_viewer.tree_form.interactions.widget.topLevelItem(0).child(0).child(0)
    assert row.isDisabled()
    assert row.checkState(3) == Qt.CheckState.Unchecked
    layer.select([key])
    layer.set_visibility([key], False)
    layer.set_visibility([key], True)
    layer.set_all_visible(False)

    assert layer.selected_keys == ()
    assert projection.scene is None
    assert projection not in viewer.state.selection
    assert tuple(model.contact_records_between(a, b)[0].contacts) == (contact,)


def test_standard_object_tab_is_highlighted(qt_app):
    tabs = Tabform()
    tabs.add_tab("Object")
    tabs.add_tab("Camera")

    highlight_active_tab(tabs, current="Object")

    assert tabs.get_current_tab_name() == "Object"
    assert "QTabBar::tab:selected" in tabs.widget.styleSheet()


def test_controller_redraw_updates_standard_object_setting():
    updates = []
    controller = object.__new__(ModelViewer)
    controller.viewer = SimpleNamespace(
        ui=SimpleNamespace(sidebar=SimpleNamespace(object_setting=SimpleNamespace(update=lambda: updates.append(True)))),
        running=False,
    )
    controller.tree_form = None
    controller.inspector = None

    controller._redraw()

    assert updates == [True]


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
    contacts = [
        Contact(
            PlanarRegion(
                Polygon(
                    [
                        Point(0, 0, 0),
                        Point(1, 0, 0),
                        Point(1, 1, 0),
                        Point(0, 1, 0),
                    ]
                )
            )
        )
    ]
    model_viewer.model.set_contacts(child, root, contacts)
    reported = []
    tree = InteractionTreeForm(model_viewer, selection_changed=reported.append)

    assert tree.widget.topLevelItemCount() == 1
    interaction_root = tree.widget.topLevelItem(0)
    assert interaction_root is not None
    pair = interaction_root.child(0)
    assert pair is not None
    assert pair.text(0) == "Child ↔ Root element"
    assert pair.childCount() == 1
    region = pair.child(0)
    assert region is not None
    assert region.text(2) == "1"

    region.setSelected(True)
    qt_app.processEvents()

    assert reported[-1].elements == (child, root)
    assert reported[-1].contacts == tuple(contacts)
    assert model_viewer.selected == []

    region.setSelected(False)
    pair.setSelected(True)
    qt_app.processEvents()

    assert {scene_object.element for scene_object in model_viewer.selected} == {child, root}


def test_element_inspector_displays_contact_data(controller):
    model_viewer, _, child, root = controller
    contact = Contact(PlanarRegion(Polygon([Point(0, 0, 0), Point(1, 0, 0), Point(1, 1, 0), Point(0, 1, 0)])))
    from compas_model.viewer import ContactSelection

    inspector = ElementInspector(model_viewer)
    inspector.inspect_contact(ContactSelection((child.graphnode, root.graphnode), (child, root), (contact,)))

    pair = inspector.tree.topLevelItem(0)
    region = inspector.tree.topLevelItem(1)
    assert pair is not None
    assert region is not None
    assert pair.text(0) == "Contact pair"
    pair_count = pair.child(2)
    region_vertices = region.child(1)
    assert pair_count is not None
    assert region_vertices is not None
    assert pair_count.text(1) == "1"
    assert region.text(0) == "Region 1"
    assert region_vertices.text(1) == "4"


def test_contact_layer_uses_individual_objects_and_tree_visibility(qt_app, monkeypatch, registered_viewer_scene_objects):
    model = Model()
    a, b = model.add_elements([MeshElement(Box().to_polygonal_surface().to_mesh(), name="A"), MeshElement(Box().to_polygonal_surface().to_mesh(), name="B")])
    contacts = [Contact(PlanarRegion(Polygon([Point(0, 0, z), Point(1, 0, z), Point(1, 1, z), Point(0, 1, z)]))) for z in (0.0, 1.0)]
    model.set_contacts(a, b, contacts)
    viewer = FakeViewer()
    monkeypatch.setattr("compas_viewer.Viewer", lambda: viewer)
    monkeypatch.setattr("compas_viewer.viewer.Viewer", lambda: viewer)
    model_viewer = ModelViewer(model, viewer=viewer, install_tree=False)
    assert model_viewer.contact_layer is not None
    assert len(model_viewer.contact_layer) == 2
    assert model_viewer.contact_layer.view(str(contacts[0].guid)).scene_object is not model_viewer.contact_layer.view(str(contacts[1].guid)).scene_object

    tree = InteractionTreeForm(model_viewer)
    interaction_root = tree.widget.topLevelItem(0)
    assert interaction_root is not None
    pair = interaction_root.child(0)
    assert pair is not None
    first = pair.child(0)
    assert first is not None

    first.setCheckState(3, Qt.CheckState.Unchecked)
    qt_app.processEvents()
    assert not model_viewer.contact_layer.view(str(contacts[0].guid)).scene_object.show
    assert model_viewer.contact_layer.view(str(contacts[1].guid)).scene_object.show

    interaction_root.setCheckState(3, Qt.CheckState.Unchecked)
    qt_app.processEvents()
    assert not model_viewer.contact_layer.group.show
    assert all(not view.scene_object.show for view in model_viewer.contact_layer)

    second = pair.child(1)
    assert second is not None
    second.setSelected(True)
    qt_app.processEvents()
    assert model_viewer.contact_layer.selected_keys == (str(contacts[1].guid),)
