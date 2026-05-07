from typing import Optional

from compas.colors import Color
from compas.geometry import Transformation
from compas.scene import SceneObject
from compas.scene.descriptors.colordict import ColorDictAttribute
from compas_model.elements import Element


class ElementObject(SceneObject):
    """Base class for all element scene objects.

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
    **kwargs
        Additional keyword arguments for the base scene object.

    """

    vertexcolor = ColorDictAttribute()
    edgecolor = ColorDictAttribute()
    facecolor = ColorDictAttribute()

    def __init__(
        self,
        vertexcolor: Optional[Color] = Color.black(),
        edgecolor: Optional[Color] = Color.black(),
        facecolor: Optional[Color] = Color.white(),
        vertexsize: Optional[float] = 1.0,
        edgewidth: Optional[float] = 1.0,
        show_vertices: Optional[bool] = False,
        show_edges: Optional[bool] = True,
        show_faces: Optional[bool] = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.vertexcolor = vertexcolor
        self.edgecolor = edgecolor
        self.facecolor = facecolor

        self.vertexsize = vertexsize
        self.edgewidth = edgewidth

        self.show_vertices = show_vertices
        self.show_edges = show_edges
        self.show_faces = show_faces

        for child in self.element.children:
            child_kwargs = kwargs.copy()
            child_kwargs["item"] = child
            self.add(**child_kwargs)

    @property
    def element(self) -> Element:
        return self.item  # type: ignore

    @property
    def transformation(self) -> Transformation:
        return self._transformation

    @transformation.setter
    def transformation(self, transformation: Transformation) -> None:
        self._transformation = transformation

    def draw(self) -> None:
        """Draw the element."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all components of the element."""
        raise NotImplementedError
