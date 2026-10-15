from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("compas_viewer")

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas_model.elements import Element
from compas_model.elements import Group
from compas_model.models import Model
from compas_model.viewer import ElementObject
from compas_model.viewer import ModelObject
from compas_model.viewer import ModelViewer
from compas_model.viewer import RenderSettings


class MeshElement(Element):
    def __init__(self, mesh: Mesh, name: str | None = None) -> None:
        super().__init__(geometry=mesh, name=name)

    def compute_elementgeometry(self, include_features: bool = False) -> Mesh | Brep:
        assert self.geometry is not None
        return self.geometry


class FakeScene:
    def add(self, item: Any, parent: Any = None, **kwargs: Any) -> ModelObject | ElementObject:
        if isinstance(item, Model):
            scene_object = ModelObject(item=item, context="Viewer", **kwargs)
        else:
            scene_object = ElementObject(item=item, context="Viewer", **kwargs)
        if parent is not None:
            parent.add(scene_object)
        return scene_object


class FakeRenderer:
    def __init__(self) -> None:
        self.update_count = 0

    def update(self) -> None:
        self.update_count += 1


class FakeViewer:
    def __init__(self) -> None:
        self.scene = FakeScene()
        self.renderer = FakeRenderer()
        self.running = False
        self.show_count = 0
        display = SimpleNamespace(linewidth=1.0, pointsize=1.0, opacity=1.0)
        self.config = SimpleNamespace(ui=SimpleNamespace(display=display))

    def show(self) -> None:
        self.show_count += 1


@pytest.fixture
def fake_viewer(monkeypatch) -> FakeViewer:
    viewer = FakeViewer()
    monkeypatch.setattr("compas_viewer.viewer.Viewer", lambda: viewer)
    return viewer


def test_model_viewer_builds_native_scene_hierarchy_and_guid_index(fake_viewer):
    model = Model()
    group = model.add_element(Group(name="assembly"))
    first = model.add_element(MeshElement(Box().to_mesh(), name="first"), parent=group)
    second = model.add_element(MeshElement(Box().to_mesh(), name="second"))

    controller = ModelViewer(model, viewer=fake_viewer)

    assert len(controller) == 3
    assert list(controller) == [controller.object_for_element(group), controller.object_for_element(first), controller.object_for_element(second)]
    assert controller.object_for_guid(str(first.guid)).element is first
    assert controller.model_object.children == [controller.object_for_element(group), controller.object_for_element(second)]
    assert controller.object_for_element(group).children == [controller.object_for_element(first)]
    assert controller.object_for_element(group).render_geometry is None
    assert controller.object_for_element(first).render_geometry is not None


def test_model_viewer_handles_empty_model(fake_viewer):
    controller = ModelViewer(Model(), viewer=fake_viewer)

    assert len(controller) == 0
    assert list(controller) == []
    assert controller.model_object.children == []


def test_model_viewer_selection_visibility_and_lookup_failures(fake_viewer):
    model = Model()
    first, second = model.add_elements([MeshElement(Box().to_mesh()), MeshElement(Box().to_mesh())])
    controller = ModelViewer(model, viewer=fake_viewer)

    controller.select([first], clear=True)
    controller.select([str(second.guid)])
    controller.hide([first])

    assert controller.selected == [controller.object_for_element(first), controller.object_for_element(second)]
    assert not controller.object_for_element(first).show
    assert controller.object_for_element(second).show

    controller.select([first], selected=False)
    controller.show([first])

    assert controller.selected == [controller.object_for_element(second)]
    assert controller.object_for_element(first).show
    with pytest.raises(KeyError, match="Unknown element GUID"):
        controller.object_for_guid("missing")
    with pytest.raises(KeyError, match="Unknown element GUID"):
        controller.hide(["missing"])


def test_model_viewer_refreshes_changed_geometry_with_shared_cache(fake_viewer):
    model = Model()
    first, second = model.add_elements([MeshElement(Box().to_mesh()), MeshElement(Box().to_mesh())])
    controller = ModelViewer(model, viewer=fake_viewer)
    first_object = controller.object_for_element(first)
    original = first_object.render_geometry

    assert not controller.refresh(first)
    assert controller.cache.hits == 1

    first.geometry = Box(2).to_mesh()
    changed = controller.refresh_all()

    assert changed == [controller.object_for_element(first), controller.object_for_element(second)]
    assert first_object.render_geometry is not original
    assert first_object.render_geometry is not None
    assert first_object.render_geometry.vertices[:, 0].max() == pytest.approx(1.0)


def test_model_viewer_tracks_implicit_model_units(fake_viewer):
    model = Model(unit="MM")
    element = model.add_element(MeshElement(Box().to_mesh()))
    controller = ModelViewer(model, viewer=fake_viewer)

    assert controller.settings.unit == "MM"
    assert controller.object_for_element(element).render_settings.unit == "MM"

    model.unit = "M"
    controller.refresh(element)

    assert controller.settings.unit == "M"
    assert controller.object_for_element(element).render_settings.unit == "M"


def test_model_viewer_rejects_explicit_unit_mismatch(fake_viewer):
    with pytest.raises(ValueError, match="match the model unit"):
        ModelViewer(Model(unit="MM"), viewer=fake_viewer, settings=RenderSettings(unit="M"))


def test_model_viewer_delegates_window_display(fake_viewer):
    controller = ModelViewer(Model(), viewer=fake_viewer)

    controller.show_viewer()

    assert fake_viewer.show_count == 1
