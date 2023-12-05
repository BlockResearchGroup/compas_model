from compas_model.elements.element import Element
from compas.datastructures import TreeNode


class ElementNode(TreeNode):
    """A tree leaf node that stores Element object


    Parameters
    ----------
    name : str, optional
        A name or identifier for the node.

    element : Element, optional
        Element or any classes that inherits from Element class.

    attributes : dict, optional
        A dictionary of additional attributes to be associated with the node.

    parent : Node, optional
        The parent node of this node.
        This input is required when the node is created separately (not by tree.add_element(...))
        After creation, the parent becomes the branch or sub-branch of the node.


    Attributes
    ----------
    element : Element, read-only
        Element object stored in the node or any classes that inherits from Element class.
    """

    def __init__(self, name=None, element=None, attributes=None, parent=None):

        super().__init__(name=name, attributes=attributes)

        # --------------------------------------------------------------------------
        # the node stores Element object in the attributes dictionary
        # --------------------------------------------------------------------------
        if isinstance(element, Element) is False:
            raise Exception("ElementNode should have an element input")
        else:
            self.attributes["my_object"] = element  # node stores the Element object

        # --------------------------------------------------------------------------
        # make the node into a leaf, it has no children
        # --------------------------------------------------------------------------
        self._children = None  # make the leaf

        # --------------------------------------------------------------------------
        # when a node is created separately, a user must define the parent node:
        # --------------------------------------------------------------------------
        self._parent = parent
        if parent is not None:
            self._tree = parent._tree

        # --------------------------------------------------------------------------
        # for debugging, the default name is the guid of an ElementNode
        # --------------------------------------------------------------------------
        self.name = name if name else str(self.guid)

    # ==========================================================================
    # Serialization
    # ==========================================================================

    @property
    def data(self):
        return {
            "name": self.name,
            "attributes": self.attributes,
            "children": None,
            "my_object": self.attributes["my_object"],
        }

    @classmethod
    def from_data(cls, data):
        my_object = data["my_object"]
        node = cls(name=data["name"], element=my_object, attributes=data["attributes"])
        node._children = None
        return node

    # ==========================================================================
    # Attributes
    # ==========================================================================
    @property
    def element(self):
        """Element object stored in the base Node class attributes dictionary "my_object" property
        Returns
        -------
        Element
        """
        return self.attributes["my_object"]

    # ==========================================================================
    # Operators
    # ==========================================================================

    def __eq__(self, other):
        """check if two nodes are the same by comparing their guids

        Parameters
        ----------
        other : Node
            The other node to compare with.

        Returns
        -------
        bool
            True if the guids are the same.
            False otherwise.
        """
        if self.element.guid == other.element.guid:
            return True
        else:
            return False

    # ==========================================================================
    # Printing
    # ==========================================================================

    def __repr__(self):
        return "<{}> {}, <element> {}".format(
            self.__class__.__name__, self.name, self.attributes["my_object"]
        )

    def __str__(self):
        return self.__repr__()
