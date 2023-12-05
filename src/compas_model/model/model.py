from collections import OrderedDict
from compas.datastructures import Graph
from compas_model.model.element_tree import ElementTree
from compas.data import Data


class Model(Data):
    """model represents:\n
    a dictionary of elements, where the key is the element.guid\n
    a tree to represent the assembly hierarchy\n
    a graph to represent the connectivity of the elements\n

    Parameters
    ----------
    name : str, optional
        A name or identifier for the model.

    elements : list, optional
        A list of elements to be added to the model.

    copy_elements : bool, optional
        If True, the elements are copied before adding to the model.

    """

    def __init__(self, name="model", elements=[], copy_elements=False):
        super(Model, self).__init__()

        # --------------------------------------------------------------------------
        # initialize the main properties of the model
        # a flat collection of elements - dict{GUID, Element}
        # a hierarchical relationships between elements
        # an abstract linkage or connection between elements and nodes
        # --------------------------------------------------------------------------
        self._name = name  # the name of the model
        self._elements = OrderedDict()
        self._hierarchy = ElementTree(model=self, name=name)
        self._interactions = Graph(name=name)
