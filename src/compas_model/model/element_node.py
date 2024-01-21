from compas_model.elements.element import Element
from compas.datastructures import TreeNode


class ElementNode(TreeNode):
    """A leaf node that stores Element object.

    Parameters
    ----------
    name : str, optional
        If element is not given, it defaults to str(``uuid.uuid4()``) of this class.
    element : :class:`compas_model.elements.Element`, optional
        :class:`compas_model.elements.Element` or any classes that inherits from it.
    attributes : dict, optional
        A dictionary of additional attributes.
    parent : :class:`compas_model.model.GroupNode`, optional
        The parent node of this node.
        This input is required when the node is created separately (not by my_model.add_element(...))
        After creation, the parent becomes the branch or sub-branch of the node.

    Attributes
    ----------
    name : str
        Name of the node, default: :class:`compas_model.elements.Element` str(``uuid.uuid4()``), otherwise user defined.
    element : :class:`compas_model.elements.Element`, read-only
        Element object stored in the node or any classes that inherits from it.

    """

    def __init__(self, name=None, element=None, attributes=None, parent=None):

        super().__init__(name=name, attributes=attributes)

        # --------------------------------------------------------------------------
        # The node stores Element object in the attributes dictionary.
        # --------------------------------------------------------------------------
        if isinstance(element, Element) is False:
            raise Exception("ElementNode should have an element input.")

        element.node = (
            self  # reference the current node to the element once it is added
        )
        self._element = element  # node stores the Element object

        # --------------------------------------------------------------------------
        # Make the node into a leaf, it has no children.
        # --------------------------------------------------------------------------
        self._children = None  # make the leaf

        # --------------------------------------------------------------------------
        # When a node is created separately, a user must define the parent node:
        # --------------------------------------------------------------------------
        self._parent = parent
        if parent is not None:
            self._tree = parent._tree

        # --------------------------------------------------------------------------
        # For debugging, the default name is the guid of an ElementNode
        # --------------------------------------------------------------------------
        self._name = None
        self.name = name

    # ==========================================================================
    # Serialization
    # ==========================================================================

    @property
    def data(self):
        return {
            "name": self.name,
            "attributes": self.attributes,
            "element": self.element,
        }

    @classmethod
    def from_data(cls, data):
        element = data["element"]
        node = cls(name=data["name"], element=element, attributes=data["attributes"])
        return node

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def name(self):
        if not self._name:
            return str(self.guid)
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def element(self):
        return self._element

    # ==========================================================================
    # Printing
    # ==========================================================================

    def __repr__(self):
        return "<{}> {}, <element> {}".format(
            self.__class__.__name__, self.name, self.element
        )

    def __str__(self):
        return self.__repr__()
