from dataclasses import replace
from typing import Any
from typing import Optional

import numpy as np

from compas.colors import Color
from compas_model.elements import Group
from compas_model.models import Model
from compas_model.models import ModelUnit
from compas_model.scene.elementobject import ElementObject as BaseElementObject
from compas_model.viewer.rendergeometry import RenderGeometry
from compas_model.viewer.viewstate import RenderGeometryCache
from compas_model.viewer.viewstate import RenderSettings
from compas_viewer.scene import ViewerSceneObject
from compas_viewer.scene.sceneobject import ShaderDataType


class ElementObject(ViewerSceneObject, BaseElementObject):
    def __init__(
        self,
        render_geometry: RenderGeometry | None = None,
        render_cache: RenderGeometryCache | None = None,
        render_settings: RenderSettings | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._render_cache = render_cache if render_cache is not None else RenderGeometryCache()
        self._render_settings_explicit = render_settings is not None
        self.render_settings = render_settings or RenderSettings(unit=self._model_unit)

        if isinstance(self.element, Group):
            self.render_geometry = None
            return

        if render_geometry is not None:
            self.render_geometry = render_geometry
            return
        self._synchronize_model_unit()
        self.render_geometry = self._render_cache.get(self.element, self.render_settings)

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
        self._synchronize_model_unit()
        geometry = self._render_cache.get(self.element, self.render_settings)
        if geometry is self.render_geometry:
            return False
        self.render_geometry = geometry
        if self._inited:
            self.update(update_transform=False, update_data=True)
        return True

    def _synchronize_model_unit(self) -> None:
        unit = self._model_unit
        if self.render_settings.unit == unit:
            return
        if self._render_settings_explicit:
            raise ValueError("Render settings unit should match the model unit.")
        self.render_settings = replace(self.render_settings, unit=unit)

    def _read_points_data(self) -> Optional[ShaderDataType]:
        if self.render_geometry is not None:
            return _shader_data(self.render_geometry.point_vertices, _uniform_color(self.vertexcolor, Color.black()), 1)

    def _read_lines_data(self) -> Optional[ShaderDataType]:
        if self.render_geometry is not None:
            return _shader_data(self.render_geometry.line_vertices, _uniform_color(self.edgecolor, Color.black()), 2)

    def _read_frontfaces_data(self) -> Optional[ShaderDataType]:
        if self.render_geometry is not None:
            return _shader_data(self.render_geometry.face_vertices, _uniform_color(self.facecolor, Color.white()), 3)

    def _read_backfaces_data(self) -> Optional[ShaderDataType]:
        if self.render_geometry is not None:
            return _shader_data(self.render_geometry.backface_vertices, _uniform_color(self.facecolor, Color.white()), 3)


def _shader_data(positions: np.ndarray, color: Color, width: int) -> ShaderDataType:
    colors = [color] * len(positions)
    elements = np.arange(len(positions), dtype=int).reshape((-1, width)).tolist()
    return positions.tolist(), colors, elements  # type: ignore[return-value]


def _uniform_color(colors: Any, fallback: Color) -> Color:
    if colors is None:
        return fallback
    color = colors[None]
    return color if isinstance(color, Color) else fallback
