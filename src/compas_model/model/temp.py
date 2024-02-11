from typing import Union, Tuple
from compas.data import Data
from compas.geometry import Geometry
from compas.datastructures import Datastructure
from compas.datastructures import Mesh
from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas.datastructures import Graph


class Interaction(Data):
    pass


class Element(Data):
    """Base class for all model elements.

    Parameters
    ----------
    geometry : {Geometry | Mesh}, optional
        The geometric representation of the element.

    Notes
    -----
    It is important that this class supports the entire serialisation mechanism,
    because the type of element and its geometic representation cannot be known in advance.

    """

    @property
    def __data__(self) -> dict:
        return {
            "geometry": self.geometry,
        }

    def __init__(self, geometry: Union[Geometry, Mesh] = None):
        super().__init__()
        self._aabb = None
        self._obb = None
        self.geometry = geometry
        self.node = None  # this is the node of the graph

    @property
    def aabb(self):
        if not self._aabb:
            self._aabb = self.compute_aabb()
        return

    def compute_aabb(self):
        raise NotImplementedError


class BlockElement(Element):
    """Class representing block elements.

    Parameters
    ----------
    geometry : :class:`compas.datastructures.Mesh`
        The geometry of the block.
    is_support : bool, optional
        Flag to indicate that this element is a support block.

    Attributes
    ----------
    is_support : bool
        Flag to indicate that this element is a support.

    """

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["is_support"] = self.is_support
        return data

    def __init__(self, geometry: Mesh, is_support: bool = False):
        super().__init__(geometry=geometry)
        self.is_support = is_support


class ElementNode(TreeNode):
    """Class representing nodes containing elements in an element tree.

    Parameters
    ----------
    element : :class:`Element`
        The element contained in the node.

    Attributes
    ----------
    element : :class:`Element`
        The element contained in the node.

    Notes
    -----
    This object will raise an Exception,
    when it is (de)serialised independently, outside the context of a Model.

    """

    @property
    def __data__(self):
        data = super().__data__
        data["element"] = None if not self.element else str(self.element.guid)
        return data

    @classmethod
    def __from_data__(cls, data):
        raise Exception(
            "ElementNode objects should only be serialised through a Model object."
        )

    def __init__(self, element: Element = None):
        super(ElementNode, self).__init__()
        self.element = element


class ElementTree(Tree):
    """Class representing the hierarchy of elements in a model."""

    @property
    def __data__(self):
        data = super().__data__
        return data

    @classmethod
    def __from_data__(cls, data):
        raise Exception(
            "ElementTree objects should only be serialised through a Model object."
        )

    def __init__(self, name: str = None):
        super().__init__(name=name)
        root = ElementNode()
        self.add(root)

    @property
    def elements(self) -> list[Element]:
        return [node.element for node in self.nodes if isinstance(node, ElementNode)]

    def find_element_node(self, element: Element):
        for node in self.nodes:
            if isinstance(node, ElementNode):
                if node.element is element:
                    return node
        raise ValueError("Element not in tree")


class InteractionGraph(Graph):
    """Class representing the interactions between elements in a model.

    Notes
    -----
    Ideally, graph (and mesh) are rewritten to use dedicated classes for nodes and edges.
    This will allow more fine-grained control over the (types of) attributes added to nodes and edges.
    It will also provide a much more intuitive API.

    """

    @property
    def __data__(self):
        data = super().__data__
        for node, attr in data["node"].items():
            attr["element"] = str(attr["element"].guid)
        return data

    @classmethod
    def __from_data__(cls, data, guid_element):
        graph = super().__from_data__(data)
        for _, attr in graph.nodes(data=True):
            attr["element"] = guid_element[attr["element"]]
        return graph

    def __init__(
        self,
        default_node_attributes=None,
        default_edge_attributes=None,
        name=None,
        **kwargs
    ):
        super().__init__(
            default_node_attributes=default_node_attributes,
            default_edge_attributes=default_edge_attributes,
            name=name,
            **kwargs,
        )
        self.update_default_node_attributes(element=None)
        self.update_default_edge_attributes(interaction=None)


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
        self._elements: dict[str, Element] = {}
        self._tree = ElementTree()
        self._graph = InteractionGraph()
        self._graph.update_default_node_attributes(element=None)

    @property
    def tree(self):
        return self._tree

    @property
    def graph(self):
        return self._graph

    # =============================================================================
    # Overwrites from Datastructure
    # =============================================================================

    # =============================================================================
    # Methods
    # =============================================================================

    def add_element(self, element: Element, parent: Element = None) -> ElementNode:
        guid = str(element.guid)
        if guid in self._elements:
            raise Exception("Element already in the model.")
        self._elements[guid] = element
        elementnode = ElementNode(element=element)
        if not parent:
            parentnode = self._tree.root
        else:
            parentnode = self._tree.find_element_node(parent)
        if not parentnode:
            raise Exception("Parent node could not be identified.")
        element.node = self._graph.add_node(element=element)
        parentnode.add(elementnode)
        print("element_node", element.node)
        return elementnode

    def remove_element(self, element: Element) -> None:
        pass

    def add_interaction(
        self, a: Element, b: Element, interaction: Interaction = None
    ) -> Tuple[int, int]:
        guid_a = str(a.guid)
        guid_b = str(b.guid)
        if guid_a not in self._elements or guid_b not in self._elements:
            raise Exception("Please add both elements to the model first.")

        print(self._graph.has_node(a.node))
        if not self._graph.has_node(a.node) or not self._graph.has_node(b.node):
            raise Exception(
                "Something went wrong: the elements are not in the interaction graph."
            )

        self._graph.add_edge(a.node, b.node, interaction=interaction)
        return a.node, b.node

    # def add_interaction(self, a: Element, b: Element, interaction: Interaction = None) -> Tuple[int, int]:
    #     guid_a = str(a.guid)
    #     guid_b = str(b.guid)
    #     if guid_a not in self._elements or guid_b not in self._elements:
    #         raise Exception("Please add both elements to the model first.")

    #     if not self._graph.has_node(a.node) or not self._graph.has_node(b.node):
    #         raise Exception("Something went wrong: the elements are not in the interaction graph.")

    #     self._graph.add_edge(a.node, b.node, interaction=interaction)
    #     return a.node, b.node

    def remove_interaction(self, a: Element, b: Element) -> None:
        edge = a.node, b.node
        if self._graph.has_edge(edge, directed=False):
            self._graph.delete_edge(edge)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":

    model = Model()

    a = Element(geometry=Mesh())
    b = Element(geometry=Mesh())

    model.add_element(a)
    model.add_element(b)

    model.add_interaction(a, b)

    # model._tree.print_hierarchy()
    # print(model.graph.default_node_attributes["element"])
    # print(model.graph.default_edge_attributes)

    # for node, attr in model.graph.nodes(data=True):
    #     node.node_attributes("element")
    #     print(attr["element"])

    # for node, attr in data["node"].items():
    #     attr["element"] = str(attr["element"].guid)¨

    # for node in model.graph.nodes():
    #     print(node)

    # for node, attr in model.graph.__data__["node"].items():
    #     print(attr)

    # print(model.graph.to_jsonstring(pretty=True))
    # print(str(model.graph.attr["element"].guid))

    # print(model.graph.to_jsonstring(pretty=True))

    # print(model._graph.nodes())

    # s = compas.json_dumps(model, pretty=True)
    # print(s)

    # d: Model = compas.json_loads(s)
    # d._tree.print_hierarchy()
