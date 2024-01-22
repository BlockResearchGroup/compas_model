from compas.datastructures import TreeNode
from compas_model.elements.element import Element
from compas_model.model.element_node import ElementNode


class GroupNode(TreeNode):
    """A leaf node that stores a geometry object or any other type attribute.

    Parameters
    ----------
    name : str, optional
        A name or str(``uuid.uuid4()``).
    geometry : any, optional
        Geometry or any other property, when you want to give a group a shape besides name.
    parent : :class:`compas_model.model.GroupNode`, optional
        The parent node of this node.
        This input is required when the node is created separately (not by tree.add_group(...))
        After creation, the parent becomes the branch or sub-branch of the node.

    Attributes
    ----------
    name : str
        Name of the node, default: :class:`compas_model.model.GroupNode` guid, otherwise user defined.
    geometry : Geometry, read-only
        The geometry of the node, if it is assigned.

    """

    def __init__(self, name=None, geometry=None, parent=None):

        super().__init__(name=name)

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
        # for debugging, the default name is the guid of the GroupNode
        # --------------------------------------------------------------------------
        self._name = None
        self.name = name

    # ==========================================================================
    # Serialization
    # ==========================================================================

    @property
    def __data__(self):
        return {
            "name": self.name,
            "children": [child.__data__ for child in self.children],  # recursion
            "geometry": self.geometry,
        }

    @classmethod
    def __from_data__(cls, data):
        geometry = data["geometry"]

        # empty root node - it has not children at this step
        node = cls(name=data["name"], geometry=geometry)

        # add children and sub-children
        for child in data["children"]:
            if "children" in child:
                # recursively add children
                node.add(cls.__from_data__(child))
            else:
                # otherwise add a leaf
                node.add_element(
                    name=child["name"],
                    element=child["element"],
                )

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
    def geometry(self):
        return self._geometry

    # ==========================================================================
    # Operators
    # ==========================================================================

    def __eq__(self, other):
        """Override the equality operator to compare the names of the two nodes

        Parameters
        ----------
        other : :class:`compas_model.model.GroupNode`
            The other node to compare with.

        Returns
        -------
        bool
            True if the two nodes are the same, False otherwise.

        """
        if self.name == other.name:
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

    def add_element(self, name=None, element=None, copy_element=False, parent=None):
        """Add :class:`compas_model.model.ElementNode` to the current  :class:`compas_model.model.GroupNode`

        Triple Behavior:

        1. If Element_Node exists, add an element to the base dictionary of the Model class.
        2. If Element_Node exists, add an element to the graph.
        3. Add a node tree.

        Parameters
        ----------
        name : str
            A name of the node.
        element : :class:`compas_model.elements.Element`
            Element object or any class that inherits from Element class.
        copy_element : bool, optional
            If True, the element is copied before adding to the tree.
        parent : Node, optional
            The parent node of this node.

        Returns
        -------
        :class:`compas_model.model.ElementNode`
            ElementNode object or any class that inherits from ElementNode class.

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
            parent=element_copy.parent,
        )

        # -----------------------------------------------------------------------
        # add the node to the children list
        # -----------------------------------------------------------------------
        self._children.append(node)

        # -----------------------------------------------------------------------
        # add elements to the base dictionary of Model class and graph
        # -----------------------------------------------------------------------
        if self.tree is not None:
            if self.tree.model is not None:
                key = str(node.element.guid)
                self.tree.model.elements[key] = node.element  # type: ignore
                # _interaction private on purpose since user should not be able to add his own nodes to the graph
                self.tree.model._interactions.add_node(key)  # type: ignore add_interaction_node

        return node

    def add_group(self, name=None, geometry=None, parent=None):
        """Add :class:`compas_model.model.GroupNode` to the current :class:`compas_model.model.GroupNode`

        Parameters
        ----------
        name : str, optional
            A name or identifier for the node.
        geometry : Any, optional
            Geometry or any other property, when you want to give a group a shape besides name.
        parent : Node, optional
            The parent node of this node.

        Returns
        -------
        :class:`compas_model.model.GroupNode`
            GroupNode object or any class that inherits from GroupNode class.

        """
        # -----------------------------------------------------------------------
        # if parent is not provided, use the node that called this method
        # -----------------------------------------------------------------------
        parent = parent if parent else self

        # -----------------------------------------------------------------------
        # create a GroupNode
        # -----------------------------------------------------------------------
        node = GroupNode(name=name, geometry=geometry, parent=parent)

        # -----------------------------------------------------------------------
        # add the node to the tree
        # -----------------------------------------------------------------------
        if node not in self._children:
            self._children.append(node)

        # -----------------------------------------------------------------------
        # output the node, so that other nodes can be added to it childs
        # -----------------------------------------------------------------------
        return node
