from collections import OrderedDict
from compas.datastructures import Graph
from compas_model.model.element_node import ElementNode
from compas_model.model.group_node import GroupNode
from compas_model.model.element_tree import ElementTree
from compas.data import Data
from compas.geometry import Line
from uuid import UUID


class Model(Data):
    """A class representing computational models.

    Parameters
    ----------
    name : str, optional
        A name or identifier for the model.
    elements : list[:class:`compas_model.elements.Element`], optional
        A list of elements to be added to the model.
    copy_elements : bool, optional
        If True, the :class:`compas_model.elements.Element` are copied before adding to the model.

    Attributes
    ----------
    name : str
        Name of the model.
    elements : dict{``uuid.uuid4()``, :class:`compas_model.elements.Element`}
        A dictionary of elements.
    elements_list : list(:class:`compas_model.elements.Element`)
        A list of elements.
    hierarchy : :class:`compas.datastructures.Tree`
        A tree data-structure that stores a tree of elements and group nodes.
    interactions : :class:`compas.datastructures.Graph`
        A graph data-structure that stores interactions between elements.
    number_of_elements : int
        A total count in the :class:`compas_model.elements.Element` dictionary.
    number_of_nodes : int
        A total count of all :class:`compas.datastructures.TreeNode` in the hierarchy.
    number_of_edges : int
        A total count of all edges in the :class:`compas.datastructures.Graph`.

    Notes
    -----
    A model contains:

    a. flat collection of elements - dict{``uuid.uuid4()``, :class:`compas_model.elements.Element`}
    b. hierarchy between elements - :class:`compas.datastructures.Tree` (:class:`compas_model.model.ElementNode` or :class:`compas_model.model.GroupNode`)
    c. abstract linkages (connections between elements and nodes) - :class:`compas.datastructures.Graph` (str(``uuid.uuid4()``), str(``uuid.uuid4()``))

    """

    DATASCHEMA = None

    @property
    def __data__(self):
        return {
            "name": self._name,
            "elements": self._elements,
            "hierarchy": self._hierarchy.__data__,
            "interactions": self._interactions.__data__,
        }

    @classmethod
    def __from_data__(cls, data):
        model = cls(data["name"])
        model._elements = data["elements"]
        model._hierarchy = ElementTree.__from_data__(data["hierarchy"])
        model._hierarchy._model = model  # variable that points to the model class
        model._interactions = Graph.__from_data__(data["interactions"])
        return model

    def __init__(self, name="model", elements=[], copy_elements=False):
        super(Model, self).__init__(name=name)

        # --------------------------------------------------------------------------
        # Initialize the main properties of the model:
        # a) flat collection of elements - dict{guid, Element}
        # b) hierarchical relationships between elements - Tree(ElementNode or GroupNode)
        # c) abstract linkages (connection between elements and nodes) - Graph(str(guid), str(guid))
        # --------------------------------------------------------------------------

        self._elements = OrderedDict()
        self._hierarchy = ElementTree(model=self, name=name)
        self._interactions = Graph(name=name)

        # --------------------------------------------------------------------------
        # if the user write Model(elements=[...])
        # then add the elements as ElementNode objects to the model
        # --------------------------------------------------------------------------
        self.add_elements(elements=elements, copy_elements=copy_elements)

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

    def __getitem__(self, key):
        if isinstance(key, UUID):
            return self._elements[str(key)]
        elif isinstance(key, str):
            return self.get_by_name(key)

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def elements(self):
        return self._elements

    @property
    def elements_list(self):
        return list(self._elements.values())

    @property
    def hierarchy(self):
        return self._hierarchy

    @property
    def interactions(self):
        return list(self._interactions.edges())

    @property
    def number_of_elements(self):
        return len(list(self.elements))

    @property
    def number_of_nodes(self):
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
        return self._interactions.number_of_edges()

    # ==========================================================================
    # Printing
    # ==========================================================================

    def print(self):
        """Print the spatial strucutre of the :class:`compas_model.model.ElementTree`,
        also total number of :class:`compas_model.elements.Element`, :class:`compas.datastructures.Graph` nodes and edges.

        This method prints information about the tree's spatial hierarchy, including nodes, elements,
        parent-child relationships.

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

    def print_elements(self):
        """Print all :class:`compas_model.elements.Element` in the model."""
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
        """Print all :class:`compas.datastructures.Graph` nodes and edges."""
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

    # ==========================================================================
    # Behavior - Hierarchy
    # ==========================================================================

    def add_elements(self, elements=[], copy_elements=False):
        """Multiple calls to the :class:`compas_model.model.Model.add_element` method.

        Parameters
        ----------
        elements : list[:class:`compas_model.elements.Element`], optional
            A list of elements.
        copy_elements : bool, optional
            If True, the elements are copied before adding to the model.

        Returns
        -------
        list : ``uuid.uuid4()``
            A list of identifiers of the elements.

        """
        guids = []
        for element in elements:
            guids.append(
                self._hierarchy.root.add_element(
                    name=None, element=element, copy_element=copy_elements
                )
            )
        return guids

    def add_element(self, name=None, element=None, copy_element=False):
        """Add a :class:`compas_model.model.ElementNode` that represents a leaf with a property of an :class:`compas_model.elements.Element`.

        Parameters
        ----------
        name : str, optional
            A name or identifier for the element.
        element : :class:`compas_model.elements.Element`, optional
            Element or any classes that inherits from Element class.
        copy_element : bool, optional
            If True, the element is copied before adding to the model.

        Returns
        -------
        :class:`compas_model.model.ElementNode`

        """

        if not isinstance(name, str):
            raise TypeError("Attribute name is not string.")

        return self.hierarchy.root.add_element(
            name=name,
            element=element,
            copy_element=copy_element,
            parent=self._hierarchy.root,
        )

    def add_group(self, name=None, geometry=None):
        """Add a :class:`compas_model.model.GroupNode` that represent a group.

        Parameters
        ----------
        name : str, optional
            A name or identifier for the group.
        geometry : Any, optional
            Geometry or any other property, when you want to give a group a shape besides name.

        Returns
        -------
        :class:`compas_model.model.GroupNode`

        """
        return self.hierarchy.root.add_group(
            name=name,
            geometry=geometry,
            parent=self._hierarchy.root,
        )

    def to_nodes_and_neighbors(self):
        """Get the :class:`compas.datastructures.Graph` as a list of nodes and a list of neighbors."""
        nodes = []
        neighberhoods = []
        for node in self._interactions.nodes():
            nodes.append(node)
            neighberhoods.append(self._interactions.neighborhood(node))
        return (nodes, neighberhoods)

    def get_by_names(self, names):
        """Get elements by element names.

        Parameters
        ----------
        names : list
            Names of the elements.

        Returns
        -------
        list
            A list of elements.

        """

        return self.hierarchy.get_nodes_by_name(names)

    def get_by_name(self, name):
        """Get elements by element name.

        Parameters
        ----------
        name : str
            Name of the element.

        Returns
        -------
        :class:`compas_model.elements.Element`
            An element.

        """

        return self.hierarchy.get_node_by_name(name)

    def get_by_type(self, element_type="interface"):
        """Get elements by element name.

        Parameters
        ----------
        element_type : str, optional
            Type of the element, by default "interface".

        Returns
        -------
        list
            A list of elements.

        """
        elements = []
        for key, value in self._elements.items():
            if value.name == element_type:
                elements.append(value)
        return elements

    def get_connected_elements(self, element_type="interface"):
        """Get connected elements by element name.

        One joint can have two or more elements connected in one interface.

        Parameters
        ----------
        element_type : str, optional
            Type of the element, by default "interface".

        Returns
        -------
        list
            A list of connected elements.

        """

        # ------------------------------------------------------------------
        # collect elements by type
        # ------------------------------------------------------------------
        flagged_elements = {}
        connected_elements = {}
        for key, value in self._elements.items():
            if value.name == element_type:
                flagged_elements[key] = value
                connected_elements[key] = []
        print(connected_elements)

        # ------------------------------------------------------------------
        # collect connected elements
        # ------------------------------------------------------------------
        for edge in self._interactions.edges():
            if self._elements[edge[0]].name == element_type:
                connected_elements[edge[0]].append(self._elements[edge[1]])
            if self._elements[edge[1]].name == element_type:
                connected_elements[edge[1]].append(self._elements[edge[0]])

        return connected_elements

    # ==========================================================================
    # Behavior - Interactions
    # ==========================================================================

    def add_interaction(self, element0, element1, name=None, geometry=None, weight=1):
        """Add edges as a pair of :class:`compas_model.elements.Element` str(``uuid.uuid4()`` to the :class:`compas.datastructures.Graph`.
        The :class:`compas_model.model.Model.interactions` already contains all the previously added elements identifiers.

        Parameters
        ----------
        element0 : :class:`compas_model.elements.Element` or :class:`compas_model.model.ElementNode`
            The first element involved in the interaction.
        element1 : :class:`compas_model.elements.Element` or :class:`compas_model.model.ElementNode`
            The second element involved in the interaction.
        geometry : Any, optional
            Geometry or any other property, when you want to give an interaction a shape besides name.
        weight : int, optional
            The weight of the interaction.
        type : str, optional
            The type of the interaction.

        Returns
        -------
        tuple[str(``uuid.uuid4()``), str(``uuid.uuid4()``)]
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
            attribute_dict = {"geometry": geometry, "weight": weight, "name": name}
            return self._interactions.add_edge(
                str(e0.guid), str(e1.guid), attribute_dict
            )
        else:
            raise ValueError("The Node does not exist.")

    def get_interactions_lines(self):
        """Get the lines of the interactions as a list of tuples of points."""
        lines = []
        for edge in self._interactions.edges():
            p0 = self.elements[edge[0]].obb.frame.point
            p1 = self.elements[edge[1]].obb.frame.point
            lines.append(Line(p0, p1))
        return lines

    # ==========================================================================
    # Copy
    # ==========================================================================

    def copy(self):
        """Duplicate the :class:`compas_model.model.Model` properties: dict{``uuid.uuid4()``,
        :class:`compas_model.elements.Element`}, :class:`compas.datastructures.Tree` and :class:`compas.datastructures.Graph`.

        Returns
        -------
        :class:`compas_model.model.Model`
            A copy of the :class:`compas_model.model.Model` object.

        """
        # --------------------------------------------------------------------------
        # Create the empty model.
        # --------------------------------------------------------------------------
        copy = Model(name=self.name)

        # --------------------------------------------------------------------------
        # Copy the hierarchy.
        # --------------------------------------------------------------------------
        dict_old_guid_and_new_element = {}

        def copy_hierarchy(current_node, copy_node):
            for child in current_node.children:
                last_group_node = None
                # --------------------------------------------------------------------------
                # Copy the elements.
                # --------------------------------------------------------------------------
                if isinstance(child, ElementNode):
                    # Copy the Element.
                    name = child.name
                    element = child.element.copy()
                    # Add the Element to the Dictionary.
                    copy._elements[str(element.guid)] = element
                    # Add the Element to the Graph.
                    copy._interactions.add_node(str(element.guid))
                    # Add the Element to the Parent Node.
                    copy_node.add_element(name=name, element=element)
                    # Add the Element to the Model Dictionary.
                    dict_old_guid_and_new_element[str(child.element.guid)] = element
                # --------------------------------------------------------------------------
                # Copy the groups.
                # --------------------------------------------------------------------------
                elif isinstance(child, GroupNode):
                    # Copy the group.
                    name = child.name
                    geometry = None if child.geometry is None else child.geometry.copy()
                    # Add the group to the Parent Node.
                    last_group_node = copy_node.add_group(name=name, geometry=geometry)
                # --------------------------------------------------------------------------
                # Recursively copy the Tree.
                # --------------------------------------------------------------------------
                if isinstance(child, GroupNode):
                    copy_hierarchy(child, last_group_node)

        copy_hierarchy(self._hierarchy.root, copy._hierarchy.root)

        # --------------------------------------------------------------------------
        # Copy the interactions, Nodes should be added previously.
        # --------------------------------------------------------------------------
        for edge in self._interactions.edges():
            node0 = dict_old_guid_and_new_element[edge[0]]
            node1 = dict_old_guid_and_new_element[edge[1]]
            copy.add_interaction(node0, node1)

        return copy
