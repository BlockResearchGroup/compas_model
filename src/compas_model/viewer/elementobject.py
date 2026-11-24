from dataclasses import dataclass
from typing import cast
from weakref import WeakKeyDictionary

import numpy as np
from numpy.typing import NDArray

from compas.colors import Color
from compas.colors import ColorDict
from compas.scene import Scene
from compas_model.elements import Element
from compas_model.elements import Group
from compas_model.models import Model
from compas_model.models import ModelUnit
from compas_model.scene.elementobject import ElementObject as StableElementObject
from compas_model.viewer.rendergeometry import RenderGeometry
from compas_model.viewer.viewstate import RenderGeometryCache
from compas_model.viewer.viewstate import RenderSettings
from compas_viewer.scene import ViewerScene
from compas_viewer.scene.runtime import clear
from compas_viewer.scene.sceneobject import ShaderDataType
from compas_viewer.scene.sceneobject import ViewerSceneObject


@dataclass(slots=True)
class _ElementRendering:
    cache: RenderGeometryCache
    settings: RenderSettings | None = None


# Buffer rebuilds replace the Viewer helpers while retaining the scene objects.
_RENDERING: WeakKeyDictionary[StableElementObject, _ElementRendering] = WeakKeyDictionary()


def _rendering_for(sceneobject: StableElementObject) -> _ElementRendering:
    rendering = _RENDERING.get(sceneobject)
    if rendering is None:
        rendering = _ElementRendering(RenderGeometryCache())
        _RENDERING[sceneobject] = rendering
    return rendering


def configure_element_rendering(sceneobject: StableElementObject, cache: RenderGeometryCache, settings: RenderSettings) -> None:
    """Share the controller's rendering configuration across buffer rebuilds."""
    rendering = _rendering_for(sceneobject)
    rendering.cache = cache
    rendering.settings = settings


def draw_element(scene: Scene, target: StableElementObject, runtime: object | None) -> list[object]:
    """Prepare transient Viewer render state for an element."""
    viewer_scene = getattr(runtime, "scene", runtime)
    if not isinstance(viewer_scene, ViewerScene):
        raise TypeError("Viewer draw operations require a Viewer or ViewerScene runtime.")
    viewer_scene.render_objects[target.guid] = ElementObject(target, runtime)
    return []


def clear_element(scene: Scene, target: StableElementObject, runtime: object | None, resources: tuple[object, ...]) -> None:
    """Release the element's transient state through Viewer."""
    clear(scene, target, runtime, resources)


class ElementObject(ViewerSceneObject):
    """Render one stable Model element in a Viewer scene."""

    sceneobject: StableElementObject

    def __init__(
        self,
        sceneobject: StableElementObject,
        runtime: object,
        *,
        render_geometry: RenderGeometry | None = None,
        render_cache: RenderGeometryCache | None = None,
        render_settings: RenderSettings | None = None,
    ) -> None:
        super().__init__(sceneobject, runtime)
        rendering = _rendering_for(sceneobject)
        cache = rendering.cache if render_cache is None else render_cache
        settings = rendering.settings if render_settings is None else render_settings
        if isinstance(self.element, Group):
            self.render_geometry: RenderGeometry | None = None
        elif render_geometry is not None:
            self.render_geometry = render_geometry
        else:
            self.render_geometry = self._current_render_geometry(cache, settings)
        rendering.cache = cache
        rendering.settings = settings
        self._rendering = rendering

    @property
    def element(self) -> Element:
        """Element: The represented element."""
        return self.sceneobject.element

    @property
    def render_settings(self) -> RenderSettings:
        """RenderSettings: Effective settings for the current model unit."""
        return self._rendering.settings or RenderSettings(unit=self._model_unit)

    @render_settings.setter
    def render_settings(self, settings: RenderSettings) -> None:
        self._rendering.settings = settings

    @property
    def show_points(self) -> bool:
        """bool: Whether element vertices are visible."""
        return self.sceneobject.show_vertices

    @property
    def show_lines(self) -> bool:
        """bool: Whether element edges are visible."""
        return self.sceneobject.show_edges

    @property
    def show_faces(self) -> bool:
        """bool: Whether element faces are visible."""
        return self.sceneobject.show_faces

    @show_faces.setter
    def show_faces(self, show: bool) -> None:
        self.sceneobject.show_faces = show

    @property
    def pointsize(self) -> float:
        """float: Display size of element vertices."""
        return self.sceneobject.vertexsize

    @property
    def linewidth(self) -> float:
        """float: Display width of element edges."""
        return self.sceneobject.edgewidth

    @property
    def _model_unit(self) -> ModelUnit:
        model = getattr(self.element, "model", None)
        return model.unit if isinstance(model, Model) else "M"

    def refresh_render_geometry(self) -> bool:
        """Refresh cached render geometry after an element geometry change.

        Returns
        -------
        bool
            ``True`` if the render geometry was replaced.

        """
        if isinstance(self.element, Group):
            return False
        geometry = self._current_render_geometry(self._rendering.cache, self._rendering.settings)
        if geometry is self.render_geometry:
            return False
        self.render_geometry = geometry
        return True

    def _current_render_geometry(self, cache: RenderGeometryCache, settings: RenderSettings | None) -> RenderGeometry:
        unit = self._model_unit
        if settings is None:
            settings = RenderSettings(unit=unit)
        elif settings.unit != unit:
            raise ValueError("Render settings unit should match the model unit.")
        return cache.get(self.element, settings)

    def _read_points_data(self) -> ShaderDataType | None:
        if self.render_geometry is not None:
            return _shader_data(self.render_geometry.point_vertices, cast(ColorDict, self.sceneobject.vertexcolor)[None], 1)
        return None

    def _read_lines_data(self) -> ShaderDataType | None:
        if self.render_geometry is not None:
            return _shader_data(self.render_geometry.line_vertices, cast(ColorDict, self.sceneobject.edgecolor)[None], 2)
        return None

    def _read_frontfaces_data(self) -> ShaderDataType | None:
        if self.render_geometry is not None:
            return _shader_data(self.render_geometry.face_vertices, cast(ColorDict, self.sceneobject.facecolor)[None], 3)
        return None

    def _read_backfaces_data(self) -> ShaderDataType | None:
        if self.render_geometry is not None:
            return _shader_data(self.render_geometry.backface_vertices, cast(ColorDict, self.sceneobject.facecolor)[None], 3)
        return None


def _shader_data(positions: NDArray[np.float64], color: Color, width: int) -> ShaderDataType:
    colors = [color] * len(positions)
    elements = np.arange(len(positions), dtype=int).reshape((-1, width)).tolist()
    return positions.tolist(), colors, elements
