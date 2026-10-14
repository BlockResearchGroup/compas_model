from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

from compas_model.elements import Element
from compas_model.models import ElementNode
from compas_model.models import Model

from .compat import prepare_viewer_backend
from .elementobject import ElementObject
from .modelobject import ModelObject
from .viewstate import RenderGeometryCache
from .viewstate import RenderSettings


class ModelViewer:
    """Control the COMPAS Viewer representation of a model.

    Parameters
    ----------
    model
        Model to add to the viewer.
    viewer
        Existing COMPAS Viewer instance. If omitted, a viewer is created.
    settings
        Shared rendering settings. Implicit settings adopt the model unit.
    cache
        Shared render-geometry cache.
    install_tree
        If ``True``, replace COMPAS Viewer's generic scene tree with tabbed
        hierarchy, group, type, and interaction projections when the viewer
        provides a UI.
    install_inspector
        If ``True``, add the selected-element inspector to the viewer sidebar.
        show_contacts
            If ``True``, display computed contact regions. Every region remains
            independently selectable and can be hidden through the interaction
            view.

    Notes
    -----
    The model tree remains authoritative. This controller creates the matching
    COMPAS scene hierarchy and indexes the resulting ``ElementObject``
    instances; it does not create a second hierarchy or element-view layer.

    """

    def __init__(
        self,
        model: Model,
        viewer: Any | None = None,
        settings: RenderSettings | None = None,
        cache: RenderGeometryCache | None = None,
        install_tree: bool = True,
        install_inspector: bool = True,
        show_contacts: bool = True,
    ) -> None:
        if settings is not None and settings.unit != model.unit:
            raise ValueError("Render settings unit should match the model unit.")
        self.model = model
        self.settings = settings or RenderSettings(unit=model.unit)
        self._settings_explicit = settings is not None
        self.cache = cache if cache is not None else RenderGeometryCache()
        self.viewer = viewer or self._create_viewer()
        self.model_object = self._add_model_object()
        self._objects: dict[str, ElementObject] = {}
        self._build_element_objects()
        self.contact_layer = self._build_contact_layer(show=show_contacts)
        has_ui = hasattr(self.viewer, "ui")
        self.inspector = self._install_inspector() if install_inspector and has_ui else None
        self.tree_form = self._install_tree() if install_tree and has_ui else None

    def __len__(self) -> int:
        return len(self._objects)

    def __iter__(self) -> Iterator[ElementObject]:
        return iter(self._objects.values())

    @property
    def selected(self) -> list[ElementObject]:
        """list[ElementObject]: Selected element objects in model order."""
        return [scene_object for scene_object in self._objects.values() if scene_object.is_selected]

    def object_for_element(self, element: Element) -> ElementObject:
        """Return the scene object representing an element."""
        scene_object = self.object_for_guid(str(element.guid))
        if scene_object.element is not element:
            raise KeyError("The element GUID belongs to a different element instance.")
        return scene_object

    def object_for_guid(self, guid: str) -> ElementObject:
        """Return the scene object registered for an element GUID."""
        try:
            return self._objects[guid]
        except KeyError:
            raise KeyError(f"Unknown element GUID: {guid!r}.") from None

    def select(
        self,
        elements: Iterable[Element | str],
        selected: bool = True,
        clear: bool = False,
    ) -> None:
        """Set element selection state.

        Parameters
        ----------
        elements
            Elements or element GUIDs to update.
        selected
            Selection state assigned to the requested objects.
        clear
            If ``True``, clear selection on all other objects.

        """
        requested = self._resolve_guids(elements)
        for guid, scene_object in self._objects.items():
            if clear and guid not in requested:
                scene_object.is_selected = False
            elif guid in requested:
                scene_object.is_selected = selected
        self._redraw()

    def show(self, elements: Iterable[Element | str]) -> None:
        """Show the requested element objects."""
        self._set_visibility(elements, True)

    def hide(self, elements: Iterable[Element | str]) -> None:
        """Hide the requested element objects."""
        self._set_visibility(elements, False)

    def refresh(self, element: Element | str) -> bool:
        """Refresh one element object's render geometry.

        Returns
        -------
        bool
            ``True`` if the render geometry was replaced.

        """
        self._synchronize_model_unit()
        guid = self._resolve_guid(element)
        changed = self._objects[guid].refresh_render_geometry()
        if changed:
            self._redraw()
        return changed

    def refresh_all(self) -> list[ElementObject]:
        """Refresh all changed element objects.

        Returns
        -------
        list[ElementObject]
            Objects whose render geometry was replaced.

        """
        self._synchronize_model_unit()
        changed = [scene_object for scene_object in self._objects.values() if scene_object.refresh_render_geometry()]
        if changed:
            self._redraw()
        return changed

    def show_viewer(self) -> None:
        """Open the viewer window."""
        self.viewer.show()

    @staticmethod
    def _create_viewer() -> Any:
        prepare_viewer_backend()
        from compas_viewer import Viewer

        return Viewer()

    def _add_model_object(self) -> ModelObject:
        scene_object = self.viewer.scene.add(self.model, add_elements=False)
        if not isinstance(scene_object, ModelObject):
            raise TypeError("The Viewer scene did not create a compas_model ModelObject.")
        return scene_object

    def _build_element_objects(self) -> None:
        def add_nodes(nodes: list[ElementNode], parent: Any) -> None:
            for node in nodes:
                element = node.element
                guid = str(element.guid)
                if guid in self._objects:
                    raise ValueError(f"Duplicate element GUID in viewer model: {guid!r}.")
                scene_object = self.viewer.scene.add(
                    element,
                    parent=parent,
                    add_children=False,
                    render_cache=self.cache,
                    render_settings=self.settings,
                )
                if not isinstance(scene_object, ElementObject):
                    raise TypeError("The Viewer scene did not create a compas_model ElementObject.")
                self._objects[guid] = scene_object
                add_nodes(node.children, scene_object)

        add_nodes(self.model.tree.root.children, self.model_object)

    def _build_contact_layer(self, show: bool) -> Any | None:
        if not any(self.model.graph.edge_attribute(edge, name="contacts") for edge in self.model.graph.edges()):
            return None
        from .contactlayer import ContactLayer

        return ContactLayer(self, show=show)

    def _resolve_guid(self, element: Element | str) -> str:
        guid = str(element.guid) if isinstance(element, Element) else element
        if guid not in self._objects:
            raise KeyError(f"Unknown element GUID: {guid!r}.")
        if isinstance(element, Element) and self._objects[guid].element is not element:
            raise KeyError("The element GUID belongs to a different element instance.")
        return guid

    def _resolve_guids(self, elements: Iterable[Element | str]) -> set[str]:
        return {self._resolve_guid(element) for element in elements}

    def _set_visibility(self, elements: Iterable[Element | str], visible: bool) -> None:
        for guid in self._resolve_guids(elements):
            self._objects[guid].show = visible
        self._redraw()

    def _synchronize_model_unit(self) -> None:
        if self.settings.unit == self.model.unit:
            return
        if self._settings_explicit:
            raise ValueError("Render settings unit should match the model unit.")
        self.settings = replace(self.settings, unit=self.model.unit)
        for scene_object in self._objects.values():
            scene_object.render_settings = self.settings

    def _redraw(self) -> None:
        tree_form = getattr(self, "tree_form", None)
        if tree_form is not None:
            tree_form.update()
        inspector = getattr(self, "inspector", None)
        if inspector is not None:
            inspector.update()
        if getattr(self.viewer, "running", False):
            self.viewer.renderer.update()

    def _install_tree(self) -> Any:
        from .navigation import install_model_navigation

        return install_model_navigation(self)

    def _install_inspector(self) -> Any:
        from .inspector import install_element_inspector

        return install_element_inspector(self)
