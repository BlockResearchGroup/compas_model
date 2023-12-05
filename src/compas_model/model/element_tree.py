from compas.datastructures import Tree
from compas_model.model.group_node import GroupNode


class ElementTree(Tree):
    """elementree stores a tree of elements and group nodes

    Parameters
    ----------
    model : Model
        Model object to update the element dictionary and the graph.

    name : str, optional
        A name or identifier for the tree.

    attributes : dict, optional
        A dictionary of additional attributes to be associated with the tree.

    """

    def __init__(self, model=None, name="root", attributes=None):

        super(ElementTree, self).__init__(name=name, attributes=attributes)

        # --------------------------------------------------------------------------
        # there is only one root node and it is of type GroupNode
        # from this node, we can backtrack to node->ElementTree->Model
        # --------------------------------------------------------------------------
        self._root = GroupNode(name="root", geometry=None, attributes=None, parent=None)
        self._root._tree = self

        # --------------------------------------------------------------------------
        # initialize the main properties of the model
        # --------------------------------------------------------------------------
        self.name = name  # the name of the tree
        self._model = model  # variable that points to the model class
