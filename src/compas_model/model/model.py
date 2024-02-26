from collections import OrderedDict
from compas_model.model.element_node import ElementNode
from compas_model.model.group_node import GroupNode
from compas_model.model.element_tree import ElementTree
from compas_model.elements import Element, BlockElement
from compas_model.model.interaction import Interaction
from compas.datastructures import Datastructure
from compas_model.model import InteractionGraph
from compas.datastructures import Mesh
from compas.geometry import Line
from typing import Tuple


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
    Model elements are contained in the tree hierarchy in tree nodes.
    Model elements are contained in the interaction graph in graph nodes.
    Every model element can appear only once in the tree, and once in the graph.
    This means every element can have only one hierarchical parent.
    Every element can have many interactions with other elements.
    The interactions and hierarchical relations are independent.

    """

    @property
    def __data__(self):
        elements = {str(element.guid): element for element in self._elements.values()}
        data = {
            "tree": self._tree.__data__,
            "graph": self._graph.__data__,
            "elements": list(elements.values()),
        }
        return data

    @classmethod
    def __from_data__(cls, data):
        model = cls()

        guid_element = {str(element.guid): element for element in data["elements"]}

        def add(nodedata: dict, parentnode: ElementNode):
            for childdata in nodedata["children"]:
                guid = childdata["element"]
                element = None if not guid else guid_element[guid]
                # perhaps this needs to be handled differently
                # to allow for tree nodes that are not element nodes
                childnode = ElementNode(element=element)
                parentnode.add(childnode)
                add(childdata, childnode)

        add(data["tree"]["root"], model._tree.root)

        graph = InteractionGraph.__from_data__(data["graph"], guid_element)
        model._graph = graph

        return model

    def __init__(self, name=None):
        super(Model, self).__init__(name)
        self._elements: OrderedDict[str, Element] = {}
        self._tree = ElementTree(model=self)
        self._graph = InteractionGraph()
        self._graph.update_default_node_attributes(element=None)
        self._elements_list = []

    def __getitem__(self, index) -> Element:
        return self.elements_list[index]

    # =============================================================================
    # Attributes
    # =============================================================================
    @property
    def elements(self):
        return self._elements

    @property
    def tree(self):
        return self._tree

    @property
    def graph(self):
        return self._graph

    @property
    def elements_list(self):
        if len(self._elements_list) != len(self._elements):
            self._elements_list = list(self._elements.values())
        return self._elements_list

    @property
    def tree_nodes(self):
        return self.tree.root.children

    # =============================================================================
    # Methods
    # =============================================================================

    def add_element(self, element: Element, parent: GroupNode = None):

        # Elements dictionary:
        guid = str(element.guid)
        if guid in self._elements:
            raise Exception("Element already in the model.")
        self._elements[guid] = element

        # Graph
        element.graph_node = self._graph.add_node(element=element)

        # Find this child's parent:
        parent_node = None

        if not parent:
            parent_node = self._tree.root
        else:
            parent_node = self._tree.find_group_node(parent)

        if not parent_node:
            raise Exception("Parent node could not be identified.")

        # Create a new ElementNode and assign the parent:
        element_node = ElementNode(element=element)
        parent_node.add(element_node)
        return element_node

    def add_elements(self, elements: list[Element], parent: GroupNode = None):
        nodes = []
        for element in elements:
            nodes.append(self.add_element(element, parent))
        return nodes

    def remove_element(self, element: Element):
        guid = str(element.guid)
        if guid not in self._elements:
            raise Exception("Element not in the model.")
        del self._elements[guid]

        self._graph.remove_node(element.tree_node)
        self._tree.remove_element(element)

    def add_group(self, name: str, parent: GroupNode = None):
        # Find this child's parent:
        parent_node = None
        if not parent:
            parent_node = self._tree.root
        else:
            parent_node = self._tree.find_group_node(parent)

        if not parent_node:
            raise Exception("Parent node could not be identified.")

        # Create a new ElementNode and assign the parent:
        group_node = GroupNode(name=name)
        parent_node.add(group_node)
        return group_node

    def add_interaction(
        self, a: Element, b: Element, interaction: Interaction = None
    ) -> Tuple[int, int]:
        guid_a = str(a.guid)
        guid_b = str(b.guid)
        if guid_a not in self._elements or guid_b not in self._elements:
            raise Exception("Please add both elements to the model first.")

        if not self._graph.has_node(a.graph_node) or not self._graph.has_node(
            b.graph_node
        ):
            raise Exception(
                "Something went wrong: the elements are not in the interaction graph."
            )

        self._graph.add_edge(a.graph_node, b.graph_node, interaction=interaction)
        return a.graph_node, b.graph_node

    def add_interaction_by_index(
        self, id0: int, id1: int, interaction: Interaction = None
    ) -> Tuple[int, int]:
        return self.graph.add_edge(id0, id1, interaction)

    def get_interactions_lines(self, log=False):
        """Get the lines of the interactions as a list of tuples of points."""
        lines = []
        for edge in self.graph.edges():
            p0 = self.graph.node_attributes(edge[0])["element"].frame.point
            p1 = self.graph.node_attributes(edge[1])["element"].frame.point
            if log:
                print("Line end points: ", p0, p1)
            lines.append(Line(p0, p1))
        return lines

    # ==========================================================================
    # Printing
    # ==========================================================================

    def print(self):
        """Prints the spatial structure of the ElementTree, along with the total number of Elements and Graph nodes and edges."""
        print("\u2500" * 100)
        print("TREE")

        def _print(node, depth=0):
            parent_name = node.parent.name if node.parent else "None"
            group_name = node.name if node else "None"
            message = (
                "    " * depth
                + group_name
                + f" | Parent: {parent_name} | Root: {node.tree.name}"
                if depth
                else str(self.tree.name) + " | Root: " + str(self.tree.root.name)
            )
            print(message)
            if node.children:
                for child in node.children:
                    _print(child, depth + 1)

        _print(self.tree.root)

        print("\u2500" * 100)
        print("GRAPH")
        print("<Nodes>")
        for node in self.graph.nodes():
            print(" " * 4 + str(node))
        print("<Edges>")
        for edge in self.graph.edges():
            print(" " * 4 + " ".join(map(str, edge)))
        print("\u2500" * 100)


if __name__ == "__main__":

    model = Model()

    a = BlockElement(geometry=Mesh())
    b = BlockElement(geometry=Mesh())

    element_node0 = model.add_element(a)
    element_node1 = model.add_element(b)
    # print(a.name)

    model.print()
    model.to_json("model.json", pretty=True)

    # s = compas.json_dumps(model, pretty=True)
    # print(s)

    # d: Model = compas.json_loads(s)
    # d._tree.print_hierarchy()
