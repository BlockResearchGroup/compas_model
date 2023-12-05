from compas.datastructures import Tree
from compas_model.elements.element import Element
from compas_model.model.element_node import ElementNode
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

    # ==========================================================================
    # Serialization
    # ==========================================================================
    @property
    def data(self):

        # serialize the nodes
        nodes = []
        for child in self.root.children:  # type: ignore
            nodes.append(child.data)

        # output the dictionary
        return {
            "name": self.name,
            "nodes": nodes,  # type: ignore
            "attributes": self.attributes,
        }

    @classmethod
    def from_data(cls, data):

        model_tree = cls(model=None, name=data["name"], attributes=data["attributes"])
        nodes = []

        for node in data["nodes"]:
            if isinstance(node["attributes"]["my_object"], Element):
                nodes.append(ElementNode.from_data(node))
            else:
                nodes.append(GroupNode.from_data(node))

        for node in nodes:
            node._tree = model_tree
            node._parent = model_tree.root
            model_tree.root._children.append(node)
        return model_tree

    # ==========================================================================
    # Properites
    # ==========================================================================
    @property
    def root(self):
        """Root node of the tree.

        Returns
        -------
        GroupNode
        """
        return self._root

    @property
    def model(self):
        """Model object that the tree belongs to.

        Returns
        -------
        Model
        """

        return self._model

    @property
    def number_of_elements(self):
        """Number of elements only in ElementNodes"""
        # iterate all children and count ElementNode
        count = 0

        def _count_elements(node, count):
            for child in node.children:
                if isinstance(child, ElementNode):
                    count += 1
                else:
                    count = _count_elements(child, count)
            return count

        count = _count_elements(self.root, count)
        return count

    # ==========================================================================
    # Printing
    # ==========================================================================

    def __repr__(self):
        return "ElementTree with {} nodes".format(len(list(self.nodes)))

    def __str__(self):
        return self.__repr__()

    def print(self):
        """Print the tree in a readable format."""

        def _print(node, depth=0):

            # ------------------------------------------------------------------
            # print current node
            # ------------------------------------------------------------------
            parent_name = "None" if node.parent is None else node.parent.name
            print("-" * 100)
            message = (
                "    " * depth
                + str(node)
                + " "
                + "| Parent: "
                + parent_name
                + " | Root: "
                + node.tree.name
            )

            if depth == 0:
                message += (
                    " | Elements: " + "{" + str(node.tree.number_of_elements) + "}"
                )

            print(message)

            # ------------------------------------------------------------------
            # recursion
            # ------------------------------------------------------------------
            if node.children is not None:
                for child in node.children:
                    _print(child, depth + 1)

        # ------------------------------------------------------------------
        # main call for the recursive printing
        # ------------------------------------------------------------------
        _print(self.root)

    # ==========================================================================
    # Behavior - Tree
    # ==========================================================================

    def add_group(self, name=None, geometry=None, attributes=None, parent=None):
        """Add a group node to the tree.

        Parameters
        ----------

        name : str, optional
            A name or identifier for the node.

        geometry : Any, optional
            Geometry or any other property, when you want to give a group a shape besides name.

        attributes : dict, optional
            A dictionary of additional attributes to be associated with the node.
        """
        return self.root.add_group(
            name=name, geometry=geometry, attributes=attributes, parent=None
        )

    def add_element(self, name=None, element=None, attributes=None, parent=None):
        """Add an element node to the tree.

        Parameters
        ----------
        name : str, optional
            A name or identifier for the node.

        element : Element, optional
            Element or any classes that inherits from Element class.

        attributes : dict, optional
            A dictionary of additional attributes to be associated with the node.

        Returns
        -------
        ElementNode
            ElementNode object or any class that inherits from ElementNode class.
        """
        return self.root.add_element(
            name=name, element=element, attributes=attributes, parent=None
        )
