from collections.abc import Callable
from typing import Literal

from PySide6.QtCore import QSignalBlocker
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtWidgets import QTreeWidget
from PySide6.QtWidgets import QTreeWidgetItem

from compas_model.elements import Element
from compas_model.models import ElementNode
from compas_viewer.components.component import Component

from .controller import ModelViewer


class ModelTreeForm(Component):
    """Tree widget synchronized with a model viewer controller.

    Parameters
    ----------
    controller
        Controller providing model hierarchy and concrete scene objects.
    selection_changed
        Optional callback receiving the selected model elements.

    Notes
    -----
    Tree items retain only element GUIDs. ``Model.tree`` remains the source of
    hierarchy, and selection and visibility remain properties of the concrete
    ``ElementObject`` instances managed by the controller.

    """

    def __init__(
        self,
        controller: ModelViewer,
        selection_changed: Callable[[list[Element]], None] | None = None,
        projection: Literal["hierarchy", "types", "collections"] = "hierarchy",
    ) -> None:
        super().__init__()
        self.controller = controller
        self.selection_changed = selection_changed
        self.projection = projection
        self.widget = QTreeWidget()
        self.widget.setColumnCount(3)
        self.widget.setHeaderLabels(["Name", "Type", "Show"])
        self.widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._items: dict[str, list[QTreeWidgetItem]] = {}
        self._categories: list[QTreeWidgetItem] = []
        self._populate()
        self.widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.widget.itemChanged.connect(self._on_item_changed)

    def update(self, refresh: bool = False) -> None:
        """Synchronize tree selection and visibility from scene objects.

        Parameters
        ----------
        refresh
            If ``True``, rebuild items from the current model tree.

        """
        if refresh:
            self._populate()
        blocker = QSignalBlocker(self.widget)
        try:
            for guid, items in self._items.items():
                scene_object = self.controller.object_for_guid(guid)
                for item in items:
                    item.setSelected(scene_object.is_selected)
                    item.setCheckState(2, Qt.CheckState.Checked if scene_object.show else Qt.CheckState.Unchecked)
                    if scene_object.is_selected:
                        self._expand_ancestors(item)
            self._sync_category_states()
        finally:
            del blocker

    def item_for_element(self, element: Element) -> QTreeWidgetItem:
        """Return the tree item representing an element."""
        return self.item_for_guid(str(element.guid))

    def item_for_guid(self, guid: str) -> QTreeWidgetItem:
        """Return the tree item registered for an element GUID."""
        try:
            return self._items[guid][0]
        except KeyError:
            raise KeyError(f"Unknown element GUID: {guid!r}.") from None

    def _populate(self) -> None:
        blocker = QSignalBlocker(self.widget)
        try:
            self.widget.clear()
            self._items.clear()
            self._categories.clear()
            if self.projection == "hierarchy":
                for node in self.controller.model.tree.root.children:
                    self._add_node(node, None)
            elif self.projection == "types":
                self._populate_types()
            elif self.projection == "collections":
                self._populate_collections()
            else:
                raise ValueError(f"Unknown model-tree projection: {self.projection!r}.")
            self._sync_category_states()
            self.widget.resizeColumnToContents(0)
            self.widget.resizeColumnToContents(1)
            self.widget.resizeColumnToContents(2)
        finally:
            del blocker

    def _add_node(self, node: ElementNode, parent: QTreeWidgetItem | None) -> None:
        element = node.element
        guid = str(element.guid)
        name = element.name or element.__class__.__name__
        item = QTreeWidgetItem([name, element.__class__.__name__, ""])
        item.setData(0, Qt.ItemDataRole.UserRole, guid)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(2, Qt.CheckState.Checked if self.controller.object_for_guid(guid).show else Qt.CheckState.Unchecked)
        if parent is None:
            self.widget.addTopLevelItem(item)
        else:
            parent.addChild(item)
        self._items.setdefault(guid, []).append(item)
        for child in node.children:
            self._add_node(child, item)

    def _populate_types(self) -> None:
        elements = sorted(self.controller.model.elements(), key=lambda element: (element.__class__.__name__, element.name or "", str(element.guid)))
        categories: dict[str, QTreeWidgetItem] = {}
        for element in elements:
            typename = element.__class__.__name__
            parent = categories.get(typename)
            if parent is None:
                parent = self._add_category(typename)
                categories[typename] = parent
            self._add_element(element, parent)

    def _populate_collections(self) -> None:
        collected: set[str] = set()
        for collection in self.controller.model.collections():
            parent = self._add_category(collection.name or "Collection")
            for element in collection.elements():
                self._add_element(element, parent)
                collected.add(str(element.guid))
        uncollected = [element for element in self.controller.model.elements() if str(element.guid) not in collected]
        if uncollected:
            parent = self._add_category("Uncollected")
            for element in uncollected:
                self._add_element(element, parent)

    def _add_category(self, name: str) -> QTreeWidgetItem:
        item = QTreeWidgetItem([name, "", ""])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.widget.addTopLevelItem(item)
        self._categories.append(item)
        return item

    def _add_element(self, element: Element, parent: QTreeWidgetItem) -> None:
        guid = str(element.guid)
        item = QTreeWidgetItem([element.name or element.__class__.__name__, element.__class__.__name__, ""])
        item.setData(0, Qt.ItemDataRole.UserRole, guid)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(2, Qt.CheckState.Checked if self.controller.object_for_guid(guid).show else Qt.CheckState.Unchecked)
        parent.addChild(item)
        self._items.setdefault(guid, []).append(item)

    def _on_selection_changed(self) -> None:
        guids = list(dict.fromkeys(guid for item in self.widget.selectedItems() for guid in self._subtree_guids(item)))
        self.controller.select(guids, clear=True)
        if self.selection_changed:
            self.selection_changed([self.controller.object_for_guid(guid).element for guid in guids])

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 2:
            return
        visible = item.checkState(2) == Qt.CheckState.Checked
        guids = self._subtree_guids(item)
        if visible:
            self.controller.show(guids)
        else:
            self.controller.hide(guids)
        self.update()

    def _subtree_guids(self, item: QTreeWidgetItem) -> list[str]:
        guid = item.data(0, Qt.ItemDataRole.UserRole)
        guids = [] if guid is None else [str(guid)]
        for index in range(item.childCount()):
            child = item.child(index)
            if child is not None:
                guids.extend(self._subtree_guids(child))
        return guids

    def _sync_category_states(self) -> None:
        for item in self._categories:
            states = [self.controller.object_for_guid(guid).show for guid in self._subtree_guids(item)]
            if states and all(states):
                state = Qt.CheckState.Checked
            elif any(states):
                state = Qt.CheckState.PartiallyChecked
            else:
                state = Qt.CheckState.Unchecked
            item.setCheckState(2, state)

    @staticmethod
    def _expand_ancestors(item: QTreeWidgetItem) -> None:
        parent = item.parent()
        while parent is not None:
            parent.setExpanded(True)
            parent = parent.parent()


def install_model_tree(
    controller: ModelViewer,
    selection_changed: Callable[[list[Element]], None] | None = None,
) -> ModelTreeForm:
    """Replace COMPAS Viewer's generic scene tree with a model tree.

    Parameters
    ----------
    controller
        Model viewer controller whose viewer UI should be updated.

    Returns
    -------
    ModelTreeForm
        Installed model hierarchy form.

    """
    sidebar = controller.viewer.ui.sidebar
    previous = sidebar.sceneform
    tree = ModelTreeForm(controller, selection_changed=selection_changed)
    index = sidebar.children.index(previous)
    sidebar.remove(previous)
    sidebar.children.insert(index, tree)
    sidebar.widget.insertWidget(index, tree.widget)
    sidebar.sceneform = tree
    return tree
