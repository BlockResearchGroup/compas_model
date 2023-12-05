from collections import OrderedDict
from compas.datastructures import Graph
from compas_model.model.element_node import ElementNode
from compas_model.model.group_node import GroupNode
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
        # --------------------------------------------------------------------------
        # if the user write Model(elements=[...])
        # then add the elements as ElementNode objects to the model
        # --------------------------------------------------------------------------
        self.add_elements(elements=elements, copy_elements=copy_elements)

    # ==========================================================================
    # Serialization
    # ==========================================================================
    @property
    def data(self):

        return {
            "name": self._name,
            "elements": self._elements,
            "hierarchy": self._hierarchy.data,
            "interactions": self._interactions.data,
        }

    @classmethod
    def from_data(cls, data):
        model = cls(data["name"])
        model._elements = data["elements"]
        model._hierarchy = ElementTree.from_data(data["hierarchy"])
        model._hierarchy._model = model  # variable that points to the model class
        model._interactions = Graph.from_data(data["interactions"])
        return model

    # ==========================================================================
    # Attributes
    # ==========================================================================
    @property
    def name(self):
        return self._name

    @property
    def elements(self):
        return self._elements

    @property
    def hierarchy(self):
        return self._hierarchy

    @property
    def interactions(self):
        return list(self._interactions.edges())

    # ==========================================================================
    # Statistics
    # ==========================================================================
    @property
    def number_of_elements(self):
        """
        Get the number of elements in the model.

        Returns
        -------
        int
            The total number of elements in the model.
        """
        return len(list(self.elements))

    @property
    def number_of_nodes(self):
        """
        Count the total number of children in the tree hierarchy.

        Returns
        -------
        int
            The total number of child nodes in the tree hierarchy.
        """

        def _count(node):
            count = 0
            if node.children is None:
                return 0
            for child in node.children:
                count += 1 + _count(child)
            return count

        total_children = _count(self._hierarchy.root)
        return total_children

    @property
    def number_of_edges(self):
        """
        Get the number of edges in the model's interactions.

        Returns
        -------
        int
            The total number of edges in the interactions graph of the model.
        """
        return self._interactions.number_of_edges()

    # ==========================================================================
    # Printing
    # ==========================================================================
    def print_elements(self):
        """
        Print all elements in the model.

        This method prints all elements in the model to the console.
        """
        print(
            "================================== {} ===================================".format(
                self.interactions.name
            )
        )
        graph_nodes = list(self._interactions.nodes())
        for idx, e in enumerate(self._elements):
            print(
                "element_guid: "
                + str(self._elements[e].guid)
                + " graph_node: "
                + str(graph_nodes[idx])
            )

    def print_interactions(self):
        """
        Print all interactions between elements.

        This method prints all interactions between elements in the model to the console.
        """
        print(
            "================================== {} ===================================".format(
                self._interactions.name
            )
        )
        edges = list(self._interactions.edges())
        for i in range(len(edges)):
            a = edges[i][0]
            b = edges[i][1]
            print(
                "print_interactions ",
                str(self._elements[a].guid),
                " ",
                str(self._elements[b].guid),
            )

    def __repr__(self):
        return (
            "<"
            + self.__class__.__name__
            + ">"
            + " with {} elements, {} children, {} interactions, {} nodes".format(
                self.number_of_elements,
                self.number_of_nodes,
                self.number_of_edges,
                self._interactions.number_of_nodes(),
            )
        )

    def __str__(self):
        return self.__repr__()

    def print(self):
        """
        Print the spatial hierarchy of the tree for debugging and visualization.

        This method prints information about the tree's spatial hierarchy, including nodes, elements,
        parent-child relationships, and other relevant details.

        """

        # ------------------------------------------------------------------
        # print hierarchy
        # ------------------------------------------------------------------
        print("\u2500" * 100)
        print("HIERARCHY")

        def _print(node, depth=0):
            parent_name = "None" if node.parent is None else node.parent.name

            # print current data
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
                message = str(self)

            print(message)

            # ------------------------------------------------------------------
            # recursively print
            # ------------------------------------------------------------------
            if node.children is not None:
                for child in node.children:
                    _print(child, depth + 1)

        _print(self._hierarchy.root)

        # ------------------------------------------------------------------
        # print interactions
        # ------------------------------------------------------------------
        print("INTERACTIONS")
        print("<Nodes>")
        for node in self._interactions.nodes():
            print(" " * 4 + str(node))
        print("<Edges>")
        for edge in self._interactions.edges():
            print(" " * 4 + str(edge[0]) + " " + str(edge[1]))
        print("\u2500" * 100)

    # ==========================================================================
    # Behavior - Hierarchy
    # ==========================================================================
    def add_elements(self, elements=[], copy_elements=False):
        """Adds elements to the model.

        This method allows you to add elements to the model.

        Parameters
        ----------

        elements : list, optional
            A list of elements to be added to the model.

        copy_elements : bool, optional
            If True, the elements are copied before adding to the model.

        Returns
        -------
        list : guid
            A list of identifiers for the elements.
        """
        guids = []
        for element in elements:
            guids.append(
                self._tree_utils.add_element(
                    name=None, element=element, copy_element=copy_elements
                )
            )
        return guids

    def add_element(self, name=None, element=None, attributes=None, copy_element=False):
        """Adds an element to the model.

        This method allows you to add an element to the model.

        Parameters
        ----------
        name : str, optional
            A name or identifier for the element.

        element : Element, optional
            Element or any classes that inherits from Element class.

        attributes : dict, optional
            A dictionary of additional attributes to be associated with the element.

        copy_element : bool, optional
            If True, the element is copied before adding to the model.

        Returns
        -------
        ElementNode
        """

        return self.hierarchy.root.add_element(
            name=name,
            element=element,
            attributes=attributes,
            copy_element=copy_element,
            parent=self._hierarchy.root,
        )

    def add_group(self, name=None, geometry=None, attributes=None):
        """Adds a group to the model.

        Parameters
        ----------
        name : str, optional
            A name or identifier for the group.

        geometry : Any, optional
            Geometry or any other property, when you want to give a group a shape besides name.

        attributes : dict, optional
            A dictionary of additional attributes to be associated with the group.

        Returns
        -------
        GroupNode
        """
        return self.hierarchy.root.add_group(
            name=name,
            geometry=geometry,
            attributes=attributes,
            parent=self._hierarchy.root,
        )

    # ==========================================================================
    # Behavior - Interactions
    # ==========================================================================
    def add_interaction(self, element0, element1, geometry=None, weight=1):
        """
        Adds an interaction between two elements in the model.

        This method allows you to establish an interaction between two elements within the model.

        Parameters
        ----------
        element0 : Element
            The first element involved in the interaction.

        element1 : Element
            The second element involved in the interaction.

        Returns
        -------
        tuple[hashable, hashable]
            The identifier of the edge.
        """
        # ------------------------------------------------------------------
        # check if user inputs ElementNode or Element
        # ------------------------------------------------------------------
        if element0 and element1 is None:
            raise ValueError("ElementNode or Element should be provided.")

        e0 = element0.element if isinstance(element0, ElementNode) else element0
        e1 = element1.element if isinstance(element1, ElementNode) else element1

        # ------------------------------------------------------------------
        # check if the nodes exist in the graph
        if self._interactions.has_node(str(e0.guid)) and self._interactions.has_node(
            str(e1.guid)
        ):
            attribute_dict = {"geometry": geometry, "weight": weight}
            return self._interactions.add_edge(
                str(e0.guid), str(e1.guid), attribute_dict
            )
        else:
            raise ValueError("The node does not exist.")

    # ==========================================================================
    # Copy
    # ==========================================================================
    def copy(self):
        """copy the model"""

        # --------------------------------------------------------------------------
        # create the empty model
        # --------------------------------------------------------------------------
        copy = Model(name=self.name)

        # --------------------------------------------------------------------------
        # copy the hierarchy
        # --------------------------------------------------------------------------
        dict_old_guid_and_new_element = {}

        def copy_hierarchy(current_node, copy_node):
            for child in current_node.children:
                last_group_node = None
                # --------------------------------------------------------------------------
                # copy the elements
                # --------------------------------------------------------------------------
                if isinstance(child, ElementNode):
                    # copy the element
                    name = child.name
                    element = child.element.copy()
                    # add the element to the dictionary
                    copy._elements[element.key] = element
                    # add the element to the graph
                    copy._interactions.add_node(element.key)
                    # add the element to the parent
                    copy_node.add_element(name=name, element=element)
                    # add the element to the dictionary
                    dict_old_guid_and_new_element[child.element.key] = element
                # --------------------------------------------------------------------------
                # copy the groups
                # --------------------------------------------------------------------------
                elif isinstance(child, GroupNode):
                    # copy the group
                    name = child.name
                    geometry = (
                        None if child.geometry is None else child._my_object.copy()
                    )
                    # add the group to the parent
                    last_group_node = copy_node.add_group(name=name, geometry=geometry)
                # --------------------------------------------------------------------------
                # recursively copy the tree
                # --------------------------------------------------------------------------
                if isinstance(child, GroupNode):
                    copy_hierarchy(child, last_group_node)

        copy_hierarchy(self._hierarchy.root, copy._hierarchy.root)

        # --------------------------------------------------------------------------
        # copy the interactions, nodes should be added previously
        # --------------------------------------------------------------------------
        for edge in self._interactions.edges():
            node0 = dict_old_guid_and_new_element[edge[0]]
            node1 = dict_old_guid_and_new_element[edge[1]]
            copy.add_interaction(node0, node1)

        return copy