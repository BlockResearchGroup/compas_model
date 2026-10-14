from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from compas.colors import Color
from compas_model.elements import Element
from compas_model.interactions import Contact

ContactKey = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class ContactView:
    """One independently selectable contact-region scene object."""

    key: ContactKey
    elements: tuple[Element, Element]
    contact: Contact
    scene_object: Any


class ContactLayer:
    """Scene representation of contacts stored in a model interaction graph.

    Each planar region receives its own scene object. This intentionally avoids
    merging contact meshes because a merged buffer cannot support independent
    picking or visibility.
    """

    def __init__(self, controller: Any, show: bool = True) -> None:
        self.controller = controller
        self.group = controller.viewer.scene.add_group(name="Contacts", show=show)
        self._views: dict[ContactKey, ContactView] = {}
        self._build(show=show)

    def __len__(self) -> int:
        return len(self._views)

    def __iter__(self):
        return iter(self._views.values())

    def view(self, key: ContactKey) -> ContactView:
        """Return the view of one graph-edge contact region."""
        try:
            return self._views[key]
        except KeyError:
            raise KeyError(f"Unknown contact key: {key!r}.") from None

    def keys_for_edge(self, edge: tuple[int, int]) -> tuple[ContactKey, ...]:
        """Return contact keys belonging to an interaction edge."""
        return tuple(key for key in self._views if key[:2] == edge)

    def set_visibility(self, keys: Iterable[ContactKey], visible: bool) -> None:
        """Set visibility of individual contact regions."""
        if visible:
            self.group.show = True
        for key in keys:
            self.view(key).scene_object.show = visible
        self._redraw()

    def set_all_visible(self, visible: bool) -> None:
        """Set visibility of the complete contact layer."""
        self.group.show = visible
        for view in self._views.values():
            view.scene_object.show = visible
        self._redraw()

    def select(self, keys: Iterable[ContactKey], clear: bool = True) -> None:
        """Set selection on contact-region scene objects."""
        requested = set(keys)
        for key, view in self._views.items():
            if clear:
                view.scene_object.is_selected = key in requested
            elif key in requested:
                view.scene_object.is_selected = True
        self._redraw()

    @property
    def selected_keys(self) -> tuple[ContactKey, ...]:
        """Keys of contact regions selected in the viewport."""
        return tuple(key for key, view in self._views.items() if view.scene_object.is_selected)

    def _build(self, show: bool) -> None:
        color = Color(0.9, 0.15, 0.1)
        for edge in self.controller.model.graph.edges():
            contacts = tuple(self.controller.model.graph.edge_attribute(edge, name="contacts") or ())
            if not contacts:
                continue
            u, v = edge
            elements = (self.controller.model.graph.node_element(u), self.controller.model.graph.node_element(v))
            for index, contact in enumerate(contacts):
                key = (u, v, index)
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
                self._views[key] = ContactView(key, elements, contact, scene_object)

    def _redraw(self) -> None:
        if getattr(self.controller.viewer, "running", False):
            self.controller.viewer.renderer.update()
