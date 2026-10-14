from typing import Any
from typing import cast

from compas_viewer.components.tabform import Tabform

from .controller import ModelViewer
from .interactionform import InteractionTreeForm
from .treeform import ModelTreeForm


class ModelNavigationForm(Tabform):
    """Tabbed read-only projections of model and interaction data."""

    def __init__(self, controller: ModelViewer) -> None:
        super().__init__(tab_position="top")
        self.controller = controller
        callback = None if controller.inspector is None else controller.inspector.inspect
        interaction_callback = None if controller.inspector is None else controller.inspector.inspect_contact
        self.hierarchy = ModelTreeForm(controller, selection_changed=callback)
        self.collections = ModelTreeForm(controller, selection_changed=callback, projection="collections")
        self.types = ModelTreeForm(controller, selection_changed=callback, projection="types")
        self.interactions = InteractionTreeForm(controller, selection_changed=interaction_callback)
        self.add_tab("Hierarchy", container=cast(Any, self.hierarchy))
        self.add_tab("Collections", container=cast(Any, self.collections))
        self.add_tab("Types", container=cast(Any, self.types))
        self.add_tab("Interactions", container=cast(Any, self.interactions))

    def update(self, refresh: bool = False) -> None:
        """Synchronize every projection with controller state."""
        self.hierarchy.update(refresh=refresh)
        self.collections.update(refresh=refresh)
        self.types.update(refresh=refresh)
        self.interactions.update(refresh=refresh)


def install_model_navigation(controller: ModelViewer) -> ModelNavigationForm:
    """Replace COMPAS Viewer's scene form with model navigation tabs."""
    sidebar: Any = controller.viewer.ui.sidebar
    previous = sidebar.sceneform
    navigation = ModelNavigationForm(controller)
    index = sidebar.children.index(previous)
    sidebar.remove(previous)
    sidebar.children.insert(index, navigation)
    sidebar.widget.insertWidget(index, navigation.widget)
    sidebar.sceneform = navigation
    return navigation
