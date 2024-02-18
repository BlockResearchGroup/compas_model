from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from compas_model.model import ElementNode  # noqa: F401

from abc import abstractmethod

import compas.geometry
import compas.datastructures  # noqa: F401

from compas.data import Data
from compas.geometry import Frame


class Element(Data):
    """Base class for all elements in the model.

    Parameters
    ----------
    geometry : Union[Geometry, Mesh]
        The geometry of the element.
    frame : None, default WorldXY
        The frame of the element.
    name : None
        The name of the element.

    Attributes
    ----------
    guid : uuid
        The unique identifier of the element.
    geometry : Union[Geometry, Mesh]
        The geometry of the element.
    frame : :class:`compas.geometry.Frame`
        The frame of the element.
    name : str
        The name of the element.
    graph_node : :class:`compas.datastructures.GraphNode`
        The graph node of the element.
    tree_node : :class:`compas.datastructures.TreeNode`
        The tree node of the element.
    dimensions : list
        The dimensions of the element.
    aabb : :class:`compas.geometry.Box`
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`
        The collision geometry of the element.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"geometry": self.geometry, "frame": self.frame, "name": self.name}

    def __init__(self, geometry=None, frame=None, name=None):
        # type: (compas.geometry.Geometry | compas.datastructures.Mesh | None, Frame | None, str | None) -> None
        super(Element, self).__init__(name=name)
        self.geometry = geometry
        self.frame = frame if frame else Frame.worldXY()
        self.graph_node = None  # type: int | None
        self.tree_node = None  # type: ElementNode | None
        self._dimensions = []
        self._aabb = None
        self._obb = None
        self._collision_mesh = None

    def __str__(self):
        return "<Element with geometry {}>".format(self.geometry.__class__.__name__)

    @property
    def dimensions(self):
        # type: () -> tuple[float, float, float]
        return self.obb.width, self.obb.height, self.obb.depth

    @property
    def aabb(self):
        # type: () -> compas.geometry.Box
        if not self._aabb:
            self._aabb = self.compute_aabb()
        return self._aabb

    @property
    def obb(self):
        # type: () -> compas.geometry.Box
        if not self._obb:
            self._obb = self.compute_obb()
        return self._obb

    @property
    def collision_mesh(self):
        # type: () -> compas.datastructures.Mesh
        if not self._collision_mesh:
            self._collision_mesh = self.compute_collision_mesh()
        return self._collision_mesh

    @abstractmethod
    def compute_aabb(self, inflate=0.0):
        # type: (float | None) -> compas.geometry.Box
        """Computes the Axis Aligned Bounding Box (AABB) of the element.

        Parameters
        ----------
        inflate : float, optional
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """
        raise NotImplementedError

    @abstractmethod
    def compute_obb(self, inflate=0.0):
        # type: (float | None) -> compas.geometry.Box
        """Computes the Oriented Bounding Box (OBB) of the element.

        Parameters
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """
        raise NotImplementedError

    @abstractmethod
    def compute_collision_mesh(self):
        # type: () -> compas.datastructures.Mesh
        """Computes the collision geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """
        raise NotImplementedError

    @abstractmethod
    def transform(self, transformation):
        # type: (compas.geometry.Transformation) -> None
        """Transforms all the attrbutes of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to be applied to the Element's geometry and frames.

        Returns
        -------
        None

        """
        raise NotImplementedError

    # ==========================================================================
    # Public methods
    # ==========================================================================

    def transformed(self, transformation):
        # type: (compas.geometry.Transformation) -> Element
        """Creates a transformed copy of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`:
            The transformation to be applied to the copy of an element.

        Returns
        -------
        :class:`compas_model.elements.Element`
            A new instance of the Element with the specified transformation applied.

        """
        new_instance = self.copy()
        new_instance.transform(transformation)
        return new_instance
