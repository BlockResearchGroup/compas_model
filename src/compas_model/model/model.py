from collections import OrderedDict
from collections import deque

import compas
import compas.datastructures  # noqa: F401
import compas.geometry  # noqa: F401
from compas.datastructures import Datastructure
from compas.geometry import Frame

from compas_model.elements import Element  # noqa: F401
from compas_model.interactions import Interaction  # noqa: F401

from .elementnode import ElementNode
from .elementtree import ElementTree
from .groupnode import GroupNode
from .interactiongraph import InteractionGraph


class Model(Datastructure):
    """Class representing a general model of hierarchically organised elements, with interactions.

    Attributes
    ----------
    elements : dict
        The elements of the model mapped by their guid.
    tree : :class:`ElementTree`
        A tree representing the spatial hierarchy of the elements in the model.
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
            "elementlist": self.elementlist,
        }
        return data

    @classmethod
    def __from_data__(cls, data):
        model = cls()

        elementdict = {str(element.guid): element for element in data["elementlist"]}

        def add(nodedata, parentnode):
            # type: (dict, GroupNode) -> None

            for childdata in nodedata["children"]:
                if "element" in childdata:
                    if "children" in childdata:
                        raise Exception("A node containing an element cannot have children.")

                    guid = childdata["element"]
                    element = elementdict[guid]
                    childnode = ElementNode(element=element)
                    parentnode.add(childnode)

                elif "children" in childdata:
                    if "element" in childdata:
                        raise Exception("A node containing other nodes cannot have an element.")

                    childnode = GroupNode(
                        name=childdata["name"],
                        attr=childdata["attributes"],
                    )
                    parentnode.add(childnode)
                    add(childdata, childnode)

                else:
                    raise Exception("A node without an element and without children is not supported.")

        # add all children of a node's data representation
        # in a "live" version of the node,
        # while converting the data representations of the children to "live" nodes as well
        # in this process, guid references to model elements are replaced by the actual elements
        add(data["tree"]["root"], model._tree.root)  # type: ignore

        # note that this overwrites the existing interaction graph
        # during the reconstruction process,
        # guid references to model elements are replaced by actual elements
        model._graph = InteractionGraph.__from_data__(data["graph"], elementdict)

        return model

    def __init__(self, name=None):
        super(Model, self).__init__(name=name)
        self._frame = None
        self._elementdict = OrderedDict()
        self._tree = ElementTree(model=self)
        self._graph = InteractionGraph()
        self._graph.update_default_node_attributes(element=None)
        self._elementlist = []

    def __getitem__(self, index):
        # type: (int) -> Element
        return self.elementlist[index]

    # ==========================================================================
    # Info
    # ==========================================================================

    def print_model(self):
        print("=" * 80)
        print("Spatial Hierarchy")
        print("=" * 80)
        self._tree.print_hierarchy()
        print("=" * 80)
        print("Element Interactions")
        print("=" * 80)
        self._graph.print_interactions()
        print("=" * 80)
        print("Element Groups")
        print("=" * 80)
        print("n/a")
        print("=" * 80)

    # =============================================================================
    # Attributes
    # =============================================================================

    @property
    def elementdict(self):
        # type: () -> OrderedDict[str, Element]
        return self._elementdict

    @property
    def elementlist(self):
        # type: () -> list[Element]
        if len(self._elementlist) != len(self._elementdict):
            self._elementlist = list(self._elementdict.values())
        return self._elementlist

    @property
    def tree(self):
        # type: () -> ElementTree
        return self._tree

    @property
    def graph(self):
        # type: () -> InteractionGraph
        return self._graph

    # A model should have a coordinate system.
    # This coordinate system is the reference frame for all elements in the model.
    # The elements in the model can define their own frame wrt the coordinate system of the model.
    # The hierarchy of transformations is defined through the element tree.
    # Each element can compute its own world coordinates by traversing the element tree.
    # Alternatively (and this might be faster),
    # the model can compute the transformations of all of the elements in the tree.

    @property
    def frame(self):
        # type: () -> compas.geometry.Frame
        if not self._frame:
            self._frame = Frame.worldXY()
        return self._frame

    @frame.setter
    def frame(self, frame):
        self._frame = frame

    # =============================================================================
    # Datastructure "abstract" methods
    # =============================================================================

    def transform(self, transformation):
        # type: (compas.geometry.Transformation) -> None
        """Transform the model and all that it contains.

        Parameters
        ----------
        :class:`compas.geometry.Transformation`
            The transformation to apply.

        Returns
        -------
        None
            The model is modified in-place.

        """
        # not sure what to do with this yet
        # especially because of potential scale transformations
        raise NotImplementedError

    # =============================================================================
    # Methods
    # =============================================================================

    def has_element(self, element):
        # type: (Element) -> bool
        guid = str(element.guid)
        return guid in self._elementdict

    def has_interaction(self, a, b):
        pass

    def add_element(self, element, parent=None):
        # type: (Element, GroupNode | None) -> ElementNode
        """Add an element to the model.

        Parameters
        ----------
        element : :class:`Element`
            The element to add.
        parent : :class:`GroupNode`, optional
            The parent group node of the element.
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
        if guid in self._elementdict:
            raise Exception("Element already in the model.")
        self._elementdict[guid] = element

        element.graph_node = self._graph.add_node(element=element)

        if not parent:
            parent = self._tree.root  # type: ignore

        if not isinstance(parent, GroupNode):
            raise ValueError("Parent should be a GroupNode.")

        element_node = ElementNode(element=element)
        parent.add(element_node)

        return element_node

    def add_elements(self, elements, parent=None):
        # type: (list[Element], GroupNode | None) -> list[ElementNode]
        """Add multiple elements to the model.

        Parameters
        ----------
        elements : list[:class:`Element`]
            The model elements.
        parent : :class:`GroupNode`, optional
            The parent group node of the elements.
            If ``None``, the elements will be added directly under the root node.

        Returns
        -------
        list[:class:`ElementNode`]

        """
        nodes = []
        for element in elements:
            nodes.append(self.add_element(element, parent=parent))
        return nodes

    def add_group(self, name, parent=None, attr=None, **kwargs):
        # type: (str, GroupNode | None, dict | None, dict) -> GroupNode
        """Add a group to the model.

        Parameters
        ----------
        name : str
            The name of the group.
        parent : :class:`GroupNode`, optional
            The parent (group) node for the group.
        attr : dict, optional
            Additional attributes to add to the group.
        **kwargs : dict, optional
            Additional keyword arguments, which will be added to the attributes dict.

        Returns
        -------
        :class:`GroupNode`

        """
        attr = attr or {}
        attr.update(kwargs)

        if not parent:
            parent = self._tree.root  # type: ignore

        if not isinstance(parent, GroupNode):
            raise ValueError("Parent should be a GroupNode.")

        groupnode = GroupNode(name=name, attr=attr)
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
        if not self.has_element(a) or not self.has_element(b):
            raise Exception("Please add both elements to the model first.")

        node_a = a.graph_node
        node_b = b.graph_node

        if not self._graph.has_node(node_a) or not self._graph.has_node(node_b):
            raise Exception("Something went wrong: the elements are not in the interaction graph.")

        edge = self._graph.add_edge(node_a, node_b, interaction=interaction)
        return edge

    def remove_element(self, element):
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
        if guid not in self._elementdict:
            raise Exception("Element not in the model.")
        del self._elementdict[guid]

        self._graph.delete_node(element.graph_node)
        self._tree.remove(element.tree_node)

    def remove_interaction(self, a, b):
        # type: (Element, Element) -> None
        """Remove the interaction between two elements.

        Parameters
        ----------
        a : :class:`Element`
        b : :class:`Element`

        Returns
        -------
        None

        """
        edge = a.graph_node, b.graph_node
        if self.graph.has_edge(edge):
            self.graph.delete_edge(edge)
            return

        edge = b.graph_node, a.graph_node
        if self.graph.has_edge(edge):
            self.graph.delete_edge(edge)
            return

    def elements_connected_by(self, interaction_type):
        """Find groups of elements connected by a specific type of interaction.

        Parameters
        ----------
        interaction_type : Type[:class:`compas_model.interactions.Interaction`]
            The type of interaction.

        Returns
        -------
        list[list[:class:`compas_model.elements.Element`]]

        """
        # type: (Type[Interaction]) -> list[list[Element]]

        def bfs(adjacency, root):
            tovisit = deque([root])
            visited = set([root])
            while tovisit:
                node = tovisit.popleft()
                for nbr in adjacency[node]:
                    if nbr not in visited:
                        if self.graph.has_edge((node, nbr)):
                            edge = node, nbr
                        else:
                            edge = nbr, node
                        interaction = self.graph.edge_attribute(edge, name="interaction")
                        if isinstance(interaction, interaction_type):
                            tovisit.append(nbr)
                            visited.add(nbr)
            return visited

        tovisit = set(self.graph.adjacency)
        components = []
        while tovisit:
            root = tovisit.pop()
            visited = bfs(self.graph.adjacency, root)
            tovisit -= visited
            if len(visited) > 1:
                components.append(visited)
        return components
