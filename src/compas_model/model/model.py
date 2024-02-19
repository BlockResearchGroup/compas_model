import compas

if not compas.IPY:
    from typing import Optional, Tuple  # noqa: F401

from collections import OrderedDict
from compas.datastructures import Datastructure

from compas_model.elements import Element
from compas_model.interactions import Interaction  # noqa: F401

from .interactiongraph import InteractionGraph
from .groupnode import GroupNode
from .elementnode import ElementNode
from .elementtree import ElementTree


class Model(Datastructure):
    """Class representing a general model of hierarchically organised elements, with interactions.

    Attributes
    ----------
    elements : dict
        The elements of the model mapped by their guid.
    tree : :class:`ElementTree`
        A hierarchical structure of the elements in the model.
    graph : :class:`InteractionGraph`
        A graph containing the interactions between the elements of the model on its edges.

    Notes
    -----
    A model has an element tree to store the hierarchical relationships between elements,
    and an interaction graph to store the interactions between pairs of elements.
    Model elements are contained in the tree hierarchy in tree nodes, and in the interaction graph in graph nodes.

    Every model element can appear only once in the tree, and only once in the graph.
    This means that every element can have only one hierarchical parent.
    At the same time, independently of the hierarchy, every element can have many interactions with other elements.

    """

    @property
    def __data__(self):
        # in their data representation,
        # the element tree and the interaction graph
        # refer to model elements by their GUID, to avoid storing duplicate data representations of those elements
        # the elements are stored in a global list
        data = {
            "tree": self._tree.__data__,
            "graph": self._graph.__data__,
            "elements": list(self._elements.values()),
        }
        return data

    @classmethod
    def __from_data__(cls, data):
        model = cls()

        guid_element = {str(element.guid): element for element in data["elements"]}

        def add(nodedata, parentnode):
            # type: (dict, ElementNode | GroupNode) -> None

            for childdata in nodedata["children"]:
                if "element" in childdata:
                    guid = childdata["element"]
                    element = guid_element[guid]
                    childnode = ElementNode(element=element)
                else:
                    childnode = GroupNode(name=childdata["name"])
                parentnode.add(childnode)
                add(childdata, childnode)

        # add all children of a node's data representation
        # in a "live" version of the node,
        # while converting the data representations of the children to "live" nodes as well
        # in this process, guid references to model elements are replaced by the actual elements
        add(data["tree"]["root"], model._tree.root)  # type: ignore

        # note that this overwrites the existing interaction graph
        # during the reconstruction process,
        # guid references to model elements are replaced by actual elements
        model._graph = InteractionGraph.__from_data__(data["graph"], guid_element)

        return model

    def __init__(self, name=None):
        super(Model, self).__init__(name=name)
        self._elements = OrderedDict()
        self._tree = ElementTree(model=self)
        self._graph = InteractionGraph()
        self._graph.update_default_node_attributes(element=None)
        self._elementlist = []

    def __getitem__(self, index):
        # type: (int) -> Element
        return self.elementlist[index]

    # =============================================================================
    # Attributes
    # =============================================================================

    @property
    def elements(self):
        # type: () -> OrderedDict[str, Element]
        return self._elements

    @property
    def tree(self):
        # type: () -> ElementTree
        return self._tree

    @property
    def graph(self):
        # type: () -> InteractionGraph
        return self._graph

    @property
    def elementlist(self):
        # type: () -> list[Element]
        if len(self._elementlist) != len(self._elements):
            self._elementlist = list(self._elements.values())
        return self._elementlist

    # =============================================================================
    # Methods
    # =============================================================================

    def add_element(self, element, parent=None):
        # type: (Element, ElementNode | GroupNode | None) -> ElementNode
        """Add an element to the model.

        Parameters
        ----------
        element : :class:`Element`
            The element to add.
        parent : :class:`ElementNode` | :class:`GroupNode`, optional
            The parent (group) node of the element.
            If ``None``, the element will be added directly under the root node.

        Returns
        -------
        :class:`Elementnode`
            The tree node containing the element in the hierarchy.

        Raises
        ------
        ValueError
            If the parent node is not a GroupNode.

        """
        guid = str(element.guid)
        if guid in self._elements:
            raise Exception("Element already in the model.")
        self._elements[guid] = element

        element.graph_node = self._graph.add_node(element=element)

        if not parent:
            parent = self._tree.root  # type: ignore

        if not isinstance(parent, (ElementNode, GroupNode)):
            raise ValueError("Parent should be ElementNode or GroupNode.")

        element_node = ElementNode(element=element)
        parent.add(element_node)

        return element_node

    def add_elements(self, elements, parent=None):
        # type: (list[Element], ElementNode | GroupNode | None) -> list[ElementNode]
        """Add multiple elements to the model.

        Parameters
        ----------
        elements : list[:class:`Element`]
            The model elements.
        parent : :class:`GroupNode`, optional
            The parent (group) node of the elements.
            If ``None``, the elements will be added directly under the root node.

        Returns
        -------
        list[:class:`ElementNode`]

        """
        nodes = []
        for element in elements:
            nodes.append(self.add_element(element, parent=parent))
        return nodes

    def add_group(self, name, parent=None):
        # type: (str, GroupNode | None) -> GroupNode
        """Add a group to the model.

        Parameters
        ----------
        name : str
            The name of the group.
        parent : :class:`GroupNode`, optional
            The parent (group) node for the group.

        Returns
        -------
        :class:`GroupNode`

        """
        if not parent:
            parent = self._tree.root  # type: ignore

        if not isinstance(parent, GroupNode):
            raise ValueError("Parent should be a GroupNode.")

        groupnode = GroupNode(name=name)
        parent.add(groupnode)

        return groupnode

    def add_interaction(self, a, b, interaction=None):
        # type: (Element, Element, Interaction | None) -> tuple[int, int]
        """Add an interaction between two elements of the model.

        Parameters
        ----------
        a : :class:`Element`
            The first element.
        b : :class:`Element`
            The second element.
        interaction : :class:`Interaction`, optional
            The interaction object.

        Returns
        -------
        tuple[int, int]
            The edge of the interaction graph representing the interaction between the two elements.

        Raises
        ------
        Exception
            If one or both of the elements are not in the graph.

        """
        guid_a = str(a.guid)
        guid_b = str(b.guid)
        if guid_a not in self._elements or guid_b not in self._elements:
            raise Exception("Please add both elements to the model first.")

        node_a = a.graph_node
        node_b = b.graph_node
        if not self._graph.has_node(node_a) or not self._graph.has_node(node_b):
            raise Exception(
                "Something went wrong: the elements are not in the interaction graph."
            )

        edge = self._graph.add_edge(node_a, node_b, interaction=interaction)
        return edge

    # def add_interaction_by_index(
    #     self, id0: int, id1: int, interaction: Interaction = None
    # ) -> Tuple[int, int]:
    #     return self.graph.add_edge(id0, id1, interaction)

    # def get_interactions_lines(self, log=False):
    #     """Get the lines of the interactions as a list of tuples of points."""
    #     lines = []
    #     for edge in self.graph.edges():
    #         p0 = self.graph.node_attributes(edge[0])["element"].frame.point
    #         p1 = self.graph.node_attributes(edge[1])["element"].frame.point
    #         if log:
    #             print("Line end points: ", p0, p1)
    #         lines.append(Line(p0, p1))
    #     return lines

    def remove_element(self, element: Element):
        # type: (Element) -> None
        """Remove an element from the model.

        Parameters
        ----------
        element : :class:`Element`
            The element to remove.

        Returns
        -------
        None

        """
        guid = str(element.guid)
        if guid not in self._elements:
            raise Exception("Element not in the model.")
        del self._elements[guid]

        self._graph.delete_node(element.graph_node)
        self._tree.remove(element.tree_node)

    # ==========================================================================
    # Printing
    # ==========================================================================

    def print(self):
        print("=" * 80)
        print("Model Hierarchy")
        print("=" * 80)
        self._tree.print_hierarchy()
        print("=" * 80)
        print("Model Interactions")
        print("=" * 80)
        self._graph.print_interactions()
        print("=" * 80)
