from collections import OrderedDict
from typing import Generator
from typing import Iterator
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from compas.datastructures import Datastructure
from compas.geometry import Transformation
from compas_model.datastructures import KDTree
from compas_model.elements import Element
from compas_model.elements import Group
from compas_model.interactions import Contact
from compas_model.materials import Material
from compas_model.modifiers import Modifier

from .bvh import ElementBVH
from .bvh import ElementOBBNode
from .elementtree import ElementNode
from .elementtree import ElementTree
from .interactiongraph import InteractionGraph

ElementType = TypeVar("ElementType", bound=Element)


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
    bvh : :class:`ElementBVH`, read-only
        To recompute the BVH, use :meth:`compute_bvh`.
        The BVH is used to speed up collision detection: for example, during calculation of element contacts.
    kdtree : :class:`KDTree`, read-only
        To recompute the tree, use :meth:`compute_kdtree`.
        The KD tree is used for nearest neighbour searches: for example, during calculation of element contacts.
    transformation : :class:`compas.geometry.Transformation`
        The transformation from local to world coordinates.

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
            "transformation": self.transformation,
            "tree": self._tree.__data__,
            "graph": self._graph.__data__,
            "elements": list(self.elements),
            "materials": list(self.materials),
            # have the feeling this can be avoided
            # reference from element to material should be though guid into the material store of the model
            "element_material": {str(element.guid): str(element.material.guid) for element in self.elements if element.material},
        }
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "Model":
        model = cls()
        model._materials = {str(material.guid): material for material in data["materials"]}
        model._elements = OrderedDict({str(element.guid): element for element in data["elements"]})

        model.transformation = data["transformation"]

        for e, m in data["element_material"].items():
            element: Element = model._elements[e]
            material: Material = model._materials[m]
            element._material = material

        def add(nodedata: dict, parentnode: ElementNode) -> None:
            if "children" in nodedata:
                for childdata in nodedata["children"]:
                    guid = childdata["element"]
                    element = model._elements[guid]
                    element.model = model
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
        model._graph = InteractionGraph.__from_data__(data["graph"], model._elements)

        return model

    def __init__(self, name=None):
        super().__init__(name=name)

        self._transformation = None
        self._materials = {}
        self._elements: OrderedDict[str, Element] = OrderedDict()
        self._tree = ElementTree()
        self._graph = InteractionGraph()
        self._graph.update_default_node_attributes(element=None)
        self._graph.update_default_edge_attributes(modifiers=None)
        self._graph.update_default_edge_attributes(contacts=None)

        self._bvh = None
        self._kdtree = None

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

    @property
    def tree(self) -> ElementTree:
        return self._tree

    @property
    def graph(self) -> InteractionGraph:
        return self._graph

    @property
    def bvh(self) -> ElementBVH:
        if not self._bvh:
            self._bvh = self.compute_bvh()
        return self._bvh

    @property
    def kdtree(self) -> KDTree:
        if not self._kdtree:
            self._kdtree = self.compute_kdtree()
        return self._kdtree

    @property
    def transformation(self) -> Optional[Transformation]:
        return self._transformation

    @transformation.setter
    def transformation(self, transformation: Transformation) -> None:
        self._transformation = transformation

    @property
    def elements(self) -> Iterator[Element]:
        return iter(self._elements.values())

    @property
    def materials(self) -> Iterator[Material]:
        return iter(self._materials.values())

    @property
    def contacts(self) -> Generator[Contact, None, None]:
        for edge in self.graph.edges():
            contacts = self.graph.edge_attribute(edge, name="contacts")
            if contacts:
                for contact in contacts:
                    yield contact

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
        self.transformation = transformation

    # =============================================================================
    # Elements
    # =============================================================================

    def add_element(
        self,
        element: Union[Element, ElementType],
        parent: Optional[Element] = None,
        material: Optional[Material] = None,
    ) -> Union[Element, ElementType]:
        """Add an element to the model.

        Parameters
        ----------
        element : :class:`Element`
            The element to add.
        parent : :class:`Element`, optional
            The parent element of the element.
            If ``None``, the element will be added directly under the root element.
        material : :class:`Material`, optional
            A material to assign to the element.
            Note that the material should have already been added to the model before it can be assigned.

        Returns
        -------
        :class:`Element`
            The element added to the model.

        Raises
        ------
        ValueError
            If the parent node is not a GroupNode.
        ValueError
            If a material is provided that is not part of the model.

        """
        guid = str(element.guid)
        if guid in self._elements:
            raise Exception("Element already in the model.")

        self._elements[guid] = element

        element.graphnode = self.graph.add_node(element=element)

        if parent is None:
            parent_node = self._tree.root
        elif isinstance(parent, Element):
            parent_node = parent.treenode
            if parent_node is None:
                raise ValueError("The parent element is not part of this model.")
        else:
            raise ValueError("Parent should be an Element or None")

        if material and not self.has_material(material):
            raise ValueError("The material is not part of the model: {}".format(material))

        element_node = ElementNode(element=element)

        if parent_node:
            parent_node.add(element_node)

        if material:
            self.assign_material(material=material, element=element)

        element.model = self

        self._bvh = None

        return element

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
        if guid not in self._elements:
            raise Exception("Element not in the model.")

        # self._elements[guid].is_dirty = True

        del self._elements[guid]

        self.graph.delete_node(element.graphnode)
        self.tree.remove(element.treenode)

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
        return guid in self._elements

    # =============================================================================
    # Groups
    # =============================================================================

    def add_group(self, name: Optional[str] = None) -> Group:
        """Add a group to the model.

        Parameters
        ----------
        name : str
            The name of the group.

        Returns
        -------
        :class:`Group`
            The group added to the model.

        """
        group = Group(name=name)
        self.add_element(group)
        return group

    # =============================================================================
    # Materials
    # =============================================================================

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
        if guid in self._materials:
            raise Exception("Material already in the model.")

        self._materials[guid] = material

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
        return guid in self._materials

    def assign_material(
        self,
        material: Material,
        element: Optional[Element] = None,
        elements: Optional[list[Element]] = None,
    ) -> None:
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
            element.material = material

        elif elements:
            if any(not self.has_element(element) for element in elements):
                raise ValueError("This element is not part of the model: {}".format(element))

            for element in elements:
                element.material = material

    # =============================================================================
    # Interactions
    # =============================================================================

    def add_interaction(self, a: Element, b: Element) -> tuple[int, int]:
        """Add an interaction between two elements of the model.

        Parameters
        ----------
        a : :class:`Element`
            The first element.
        b : :class:`Element`
            The second element.

        Returns
        -------
        tuple[int, int]
            The edge of the interaction graph representing the interaction between the two elements.

        Raises
        ------
        Exception
            If one or both of the elements are not in the graph.

        Notes
        -----
        In future implementations, adding an interaction should implicitly take care of adding modifiers
        onto the interaction edges, based on the registered modifiers of the source nodes.

        In the current implementation, modifiers have to be added explicitly using :meth:`add_modifiers`.
        This method will add an interaction edge from the source of the modifier to its target if needed
        and store the modifier object on it.

        """
        node_a = a.graphnode
        node_b = b.graphnode

        if not self.has_element(a) or not self.has_element(b):
            raise Exception("Please add both elements to the model first.")

        if not self.graph.has_node(node_a) or not self.graph.has_node(node_b):
            raise Exception("Something went wrong: the elements are not in the interaction graph.")

        edge = self.graph.add_edge(node_a, node_b)

        # modifiers = []
        # if a.modifiers:
        #     for modifiertype in a.modifiers:
        #         # modifiertype.applies_to
        #         # modifiers.append()
        #         pass

        # if modifiers:
        #     self.graph.edge_attribute(edge, name="modifiers", value=modifiers)

        return edge

    def remove_interaction(self, a: Element, b: Element) -> None:
        """Remove the interaction between two elements.

        Parameters
        ----------
        a : :class:`Element`
        b : :class:`Element`

        Returns
        -------
        None

        """
        # elements = list(self.elements)
        # elements[b.graphnode].is_dirty = True

        edge = a.graphnode, b.graphnode
        if self.graph.has_edge(edge):
            self.graph.delete_edge(edge)
            return

        edge = b.graphnode, a.graphnode
        if self.graph.has_edge(edge):
            self.graph.delete_edge(edge)
            return

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

    # =============================================================================
    # Modifiers (temp)
    # =============================================================================

    def add_modifier(
        self,
        source: Element,
        target: Element,
        modifiertype: Type[Modifier],
    ) -> list[Modifier]:
        """Add a modifier between two elements, with one the source of the modifier and the other the target.

        Parameters
        ----------
        source : :class:`compas_model.elements.Element`
            The source element.
        target : :class:`compas_model.elements.Element`
            The target element.
        modifiertype : Type[:class:`compas_model.modifiers.Modifier`]
            The type of modifier.

        Returns
        -------
        list[Modifier]
            All modifiers stored on the interaction edge between source and target.

        Notes
        -----
        This element should implement the protocol specified by the modifier.
        The methods of the source element defined by the protocol are used to compute the tools involved in the modification.
        The tools are used by the modifier to apply the modification to the model geometry of the target element.

        The modifier defines the protocol for the modification.
        The protocol should be implemented by the source element.
        The protocol methods of the source element are used to compute the modification tool.
        The modifier applies the modification to the target using this tool.

        """
        edge = self.add_interaction(source, target)
        modifiers = self.graph.edge_attribute(edge, name="modifiers") or []
        modifiers.append(modifiertype(source))
        self.graph.edge_attribute(edge, name="modifiers", value=modifiers)
        return modifiers

    # =============================================================================
    # Compute
    # =============================================================================

    def compute_bvh(
        self,
        nodetype=ElementOBBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
    ) -> ElementBVH:
        """Compute the Bounding Volume Hierarchy (BVH) of the elements for fast collision checks.

        Parameters
        ----------
        nodetype : :class:`ElementOBBNode`
            The type of bounding volume node used in the tree.
        max_depth : int, optional
            The maximum depth used for constructing the BVH.
        leafsize : int, optional
            The number of elements contained in a BVH leaf node.

        Returns
        -------
        :class:`ElementBVH`

        """
        self._bvh = ElementBVH.from_elements(
            self.elements,
            nodetype=nodetype,
            max_depth=max_depth,
            leafsize=leafsize,
        )
        return self._bvh

    def compute_kdtree(self) -> KDTree:
        """Compute the KD tree of the elements for fast nearest neighbour queries.

        The KD tree is built using the reference points of the elements of the model.

        Returns
        -------
        :class:`KDTree`

        """
        self._kdtree = KDTree(list(self.elements))
        return self._kdtree

    def compute_contacts(self, tolerance=1e-6, minimum_area=1e-2) -> None:
        """Compute the contacts between the block elements of this model.

        Computing contacts is done independently of the edges of the interaction graph.
        If contacts are found between two elements with an existing edge, the contacts attribute of the edge will be replaced.
        If there is no pre-existing edge, one will be added.
        No element pairs are excluded in the search based on the existence of an edge between their nodes in the interaction graph.

        The search is conducted entirely based on the BVH of the elements contained in the model.
        It is a spatial search that creates topological connections between elements based on their geometrical interaction.

        Parameters
        ----------
        tolerance : float, optional
            The distance tolerance.
        minimum_area : float, optional
            The minimum contact size.

        Returns
        -------
        None

        """
        for element in self.elements:
            u = element.graphnode

            for nbr in self.bvh.nearest_neighbors(element):
                v = nbr.graphnode
                if not self.graph.has_edge((u, v), directed=False):
                    contacts = element.contacts(nbr, tolerance=tolerance, minimum_area=minimum_area)
                    if contacts:
                        self.graph.add_edge(u, v, contacts=contacts)

                else:
                    edge = (u, v) if self.graph.has_edge((u, v)) else (v, u)
                    contacts = self.graph.edge_attribute(edge, name="contacts")
                    if not contacts:
                        contacts = element.contacts(nbr, tolerance=tolerance, minimum_area=minimum_area)
                    self.graph.edge_attribute(edge, name="contacts", value=contacts)

    # =============================================================================
    # Other Methods
    # =============================================================================

    def element_nnbrs(self, element: Element, k=1) -> list[tuple[Element, float]]:
        """Find the nearest neighbours to a root element.

        Parameters
        ----------
        element : :class:`Element`
            The root element.
        k : int, optional
            The number of nearest neighbours that should be returned.

        Returns
        -------
        list[tuple[Element, float]]
            A list of nearest neighbours,
            with each neighbour defined as an element and the distance of that element to the root element.

        """
        return [nbr for nbr in self.point_nnbrs(element.point, k=k + 1) if nbr[0] is not element]

    def point_nnbrs(self, point, k=1) -> list[tuple[Element, float]]:
        """Find the nearest neighbours to a point.

        Parameters
        ----------
        point : :class:`compas.geometry.Point`
            The root point.
        k : int, optional
            The number of nearest neighbours that should be returned.

        Returns
        -------
        list[tuple[Element, float]]
            A list of nearest neighbours,
            with each neighbour defined as an element and the distance of that element to the root element.

        """
        if k == 1:
            return [self.kdtree.nearest_neighbor(point)]
        return self.kdtree.nearest_neighbors(point, number=k)
