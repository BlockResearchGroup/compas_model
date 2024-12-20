from collections import OrderedDict
from collections import deque
from typing import Generator
from typing import Optional
from typing import Type

from compas.datastructures import Datastructure
from compas.geometry import Frame
from compas.geometry import Transformation
from compas_model.elements import Element
from compas_model.interactions import Interaction
from compas_model.materials import Material

from .elementnode import ElementNode
from .elementtree import ElementTree
from .interactiongraph import InteractionGraph


class ModelError(Exception):
    pass


class Model(Datastructure):
    """Class representing a general model of hierarchically organised elements, with interactions.

    Attributes
    ----------
    tree : :class:`ElementTree`, read-only
        A tree representing the spatial hierarchy of the elements in the model.
    graph : :class:`InteractionGraph`, read-only
        A graph containing the interactions between the elements of the model on its edges.
    frame : :class:`compas.geometry.Frame`
        The reference frame for all the elements in the model.
        By default, this is the world coordinate system.

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
    def __data__(self) -> dict:
        # in their data representation,
        # the element tree and the interaction graph
        # refer to model elements by their GUID, to avoid storing duplicate data representations of those elements
        # the elements are stored in a global list
        data = {
            "frame": self.frame,
            "tree": self._tree.__data__,
            "graph": self._graph.__data__,
            "elements": list(self.elements()),
            "materials": list(self.materials()),
            "element_material": {str(element.guid): str(element.material.guid) for element in self.elements() if element.material},
        }
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "Model":
        model = cls()
        model._guid_material = {str(material.guid): material for material in data["materials"]}
        model._guid_element = {str(element.guid): element for element in data["elements"]}

        for e, m in data["element_material"].items():
            element: Element = model._guid_element[e]
            material: Material = model._guid_material[m]
            element._material = material

        def add(nodedata: dict, parentnode: ElementNode) -> None:
            if "children" in nodedata:
                for childdata in nodedata["children"]:
                    guid = childdata["element"]
                    element = model._guid_element[guid]
                    attr = childdata.get("attributes") or {}
                    childnode = ElementNode(element=element, name=childdata["name"], **attr)
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
        model._graph = InteractionGraph.__from_data__(data["graph"], model._guid_element)

        return model

    def __init__(self, name=None):
        super().__init__(name=name)

        self._frame = None
        self._guid_material = {}
        self._guid_element = OrderedDict()
        self._tree = ElementTree()
        self._graph = InteractionGraph()
        self._graph.update_default_node_attributes(element=None)
        self._graph.update_default_edge_attributes(interactions=None)

    def __str__(self):
        output = "=" * 80 + "\n"
        output += "Spatial Hierarchy\n"
        output += "=" * 80 + "\n"
        output += str(self._tree) + "\n"
        output += "=" * 80 + "\n"
        output += "Element Interactions\n"
        output += "=" * 80 + "\n"
        output += str(self._graph) + "\n"
        output += "=" * 80 + "\n"
        output += "Element Groups\n"
        output += "=" * 80 + "\n"
        output += "n/a\n"
        output += "=" * 80 + "\n"
        return output

    # =============================================================================
    # Attributes
    # =============================================================================

    # not sure if this dict/list is a good naming convention
    # furthermore, the list variants can actually be modified by the user
    # which is not the intention of the model API
    # perhaps it would be better to not make the dict variants public,
    # rename the list variants to elements/materials,
    # and return tuples instead of lists,
    # such that the user can't make unintended and potentially breaking changes

    @property
    def tree(self) -> ElementTree:
        return self._tree

    @property
    def graph(self) -> InteractionGraph:
        return self._graph

    # A model should have a coordinate system.
    # This coordinate system is the reference frame for all elements in the model.
    # The elements in the model can define their own frame wrt the coordinate system of the model.
    # The hierarchy of transformations is defined through the element tree.
    # Each element can compute its own world coordinates by traversing the element tree.
    # Alternatively (and this might be faster),
    # the model can compute the transformations of all of the elements in the tree.

    @property
    def frame(self) -> Frame:
        if not self._frame:
            self._frame = Frame.worldXY()
        return self._frame

    @frame.setter
    def frame(self, frame: Frame):
        self._frame = frame

    # =============================================================================
    # Datastructure "abstract" methods
    # =============================================================================

    def transform(self, transformation: Transformation) -> None:
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
        for element in self.elements():
            element.transformation = transformation

    # =============================================================================
    # Methods
    # =============================================================================

    def has_element(self, element: Element) -> bool:
        """Returns True if the model contains the given element.

        Parameters
        ----------
        element : :class:`Element`
            The element to check.

        Returns
        -------
        bool

        """
        guid = str(element.guid)
        return guid in self._guid_element

    def has_interaction(self, a: Element, b: Element) -> bool:
        """Returns True if two elements have an interaction set between them.

        Parameters
        ----------
        a : :class:`Element`
            The first element.
        b : :class:`Element`
            The second element.

        Returns
        -------
        bool

        """
        edge = a.graphnode, b.graphnode
        result = self.graph.has_edge(edge)
        if not result:
            edge = b.graphnode, a.graphnode
            result = self.graph.has_edge(edge)
        return result

    def has_material(self, material: Material) -> bool:
        """Verify that the model contains a specific material.

        Parameters
        ----------
        material : :class:`Material`
            A model material.

        Returns
        -------
        bool

        """
        guid = str(material.guid)
        return guid in self._guid_material

    def add_element(self, element: Element, parent: Optional[ElementNode] = None, material: Optional[Material] = None) -> ElementNode:
        """Add an element to the model.

        Parameters
        ----------
        element : :class:`Element`
            The element to add.
        parent : :class:`ElementNode`, optional
            The parent group node of the element.
            If ``None``, the element will be added directly under the root node.
        material : :class:`Material`, optional
            A material to assign to the element.
            Note that the material should have already been added to the model before it can be assigned.

        Returns
        -------
        :class:`Elementnode`
            The tree node containing the element in the hierarchy.

        Raises
        ------
        ValueError
            If the parent node is not a GroupNode.
        ValueError
            If a material is provided that is not part of the model.

        """
        guid = str(element.guid)
        if guid in self._guid_element:
            raise Exception("Element already in the model.")

        self._guid_element[guid] = element

        element.graphnode = self.graph.add_node(element=element)

        if not parent:
            parent = self._tree.root

        if isinstance(parent, Element):
            if parent.treenode is None:
                raise ValueError("The parent element is not part of this model.")

            parent = parent.treenode

        if not isinstance(parent, ElementNode):
            raise ValueError("Parent should be an Element or ElementNode of the current model.")

        if material and not self.has_material(material):
            raise ValueError("The material is not part of the model: {}".format(material))

        element_node = ElementNode(element=element)
        parent.add(element_node)

        if material:
            self.assign_material(material=material, element=element)

        element.model = self

        return element_node

    def add_elements(self, elements: list[Element], parent: Optional[ElementNode] = None) -> list[ElementNode]:
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

    def add_material(self, material: Material) -> None:
        """Add a material to the model.

        Parameters
        ----------
        material : :class:`Material`
            A material.

        Returns
        -------
        None

        """
        guid = str(material.guid)
        if guid in self._guid_material:
            raise Exception("Material already in the model.")

        # check if a similar material is already in the model
        self._guid_material[guid] = material

    def add_interaction(self, a: Element, b: Element, interaction: Optional[Interaction] = None) -> tuple[int, int]:
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

        node_a = a.graphnode
        node_b = b.graphnode

        if not self.graph.has_node(node_a) or not self.graph.has_node(node_b):
            raise Exception("Something went wrong: the elements are not in the interaction graph.")

        edge = self._graph.add_edge(node_a, node_b)

        if interaction:
            interactions = self.graph.edge_interactions(edge) or []
            interactions.append(interaction)
            self.graph.edge_attribute(edge, name="interactions", value=interactions)

        self._guid_element[str(b.guid)].is_dirty = True

        return edge

    def remove_element(self, element: Element) -> None:
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
        if guid not in self._guid_element:
            raise Exception("Element not in the model.")

        self._guid_element[guid].is_dirty = True

        del self._guid_element[guid]

        self.graph.delete_node(element.graphnode)
        self.tree.remove(element.treenode)

    def remove_interaction(self, a: Element, b: Element, interaction: Optional[Interaction] = None) -> None:
        """Remove the interaction between two elements.

        Parameters
        ----------
        a : :class:`Element`
        b : :class:`Element`
        interaction : :class:`Interaction`, optional

        Returns
        -------
        None

        """
        if interaction:
            raise NotImplementedError

        elements = list(self.elements())
        elements[b.graphnode]._is_dirty = True

        edge = a.graphnode, b.graphnode
        if self.graph.has_edge(edge):
            self.graph.delete_edge(edge)
            return

        edge = b.graphnode, a.graphnode
        if self.graph.has_edge(edge):
            self.graph.delete_edge(edge)
            return

    def assign_material(self, material: Material, element: Optional[Element] = None, elements: Optional[list[Element]] = None) -> None:
        """Assign a material to an element or a list of elements.

        Parameters
        ----------
        material : :class:`Material`
            The material.
        element : :class:`Element`, optional
            The element to assign the material to.
        elements : list[:class:`Element`, optional]
            The list of elements to assign the material to.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If neither `element` or `elements` is provided.
        ValueError
            If both `element` and `elements` are provided.
        ValueError
            If the material is not part of the model.
        ValueError
            If the provided element or one of the elements in the provided element list is not part of the model.

        """
        if not self.has_material(material):
            raise ValueError("This material is not part of the model: {}".format(material))
        if not element and not elements:
            raise ValueError("Either an element or a list of elements should be provided.")
        if element and elements:
            raise ValueError("It is not allowed to provide both an element and an element list.")
        if element:
            if not self.has_element(element):
                raise ValueError("This element is not part of the model: {}".format(element))
            element._material = material
        else:
            if any(not self.has_element(element) for element in elements):
                raise ValueError("This element is not part of the model: {}".format(element))
            for element in elements:
                element._material = material

    # =============================================================================
    # Accessors
    # =============================================================================

    def elements(self) -> Generator[Element, None, None]:
        """Yield all the elements contained in the model.

        Yields
        ------
        :class:`Element`

        """
        return iter(self._guid_element.values())

    def materials(self) -> Generator[Material, None, None]:
        """Yield all the materials contained in the model.

        Yields
        ------
        :class:`Material`

        """
        return iter(self._guid_material.values())

    def interactions(self) -> Generator[Interaction, None, None]:
        """Yield all interactions between all elements in the model.

        Yields
        ------
        :class:`Interaction`

        """
        return self._graph.interactions()

    def elements_connected_by(self, interaction_type: Type[Interaction]) -> list[list[Element]]:
        """Find groups of elements connected by a specific type of interaction.

        Parameters
        ----------
        interaction_type : Type[:class:`compas_model.interactions.Interaction`]
            The type of interaction.

        Returns
        -------
        list[list[:class:`compas_model.elements.Element`]]

        """

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
                        interactions = self.graph.edge_interactions(edge)
                        if any(isinstance(interaction, interaction_type) for interaction in interactions):
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
