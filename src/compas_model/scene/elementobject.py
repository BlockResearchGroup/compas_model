import compas.geometry  # noqa: F401
import compas_model.elements  # noqa: F401
from compas.colors import Color
from compas.scene import SceneObject
from compas.scene.descriptors.colordict import ColorDictAttribute


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

    def __init__(self, element, **kwargs):
        # type: (compas_model.elements.Element, dict) -> None
        super(ElementObject, self).__init__(item=element, **kwargs)

        self._element = element
        self.vertexcolor = kwargs.get("vertexcolor", Color.black())
        self.edgecolor = kwargs.get("edgecolor", Color.black())
        self.facecolor = kwargs.get("facecolor", Color.white())
        self.vertexsize = kwargs.get("vertexsize", 1.0)
        self.edgewidth = kwargs.get("edgewidth", 1.0)
        self.show_vertices = kwargs.get("show_vertices", False)
        self.show_edges = kwargs.get("show_edges", True)
        self.show_faces = kwargs.get("show_faces", True)

    @property
    def element(self):
        # type: () -> compas_model.elements.Element
        return self._element

    @element.setter
    def element(self, element):
        self._element = element
        self._transformation = None

    @property
    def transformation(self):
        # type: () -> compas.geometry.Transformation | None
        return self._transformation

    @transformation.setter
    def transformation(self, transformation):
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
