from collections.abc import Mapping
from typing import Any
from typing import cast

from compas.colors import Color
from compas.colors import ColorDict
from compas.colors.color import ColorInput
from compas.scene import SceneObject
from compas.scene import SceneStateField
from compas.scene.descriptors.colordict import ColorDictAttribute
from compas_model.elements import Element

type _ColorSpec = Mapping[Any, ColorInput] | Color | ColorDict | None


class ElementObject(SceneObject):
    """Represent an element and its presentation in a scene.

    Parameters
    ----------
    vertexcolor
        Vertex colors.
    edgecolor
        Edge colors.
    facecolor
        Face colors.
    vertexsize
        The size of the vertices.
    edgewidth
        The width of the edges.
    show_vertices
        Flag for showing or hiding the vertices.
    show_edges
        Flag for showing or hiding the edges.
    show_faces
        Flag for showing or hiding the faces.
    pointcolor, linecolor, surfacecolor, pointsize, linewidth, show_points, show_lines, show_surfaces
        Presentation options passed by Viewer when adding an element.
    **kwargs
        Additional keyword arguments for the base scene object.

    """

    vertexcolor = ColorDictAttribute(default=Color.black())
    edgecolor = ColorDictAttribute(default=Color.black())
    facecolor = ColorDictAttribute(default=Color.white())
    __scene_state_namespace__ = "compas_model.scene.ElementObject"
    __scene_state_fields__ = (
        SceneStateField("vertexcolor", ColorDict, required=False),
        SceneStateField("edgecolor", ColorDict, required=False),
        SceneStateField("facecolor", ColorDict, required=False),
        SceneStateField("vertexsize", (int, float), default=1.0, required=False),
        SceneStateField("edgewidth", (int, float), default=1.0, required=False),
        SceneStateField("show_vertices", bool, default=False, required=False),
        SceneStateField("show_edges", bool, default=True, required=False),
        SceneStateField("show_faces", bool, default=True, required=False),
    )

    def __init__(
        self,
        vertexcolor: _ColorSpec = None,
        edgecolor: _ColorSpec = None,
        facecolor: _ColorSpec = None,
        vertexsize: float = 1.0,
        edgewidth: float = 1.0,
        show_vertices: bool = False,
        show_edges: bool = True,
        show_faces: bool = True,
        *,
        pointcolor: _ColorSpec = None,
        linecolor: _ColorSpec = None,
        surfacecolor: _ColorSpec = None,
        pointsize: float | None = None,
        linewidth: float | None = None,
        show_points: bool | None = None,
        show_lines: bool | None = None,
        show_surfaces: bool | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.vertexcolor = vertexcolor if vertexcolor is not None else pointcolor
        self.edgecolor = edgecolor if edgecolor is not None else linecolor
        self.facecolor = facecolor if facecolor is not None else surfacecolor
        self.vertexsize = vertexsize if pointsize is None else pointsize
        self.edgewidth = edgewidth if linewidth is None else linewidth
        self.show_vertices = show_vertices if show_points is None else show_points
        self.show_edges = show_edges if show_lines is None else show_lines
        self.show_faces = show_faces if show_surfaces is None else show_surfaces

    @property
    def element(self) -> Element:
        """Element: The represented element."""
        return cast(Element, self.item)
