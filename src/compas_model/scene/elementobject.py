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
    element : :class:`compas_model.elements.Element`
        A COMPAS element.

    Attributes
    ----------
    element : :class:`compas_model.elements.Element`
        The element.
    color : :class:`compas.colors.Color`
        The base RGB color of the element.
    vertexcolor : :class:`compas.colors.ColorDict`
        Vertex colors.
    edgecolor : :class:`compas.colors.ColorDict`
        Edge colors.
    facecolor : :class:`compas.colors.ColorDict`
        Face colors.
    vertexsize : float
        The size of the vertices. Default is ``1.0``.
    edgewidth : float
        The width of the edges. Default is ``1.0``.
    show_vertices : Union[bool, sequence[float]]
        Flag for showing or hiding the vertices, or a list of keys for the vertices to show.
        Default is ``False``.
    show_edges : Union[bool, sequence[tuple[int, int]]]
        Flag for showing or hiding the edges, or a list of keys for the edges to show.
        Default is ``True``.
    show_faces : Union[bool, sequence[int]]
        Flag for showing or hiding the faces, or a list of keys for the faces to show.
        Default is ``True``.

    See Also
    --------
    :class:`compas.scene.GraphObject`
    :class:`compas.scene.VolElementObject`

    """

    vertexcolor = ColorDictAttribute()
    edgecolor = ColorDictAttribute()
    facecolor = ColorDictAttribute()

    def __init__(
        self,
        element: Element,
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
        super().__init__(item=element, **kwargs)

        self._element = element

        self.vertexcolor = vertexcolor
        self.edgecolor = edgecolor
        self.facecolor = facecolor

        self.vertexsize = vertexsize
        self.edgewidth = edgewidth

        self.show_vertices = show_vertices
        self.show_edges = show_edges
        self.show_faces = show_faces

    @property
    def element(self) -> Element:
        return self._element

    @element.setter
    def element(self, element: Element) -> None:
        self._element = element
        self._transformation = None

    @property
    def transformation(self) -> Transformation:
        return self._transformation

    @transformation.setter
    def transformation(self, transformation: Transformation) -> None:
        self._transformation = transformation

    def draw(self):
        """draw the element.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def clear(self):
        """Clear all components of the element.

        Returns
        -------
        None

        """
        raise NotImplementedError
