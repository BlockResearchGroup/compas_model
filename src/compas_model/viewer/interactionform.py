from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from PySide6.QtCore import QSignalBlocker
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QTreeWidget
from PySide6.QtWidgets import QTreeWidgetItem

from compas_model.elements import Element
from compas_model.interactions import Contact
from compas_viewer.components.component import Component

from .controller import ModelViewer


@dataclass(frozen=True, slots=True)
class InteractionSelection:
    """Selection of an interaction pair or some of its payload objects."""

    edge: tuple[str, str]
    elements: tuple[Element, Element]
    contacts: tuple[Contact, ...]
    modifiers: tuple[object, ...] = ()


ContactSelection = InteractionSelection


class InteractionTreeForm(Component):
    """Tree projection of model interaction edges and their payloads."""

    def __init__(
        self,
        controller: ModelViewer,
        selection_changed: Callable[[InteractionSelection | None], None] | None = None,
    ) -> None:
        super().__init__()
        self.controller = controller
        self.selection_changed = selection_changed
        self.widget = QTreeWidget()
        self.widget.setColumnCount(4)
        self.widget.setHeaderLabels(["Interaction", "Kind", "Area", "Show"])
        self.widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._records: dict[tuple[str, str], tuple[Element, Element, tuple[Contact, ...], tuple[object, ...]]] = {}
        self._contact_items: dict[str, QTreeWidgetItem] = {}
        self._pair_items: dict[tuple[str, str], QTreeWidgetItem] = {}
        self._root_item: QTreeWidgetItem | None = None
        self._populate()
        self.widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.widget.itemChanged.connect(self._on_item_changed)

    def update(self, refresh: bool = False) -> None:
        """Synchronize contact selection and visibility with the scene."""
        if refresh:
            self._populate()
        layer = self.controller.contact_layer
        if layer is None:
            return
        blocker = QSignalBlocker(self.widget)
        try:
            if self._root_item is not None:
                self._root_item.setCheckState(3, Qt.CheckState.Checked if layer.group.show else Qt.CheckState.Unchecked)
            selected = set(layer.selected_keys)
            for key, item in self._contact_items.items():
                view = layer.view(key)
                item.setCheckState(3, Qt.CheckState.Checked if view.scene_object.show else Qt.CheckState.Unchecked)
                item.setSelected(key in selected)
            for edge, item in self._pair_items.items():
                states = [layer.view(key).scene_object.show for key in layer.keys_for_edge(edge)]
                item.setCheckState(3, _aggregate_check_state(states))
        finally:
            del blocker
        if selected:
            self._report_contact_keys(selected)

    def _populate(self) -> None:
        blocker = QSignalBlocker(self.widget)
        try:
            self.widget.clear()
            self._records.clear()
            self._contact_items.clear()
            self._pair_items.clear()
            root_item = QTreeWidgetItem(["All interactions", "", "", ""])
            root_item.setFlags(root_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            if self.controller.contact_layer is not None:
                root_item.setFlags(root_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                root_item.setCheckState(3, Qt.CheckState.Checked if self.controller.contact_layer.group.show else Qt.CheckState.Unchecked)
            self._root_item = root_item
            self.widget.addTopLevelItem(root_item)

            for edge in self.controller.model.graph.edges():
                edge = cast(tuple[str, str], edge)
                u, v = edge
                a = self.controller.model.element_by_guid(u)
                b = self.controller.model.element_by_guid(v)
                contacts = tuple(contact for record in self.controller.model.contact_records_between(a, b) for contact in record.contacts)
                modifiers = tuple(record.modifier for record in self.controller.model.modifier_records_between(a, b))
                self._records[u, v] = (a, b, contacts, modifiers)
                kinds = (["Contact"] if contacts else []) + (["Modifier"] if modifiers else [])
                pair = QTreeWidgetItem(
                    [f"{_element_name(a)} ↔ {_element_name(b)}", " + ".join(kinds) or "Interaction", _format_area(sum(contact.size for contact in contacts)), ""]
                )
                pair.setData(0, Qt.ItemDataRole.UserRole, (u, v, "pair", -1))
                if contacts:
                    pair.setFlags(pair.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    pair.setCheckState(3, Qt.CheckState.Checked)
                root_item.addChild(pair)
                self._pair_items[u, v] = pair

                for index, contact in enumerate(contacts):
                    key = str(contact.guid)
                    region = QTreeWidgetItem([f"Region {index + 1}", "Planar region", _format_area(contact.size), ""])
                    region.setData(0, Qt.ItemDataRole.UserRole, (u, v, "contact", key))
                    region.setFlags(region.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    region.setCheckState(3, Qt.CheckState.Checked)
                    pair.addChild(region)
                    self._contact_items[key] = region

                for index, modifier in enumerate(modifiers):
                    item = QTreeWidgetItem([getattr(modifier, "name", None) or modifier.__class__.__name__, "Modifier", "", ""])
                    item.setData(0, Qt.ItemDataRole.UserRole, (u, v, "modifier", index))
                    pair.addChild(item)

            for column in range(4):
                self.widget.resizeColumnToContents(column)
        finally:
            del blocker

    def _on_selection_changed(self) -> None:
        items = self.widget.selectedItems()
        if not items:
            if self.selection_changed:
                self.selection_changed(None)
            return
        first = items[0].data(0, Qt.ItemDataRole.UserRole)
        if first is None:
            return
        u, v, _, _ = first
        a, b, all_contacts, all_modifiers = self._records[u, v]
        contact_keys = {data[3] for item in items if (data := item.data(0, Qt.ItemDataRole.UserRole)) is not None and data[:2] == (u, v) and data[2] == "contact"}
        modifier_indices = {data[3] for item in items if (data := item.data(0, Qt.ItemDataRole.UserRole)) is not None and data[:2] == (u, v) and data[2] == "modifier"}
        pair_selected = any(item.data(0, Qt.ItemDataRole.UserRole)[2] == "pair" for item in items)
        contacts: tuple[Contact, ...] = all_contacts if pair_selected else tuple(contact for contact in all_contacts if str(contact.guid) in contact_keys)
        modifiers: tuple[object, ...] = all_modifiers if pair_selected else tuple(all_modifiers[index] for index in sorted(modifier_indices))
        layer = self.controller.contact_layer
        if layer is not None:
            keys = layer.keys_for_edge((u, v)) if pair_selected else tuple(contact_keys)
            layer.select(keys, clear=True)
        # A contact region is an independently selectable scene object. Only
        # pair and modifier selections imply selection of their endpoint
        # elements; selecting a region should not highlight those elements.
        elements = [a, b] if pair_selected or modifier_indices else []
        self.controller.select(elements, clear=True)
        if self.selection_changed:
            self.selection_changed(InteractionSelection((u, v), (a, b), contacts, modifiers))

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        layer = self.controller.contact_layer
        if column != 3 or layer is None:
            return
        visible = item.checkState(3) == Qt.CheckState.Checked
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data is None:
            layer.set_all_visible(visible)
        elif data[2] == "pair":
            layer.set_visibility(layer.keys_for_edge(data[:2]), visible)
        elif data[2] == "contact":
            layer.set_visibility([data[3]], visible)
        self.update()

    def _report_contact_keys(self, keys: set[str]) -> None:
        layer = self.controller.contact_layer
        if layer is None:
            return
        views = [layer.view(key) for key in sorted(keys)]
        u, v = views[0].edge
        a, b = views[0].elements
        if self.selection_changed:
            self.selection_changed(InteractionSelection((u, v), (a, b), tuple(view.contact for view in views)))


def _element_name(element: Element) -> str:
    return element.name or element.__class__.__name__


def _format_area(area: float) -> str:
    return f"{area:.6g}"


def _aggregate_check_state(states: list[bool]) -> Qt.CheckState:
    if states and all(states):
        return Qt.CheckState.Checked
    if any(states):
        return Qt.CheckState.PartiallyChecked
    return Qt.CheckState.Unchecked
