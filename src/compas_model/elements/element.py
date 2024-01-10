from __future__ import print_function
from __future__ import absolute_import
from __future__ import division


from compas.data import Data
from compas.geometry import (
    Frame,
    Vector,
)


class Element(Data):
    """Class representing a structural object.

    Parameters
    ----------
    name : str, optional
        Name of the element
    frame : :class:`compas.geometry.Frame`, optional
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`. There is also a global frame stored as an attribute.
    geometry_simplified : Any, optional
        Minimal geometrical represetation of an object. For example a :class:`compas.geometry.Polyline` that can represent: a point, a line or a polyline.
    geometry : Any, optional
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    copy_geometry : bool, optional
        If True, the geometry will be copied to avoid references.
    kwargs (dict, optional):
        Additional keyword arguments.

    Examples
    --------
    >>> frame = Frame([3, 0, 0], [0.866, 0.1, 0.0], [0.5, 0.866, 0.0])
    >>> box = Box(frame=frame, xsize=2, ysize=4, zsize=0.25)
    >>> element = Element("BLOCK", Frame.worldXY(), Point(0,0,0), box)
    >>> element.insertion = Vector(0, 0, 1)

    """

    def __init__(
        self,
        name=None,
        frame=None,
        geometry_simplified=None,
        geometry=None,
        copy_geometry=True,
        **kwargs
    ):
        # --------------------------------------------------------------------------
        # Call the inherited Data constructor.
        # --------------------------------------------------------------------------
        super(Element, self).__init__(**kwargs)

        # --------------------------------------------------------------------------
        # Set the element name.
        # --------------------------------------------------------------------------
        self.name = name.lower() if name else "unknown"

        # --------------------------------------------------------------------------
        # Set the base frame of the element.
        # --------------------------------------------------------------------------
        self.frame = frame.copy() if frame else Frame.worldXY()

        # --------------------------------------------------------------------------
        # Copy geometries to avoid transformation issues.
        # --------------------------------------------------------------------------
        self.geometry_simplified = []
        self.geometry = []
        if geometry_simplified:
            self.copy_geometry = copy_geometry
            self.geometry_simplified = self._copy_geometries(
                geometry_simplified, copy_geometry
            )

        if geometry:
            self.geometry = self._copy_geometries(geometry, copy_geometry)

        # --------------------------------------------------------------------------
        # Define this property dynamically in the class.
        # --------------------------------------------------------------------------
        self._aabb = None
        self._oobb = None
        self._inflate = 0.0
        self._id = -1
        self._insertion = Vector(0, 0, 1)

    def __repr__(self):
        return """{0} {1}""".format(self.name, self.guid)

    def __str__(self):
        return self.__repr__()
