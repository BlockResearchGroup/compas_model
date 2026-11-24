from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from compas.colors import Color
from compas.scene import SceneObject
from compas_model.elements import Element
from compas_model.interactions import Contact

if TYPE_CHECKING:
    from .controller import ModelViewer

ContactKey = str


@dataclass(frozen=True, slots=True)
class ContactView:
    """One independently selectable contact-region scene object."""

    key: ContactKey
    edge: tuple[str, str]
    elements: tuple[Element, Element]
    contact: Contact
    scene_object: SceneObject


class ContactLayer:
    """Scene representation of contacts stored in a model interaction graph.

    Each planar region receives its own scene object. This intentionally avoids
    merging contact meshes because a merged buffer cannot support independent
    picking or visibility.
    """

    def __init__(self, controller: "ModelViewer", show: bool = True) -> None:
        self.controller = controller
        self.group = controller.viewer.scene.add_group(name="Contacts", show=show)
        self._views: dict[ContactKey, ContactView] = {}
        self._build(show=show)

    def __len__(self) -> int:
        return len(self._views)

    def __iter__(self) -> Iterator[ContactView]:
        return iter(self._views.values())

    def view(self, key: ContactKey) -> ContactView:
        """Return the view of one graph-edge contact region."""
        try:
            return self._views[key]
        except KeyError:
            raise KeyError(f"Unknown contact key: {key!r}.") from None

    def keys_for_edge(self, edge: tuple[str, str]) -> tuple[ContactKey, ...]:
        """Return contact keys belonging to an interaction edge."""
        return tuple(key for key, view in self._views.items() if view.edge == edge or view.edge == edge[::-1])

    def set_visibility(self, keys: Iterable[ContactKey], visible: bool) -> None:
        """Set visibility of individual contact regions."""
        scene = self.controller.viewer.scene
        requested = (self.view(key).scene_object for key in keys)
        objects = [obj for obj in requested if obj.scene is scene]
        if objects and visible and self.group.scene is scene:
            objects.insert(0, self.group)
        self._set_visibility(objects, visible)

    def set_all_visible(self, visible: bool) -> None:
        """Set visibility of the complete contact layer."""
        scene = self.controller.viewer.scene
        objects = [self.group, *(view.scene_object for view in self._views.values())]
        self._set_visibility([obj for obj in objects if obj.scene is scene], visible)

    def _set_visibility(self, objects: list[SceneObject], visible: bool) -> None:
        for obj in objects:
            obj.show = visible
        if objects and self.controller.viewer.running:
            self.controller.viewer.renderer.update()

    def select(self, keys: Iterable[ContactKey], clear: bool = True) -> None:
        """Set selection on contact-region scene objects."""
        requested_keys = set(keys)
        scene = self.controller.viewer.scene
        requested = [view.scene_object for key, view in self._views.items() if key in requested_keys and view.scene_object.scene is scene]
        selection = self.controller.viewer.state.selection
        if clear:
            contact_objects = {view.scene_object for view in self._views.values()}
            selection.replace([*(obj for obj in selection if obj not in contact_objects), *requested])
        else:
            selection.add(*requested)

    @property
    def selected_keys(self) -> tuple[ContactKey, ...]:
        """Keys of contact regions selected in the viewport."""
        selection = self.controller.viewer.state.selection
        scene = self.controller.viewer.scene
        return tuple(key for key, view in self._views.items() if view.scene_object.scene is scene and view.scene_object in selection)

    def _build(self, show: bool) -> None:
        color = Color(0.9, 0.15, 0.1)
        for record in self.controller.model.contact_records():
            elements = (self.controller.model.element_by_guid(record.element_a), self.controller.model.element_by_guid(record.element_b))
            edge = (elements[0].graphnode, elements[1].graphnode)
            u, v = edge
            for index, contact in enumerate(record.contacts):
                key = str(contact.guid)
                scene_object = self.controller.viewer.scene.add(
                    contact.mesh,
                    parent=self.group,
                    name=f"Contact {u}–{v} [{index + 1}]",
                    facecolor=color,
                    linecolor=color,
                    opacity=0.9,
                    show=show,
                    show_lines=False,
                )
                self._views[key] = ContactView(key, edge, elements, contact, scene_object)
