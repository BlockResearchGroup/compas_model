from compas.datastructures import TreeNode
from compas_model.elements.element import Element
from compas_model.model.element_node import ElementNode


class GroupNode(TreeNode):

    """A group node that is represented by a name and a geometry and a list of children


    Parameters
    ----------
    name : str, optional
        A name or identifier for the node.
    geometry : Any, optional
        Geometry or any other property, when you want to give a group a shape besides name.
    attributes : dict, optional
        A dictionary of additional attributes to be associated with the node.

    parent : Node, optional
        The parent node of this node.
        This input is required when the node is created separately (not by tree.add_group(...))
        After creation, the parent becomes the branch or sub-branch of the node.


    Attributes
    ----------
    geometry : Geometry, read-only
        The geometry of the node, if it is assigned.

    """

    def __init__(self, name=None, geometry=None, attributes=None, parent=None):

        super().__init__(name=name, attributes=attributes)

        # --------------------------------------------------------------------------
        # geometry of the group node
        # --------------------------------------------------------------------------
        self._geometry = geometry  # node stores the Element object

        # --------------------------------------------------------------------------
        # when a node is created separately, a user must define the parent node:
        # --------------------------------------------------------------------------
        self._parent = parent
        if parent is not None:
            self._tree = parent._tree

        # --------------------------------------------------------------------------
        # for debugging, the default name is the guid of th GroupNode
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
            "children": [child.data for child in self.children],
            "geometry": self.geometry,
        }

    @classmethod
    def from_data(cls, data):
        geometry = data["geometry"]

        # empty root node - it has not children at this step
        node = cls(name=data["name"], geometry=geometry, attributes=data["attributes"])

        # add children and sub-children
        for child in data["children"]:
            if child["children"]:
                # recursively add children
                node.add(cls.from_data(child))
            else:
                # otherwise add a leaf
                node.add_element(
                    name=child["name"],
                    element=child["element"],
                    attributes=child["attributes"],
                )

        return node

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def geometry(self):
        """Geometry object

        Returns
        -------
        Any

        """
        return self._geometry

    # ==========================================================================
    # Operators
    # ==========================================================================

    def __eq__(self, other):
        """Override the equality operator to compare the guid of two nodes

        Parameters
        ----------
        other : Node
            The other node to compare with.

        Returns
        -------
        bool
            True if the two nodes are the same, False otherwise.

        """
        if self.guid == other.guid:
            return True
        else:
            return False

    # ==========================================================================
    # Printing
    # ==========================================================================

    def __repr__(self):
        return "<{}> {}, <geometry> {}".format(
            self.__class__.__name__, self.name, self.geometry
        )

    def __str__(self):
        return self.__repr__()

    def add_element(
        self, name=None, element=None, attributes=None, copy_element=False, parent=None
    ):

        """Add element to the group

        Triple Behavior:

        1. If Element_Node exists, add an element to the base dictionary of the Model class.
        2. If Element_Node exists, add an element to the graph.
        3. Add a node tree.

        Parameters
        ----------
        name : str
            a name of the ElementNode.
        element : Element
            Element object or any class that inherits from Element class.
        attributes : dict, optional
            A dictionary of additional attributes to be associated with the node.
        copy_element : bool, optional
            If True, the element is copied before adding to the tree.
        parent : Node, optional
            The parent node of this node.

        """
        # -----------------------------------------------------------------------
        # user interface
        # 1 user did not provide anything -> return None
        # 2 user provided element input -> my_node.add_element(name, element)
        # 3 otherwise there is an exception
        # -----------------------------------------------------------------------

        if isinstance(element, Element):
            element_copy = element.copy() if copy_element else element
            name = name if name else str(element_copy.guid)
        else:
            raise Exception("At least provide element input")

        # -----------------------------------------------------------------------
        # set a parent property in element, incase you want to traverse backwards
        # create a node and add it to the tree
        # -----------------------------------------------------------------------
        element_copy.parent = parent if parent else self
        node = ElementNode(
            name=name,
            element=element_copy,
            attributes=attributes,
            parent=element_copy.parent,
        )

        # -----------------------------------------------------------------------
        # add the node to the children list
        # -----------------------------------------------------------------------
        self._children.append(node)

        # -----------------------------------------------------------------------
        # add elements to the base dictionary of Model class and graph
        # -----------------------------------------------------------------------
        if self._tree is not None:
            if self._tree._model is not None:
                key = str(node.element.guid)
                self._tree._model.elements[key] = node.element  # type: ignore
                self._tree._model._interactions.add_node(key)  # type: ignore

        return node

    def add_group(self, name=None, geometry=None, attributes=None, parent=None):
        """add group to the group

        Parameters
        ----------
        name : str, optional
            A name or identifier for the node.
        geometry : Any, optional
            Geometry or any other property, when you want to give a group a shape besides name.
        attributes : dict, optional
            A dictionary of additional attributes to be associated with the node.
        parent : Node, optional
            The parent node of this node.

        """
        # -----------------------------------------------------------------------
        # if parent is not provided, use the node that called this method
        # -----------------------------------------------------------------------
        parent = parent if parent else self

        # -----------------------------------------------------------------------
        # create a GroupNode
        # -----------------------------------------------------------------------
        node = GroupNode(
            name=name, geometry=geometry, attributes=attributes, parent=parent
        )

        # -----------------------------------------------------------------------
        # add the node to the tree
        # -----------------------------------------------------------------------
        if node not in self._children:
            self._children.append(node)

        # -----------------------------------------------------------------------
        # output the node, so that other nodes can be added to it childs
        # -----------------------------------------------------------------------
        return node
