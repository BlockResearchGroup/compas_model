from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from enum import IntFlag
from enum import auto
from itertools import combinations
from typing import Literal
from typing import Optional
from typing import TypeVar
from typing import Union
from typing import cast

from compas.datastructures import Datastructure
from compas.datastructures import Graph
from compas.datastructures import Mesh
from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Transformation
from compas_model.elements import CollisionGeometryStage
from compas_model.elements import Element
from compas_model.elements import Group
from compas_model.geometry import is_geometry_empty
from compas_model.interactions import Contact
from compas_model.interactions import ContactRecord
from compas_model.interactions import InteractionRecord
from compas_model.interactions import ModifierRecord
from compas_model.materials import Material
from compas_model.modifiers import Modifier

from .bvh import ElementAABBNode
from .bvh import ElementBVH
from .bvh import ElementOBBNode
from .collection import Collection
from .elementtree import ElementNode

ElementType = TypeVar("ElementType", bound=Element)
ModelUnit = Literal["M", "MM"]
MODEL_UNITS = frozenset({"M", "MM"})


class _GeometryInvalidationScope(IntFlag):
    """Stages invalidated while following geometry dependencies."""

    FINAL = 0
    BASE = auto()
    LOCAL = auto()
    MODEL = auto()
    TRANSFORMATION = auto()
    DESCENDANTS = auto()


class ModelError(Exception):
    pass


class ModelElementNotFound(ModelError):
    pass


class Model(Datastructure):
    """Class representing a general model of hierarchically organised elements, with interactions.

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
        data = {
            "unit": self.unit,
            "transformation": self.transformation,
            "elements": self._elements,
            "materials": self._materials,
            "collections": self._collections,
            "interactions": self._interactions,
            "hierarchy": self._hierarchy_data(),
        }
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "Model":
        model = cls(unit=data.get("unit", "M"))

        model._transformation = data["transformation"]
        model._materials = data["materials"]
        elements = data["elements"]
        collections = data.get("collections", {})
        interactions = data.get("interactions", {})
        hierarchy = data["hierarchy"] if "hierarchy" in data else cls._legacy_hierarchy_data(data["tree"])

        added: set[str] = set()
        for entry in hierarchy:
            guid = cast(str, entry["element"])
            if guid in added:
                raise ValueError(f"Element appears more than once in the hierarchy: {guid!r}.")
            try:
                element = elements[guid]
            except KeyError:
                raise ValueError(f"Hierarchy references unknown element GUID: {guid!r}.") from None
            parent_guid = cast(str | None, entry.get("parent"))
            if parent_guid is not None and parent_guid not in added:
                raise ValueError(f"Hierarchy parent should precede its children: {parent_guid!r}.")
            parent = model.element_by_guid(parent_guid) if parent_guid is not None else None
            model.add_element(element, parent=parent)
            element.treenode.name = entry.get("name")
            element.treenode.attributes.update(entry.get("attributes") or {})
            added.add(guid)

        missing = set(elements) - added
        if missing:
            raise ValueError(f"Elements are missing from the hierarchy: {sorted(missing)!r}.")

        for collection in collections.values():
            model.add_collection(collection)

        for record in interactions.values():
            model._add_interaction_record(record)

        return model

    def __init__(self, name: Optional[str] = None, unit: ModelUnit = "M", **kwargs: object) -> None:
        super().__init__(name=name)

        self._unit: ModelUnit = "M"
        self.unit = unit
        self._transformation = None
        self._materials: dict[str, Material] = {}
        self._elements: dict[str, Element] = {}
        self._collections: dict[str, Collection] = {}
        self._interactions: dict[str, InteractionRecord] = {}

        self._tree = Tree()
        self._tree.add(TreeNode(name="root"))
        self._graph = Graph()
        self._graph.update_default_edge_attributes(record_ids=None)

        self._bvh = None
        self._model_bvh = None

    def _hierarchy_data(self) -> list[dict[str, object]]:
        """Return the hierarchy as ordered element relationships."""
        hierarchy: list[dict[str, object]] = []

        def visit(node: ElementNode, parent: str | None) -> None:
            guid = str(node.element.guid)
            hierarchy.append(
                {
                    "element": guid,
                    "parent": parent,
                    "name": node.name,
                    "attributes": node.attributes,
                }
            )
            for child in node.children:
                visit(child, guid)

        root = self.tree.root
        if root is None:
            raise RuntimeError("The model hierarchy has no root node.")
        for child in root.children:
            visit(child, None)
        return hierarchy

    @staticmethod
    def _legacy_hierarchy_data(data: dict) -> list[dict[str, object]]:
        """Normalize the former nested tree representation."""
        hierarchy: list[dict[str, object]] = []

        def visit(node: dict, parent: str | None) -> None:
            guid = node["element"]
            hierarchy.append(
                {
                    "element": guid,
                    "parent": parent,
                    "name": node.get("name"),
                    "attributes": node.get("attributes") or {},
                }
            )
            for child in node.get("children", []):
                visit(child, guid)

        for child in data["root"].get("children", []):
            visit(child, None)
        return hierarchy

    def __str__(self) -> str:
        output = "=" * 80 + "\n"
        output += "Spatial Hierarchy\n"
        output += "=" * 80 + "\n"
        output += str(self._tree) + "\n"
        output += "=" * 80 + "\n"
        output += "Element Interactions\n"
        output += "=" * 80 + "\n"
        output += str(self._graph) + "\n"
        output += "=" * 80 + "\n"
        return output

    # =============================================================================
    # Attributes
    # =============================================================================

    @property
    def unit(self) -> ModelUnit:
        """ModelUnit: Length unit used by model coordinate values."""
        return self._unit

    @unit.setter
    def unit(self, unit: str) -> None:
        normalized = unit.upper()
        if normalized not in MODEL_UNITS:
            raise ValueError(f"Unsupported model length unit: {unit!r}.")
        self._unit = cast(ModelUnit, normalized)

    @property
    def tree(self) -> Tree:
        return self._tree

    @property
    def graph(self) -> Graph:
        return self._graph

    @property
    def bvh(self) -> ElementBVH:
        return self.bvh_for("final")

    def bvh_for(self, geometry_stage: CollisionGeometryStage = "final") -> ElementBVH:
        """Return the cached BVH for a collision geometry stage.

        Parameters
        ----------
        geometry_stage
            ``"model"`` for transformed geometry before modifiers or
            ``"final"`` for fully evaluated geometry.

        Returns
        -------
        ElementBVH
            Spatial index built from the requested geometry stage.

        """
        if geometry_stage == "model":
            if self._model_bvh is None:
                self._model_bvh = self.compute_bvh(geometry_stage="model")
            return self._model_bvh
        if geometry_stage == "final":
            if self._bvh is None:
                self._bvh = self.compute_bvh(geometry_stage="final")
            return self._bvh
        raise ValueError(f"Unsupported collision geometry stage: {geometry_stage!r}.")

    @property
    def transformation(self) -> Optional[Transformation]:
        return self._transformation

    @transformation.setter
    def transformation(self, transformation: Transformation) -> None:
        self._transformation = transformation
        self._invalidate_computed_geometry()

    def _invalidate_spatial_indices(self, *, model: bool = True, final: bool = True) -> None:
        """Invalidate cached spatial acceleration structures."""
        if model:
            self._model_bvh = None
        if final:
            self._bvh = None

    def _invalidate_computed_geometry(self) -> None:
        """Invalidate element geometry caches and spatial indices."""
        self._propagate_geometry_invalidation(
            self.elements(),
            include_model=True,
            include_transformation=True,
        )

    def _propagate_geometry_invalidation(
        self,
        elements: Iterable[Element],
        *,
        include_descendants: bool = False,
        include_base: bool = False,
        include_local: bool = False,
        include_model: bool = False,
        include_transformation: bool = False,
    ) -> None:
        """Invalidate selected elements and their modifier dependants.

        Parameters
        ----------
        elements
            Elements whose derived geometry is stale.
        include_descendants
            If ``True``, include hierarchy descendants whose model
            transformations depend on the selected elements.
        include_base
            Clear geometry generated from the selected elements' definitions.
        include_local
            If ``True``, clear feature-evaluated local geometry for the
            selected elements.
        include_model
            If ``True``, clear transformed, unmodified model geometry for the
            selected elements.
        include_transformation
            If ``True``, clear model transformations for the selected
            elements.

        Notes
        -----
        The invalidation scope changes as dependencies are followed. Hierarchy
        descendants retain local geometry but lose their model transformation
        and final geometry. Modifier targets retain both local geometry and
        their model transformation, and lose only final geometry. Therefore
        each pending element carries its current scope rather than sharing the
        initial method options.

        An element can be reached through more than one dependency path. Its
        scopes are combined before caches are cleared so its geometry revision
        increases only once. Directed modifier dependencies are followed
        transitively. Cycles are safe because each element's outgoing modifier
        dependencies and hierarchy descendants are expanded at most once.

        """
        initial_scope = _GeometryInvalidationScope.FINAL
        if include_base:
            initial_scope |= _GeometryInvalidationScope.BASE
        if include_local:
            initial_scope |= _GeometryInvalidationScope.LOCAL
        if include_model:
            initial_scope |= _GeometryInvalidationScope.MODEL
        if include_transformation:
            initial_scope |= _GeometryInvalidationScope.TRANSFORMATION
        if include_descendants:
            initial_scope |= _GeometryInvalidationScope.DESCENDANTS

        pending = [(element, initial_scope) for element in elements]
        affected: dict[str, tuple[Element, _GeometryInvalidationScope]] = {}
        expanded_descendants: set[str] = set()
        expanded_modifiers: set[str] = set()

        while pending:
            element, scope = pending.pop()
            guid = str(element.guid)
            current = affected.get(guid)
            if current is None:
                affected[guid] = (element, scope)
            else:
                affected[guid] = (element, current[1] | scope)

            if scope & _GeometryInvalidationScope.DESCENDANTS and guid not in expanded_descendants:
                expanded_descendants.add(guid)
                descendant_scope = _GeometryInvalidationScope.MODEL | _GeometryInvalidationScope.TRANSFORMATION | _GeometryInvalidationScope.DESCENDANTS
                pending.extend((child, descendant_scope) for child in element.children)

            if guid not in expanded_modifiers:
                expanded_modifiers.add(guid)
                pending.extend(
                    (self.element_by_guid(record.target), _GeometryInvalidationScope.FINAL)
                    for record in self._interactions.values()
                    if isinstance(record, ModifierRecord) and record.source == guid
                )

        for element, scope in affected.values():
            element._clear_geometry_cache(
                base=bool(scope & _GeometryInvalidationScope.BASE),
                local=bool(scope & _GeometryInvalidationScope.LOCAL),
                model=bool(scope & _GeometryInvalidationScope.MODEL),
                transformation=bool(scope & _GeometryInvalidationScope.TRANSFORMATION),
            )
        invalidate_model_bvh = any(
            scope & (_GeometryInvalidationScope.BASE | _GeometryInvalidationScope.LOCAL | _GeometryInvalidationScope.MODEL) for _, scope in affected.values()
        )
        self._invalidate_spatial_indices(model=invalidate_model_bvh)

    # =============================================================================
    # Datastructure "abstract" methods
    # =============================================================================

    def transform(self, transformation: Transformation) -> None:
        """Transform the model and all that it contains.

        Parameters
        ----------
        transformation
            The transformation to apply.

        """
        self.transformation = transformation

    # =============================================================================
    # Elements
    # =============================================================================

    def elements(self) -> Iterator[Element]:
        """Iterate over the elements contained in the model.

        Returns
        -------
        Iterator[Element]
            The elements contained in the model.

        """
        return iter(self._elements.values())

    def element_by_guid(self, guid: str) -> Element:
        """Return the model element with the requested GUID."""
        try:
            return self._elements[guid]
        except KeyError:
            raise ModelElementNotFound(f"Unknown element GUID: {guid!r}.") from None

    def add_element(
        self,
        element: Union[Element, ElementType],
        parent: Optional[Element] = None,
        material: Optional[Material] = None,
    ) -> Union[Element, ElementType]:
        """Add an element to the model.

        Parameters
        ----------
        element
            The element to add.
        parent
            The parent element of the element.
            If ``None``, the element will be added directly under the root element.
        material
            A material to assign to the element.
            Note that the material should have already been added to the model before it can be assigned.

        Returns
        -------
        Element
            The element added to the model.

        Raises
        ------
        ValueError
            If the element already belongs to a model, its GUID is already in
            this model, the parent does not belong to this model, or the
            material is not part of this model.

        """
        guid = str(element.guid)
        if guid in self._elements:
            raise ValueError("An element with this GUID is already part of the model.")
        if getattr(element, "model", None) is not None:
            raise ValueError("The element already belongs to a model.")
        if parent is not None and not self.has_element(parent):
            raise ValueError("The parent element is not part of the model.")

        if material and not self.has_material(material):
            raise ValueError("The material is not part of the model: {}".format(material))

        parentnode = self.tree.root if parent is None else parent.treenode
        if parentnode is None:
            raise RuntimeError("The model hierarchy has no root node.")
        treenode = ElementNode(element=element)

        self._invalidate_spatial_indices()
        self.graph.add_node(key=guid)
        self.tree.add(treenode, parent=parentnode)

        self._elements[guid] = element
        element.model = self
        element.graphnode = guid
        element.treenode = treenode

        if material:
            self.assign_material(material=material, element=element)

        return element

    def add_elements(
        self,
        elements: list[ElementType],
        parent: Optional[Element] = None,
        material: Optional[Material] = None,
    ) -> list[ElementType]:
        """Add a list of elements to the model.

        Parameters
        ----------
        elements
            The elements to add.
        parent
            The parent element of the elements.
            If ``None``, the elements will be added directly under the root element.
        material
            A material to assign to the elements.
            Note that the material should have already been added to the model before it can be assigned.

        Returns
        -------
        list[Element]
            The list of elements added to the model.

        Raises
        ------
        ValueError
            If any element already belongs to a model, has a duplicate GUID,
            the parent is not part of this model, or the material is not part
            of this model.

        """
        for element in elements:
            self.add_element(element, parent, material)
        return elements

    def remove_element(self, element: Element) -> None:
        """Remove an element from the model.

        Parameters
        ----------
        element
            The element to remove.

        Raises
        ------
        ValueError
            If the element is not part of the model or has hierarchy children.

        Notes
        -----
        Removal is deliberately leaf-only. Reparent or explicitly remove an
        element's children before removing their parent.

        """
        guid = str(element.guid)
        if not self.has_element(element):
            raise ValueError("The element is not part of the model.")
        if element.children:
            raise ValueError("An element with children cannot be removed.")

        for record in list(self.interaction_records()):
            if guid in {record.element_a, record.element_b}:
                self.remove_interaction_record(record)
        del self._elements[guid]
        for collection in self._collections.values():
            collection.remove_element(element)
        self._invalidate_spatial_indices()

        self.graph.delete_node(element.graphnode)
        self.tree.remove(element.treenode)
        element.model = None  # type: ignore
        element.graphnode = None  # type: ignore
        element.treenode = None  # type: ignore

    def reparent_element(self, element: Element, parent: Optional[Element] = None) -> None:
        """Move an element and its subtree to a different hierarchy parent.

        Parameters
        ----------
        element
            Element to move.
        parent
            New parent element. If ``None``, move the element directly below
            the model root.

        Raises
        ------
        ValueError
            If either element is not part of the model, the element is its own
            parent, or the move would create a hierarchy cycle.

        Notes
        -----
        Reparenting preserves sibling order outside the moved subtree and
        appends the element after the new parent's existing children. The
        element, its descendants, and transitive modifier dependants receive
        targeted placement invalidation.

        """
        if not self.has_element(element):
            raise ValueError("The element is not part of the model.")
        if parent is not None and not self.has_element(parent):
            raise ValueError("The parent element is not part of the model.")
        if parent is element:
            raise ValueError("An element cannot be its own parent.")

        ancestor = parent
        while ancestor is not None:
            if ancestor is element:
                raise ValueError("Reparenting would create a hierarchy cycle.")
            ancestor = ancestor.parent

        parentnode = self.tree.root if parent is None else parent.treenode
        if parentnode is None:
            raise RuntimeError("The model hierarchy has no root node.")
        if element.treenode.parent is parentnode:
            return

        self.tree.remove(element.treenode)
        self.tree.add(element.treenode, parent=parentnode)
        self._propagate_geometry_invalidation(
            [element],
            include_descendants=True,
            include_local=False,
            include_model=True,
            include_transformation=True,
        )

    def has_element(self, element: Element) -> bool:
        """Returns True if the model contains the given element.

        Parameters
        ----------
        element
            The element to check.

        Returns
        -------
        bool
            True if the model contains the element.

        """
        guid = str(element.guid)
        return self._elements.get(guid) is element

    def has_element_with_name(self, name: str) -> bool:
        """Returns True if the model contains an element with the given name.

        Parameters
        ----------
        name
            The name to check.

        Returns
        -------
        bool
            True if the model contains an element with the name.

        """
        return any(element.name == name for element in self.elements())

    def find_element_with_name(self, name: str) -> Optional[Element]:
        """Returns True if the model contains an element with the given name.

        Parameters
        ----------
        name
            The name to check.

        Returns
        -------
        Element or None
            The element with the name, if found.

        """
        for element in self.elements():
            if element.name == name:
                return element

    def find_element_with_name_or_fail(self, name: str) -> Element:
        element = self.find_element_with_name(name)
        if not element:
            raise ModelElementNotFound
        return element

    def find_all_elements_of_type(self, elementtype: type[Element]) -> list[Element]:
        """Find all model elements of a given type.

        Parameters
        ----------
        elementtype
            The type of element.

        Returns
        -------
        list[Element]
            The elements of the requested type.

        """
        elements = []
        for element in self.elements():
            if isinstance(element, elementtype):
                elements.append(element)
        return elements

    def remove_elements_of_type(self, elementtype: type[Element]) -> list[Element]:
        """Remove all model elements of a given type.

        Parameters
        ----------
        elementtype
            The type of element.

        Returns
        -------
        list[Element]
            The removed elements.

        Raises
        ------
        ValueError
            If a matching element has a child that does not also match the
            requested type.

        """
        elements = self.find_all_elements_of_type(elementtype)
        selected = {str(element.guid) for element in elements}
        if any(str(child.guid) not in selected for element in elements for child in element.children):
            raise ValueError("Cannot remove elements of this type while they contain non-matching children.")

        def depth(element: Element) -> int:
            count = 0
            node = element.treenode
            while node.parent is not None and not node.parent.is_root:
                count += 1
                node = node.parent
            return count

        for element in sorted(elements, key=depth, reverse=True):
            self.remove_element(element)
        return elements

    # =============================================================================
    # Groups
    # =============================================================================

    def add_group(self, name: Optional[str] = None) -> Group:
        """Add a group to the model.

        Parameters
        ----------
        name
            The name of the group.

        Returns
        -------
        Group
            The group added to the model.

        """
        group = Group(name=name)
        self.add_element(group)
        return group

    # =============================================================================
    # Collections
    # =============================================================================

    def collections(self) -> Iterator[Collection]:
        """Iterate over non-hierarchical element collections."""
        return iter(self._collections.values())

    def add_collection(self, collection: Collection | str, attributes: Optional[dict[str, object]] = None) -> Collection:
        """Add a collection or create one from a name."""
        if isinstance(collection, str):
            collection = Collection(name=collection, attributes=attributes)
        elif attributes is not None:
            raise ValueError("Attributes can only be supplied when creating a collection by name.")
        guid = str(collection.guid)
        if guid in self._collections:
            raise ValueError("Collection already in the model.")
        if collection.model is not None and collection.model is not self:
            raise ValueError("Collection already belongs to another model.")
        unknown = set(collection.element_guids) - set(self._elements)
        if unknown:
            raise ValueError(f"Collection references unknown element GUIDs: {sorted(unknown)!r}.")
        collection.model = self
        self._collections[guid] = collection
        return collection

    def remove_collection(self, collection: Collection) -> None:
        """Remove a collection without removing its member elements."""
        guid = str(collection.guid)
        if self._collections.get(guid) is not collection:
            raise ValueError("Collection is not part of the model.")
        del self._collections[guid]
        collection.model = None

    def find_collection_with_name(self, name: str) -> Optional[Collection]:
        """Return the first collection with the requested name."""
        return next((collection for collection in self._collections.values() if collection.name == name), None)

    def collections_for_element(self, element: Element) -> list[Collection]:
        """Return all collections containing an element."""
        if not self.has_element(element):
            raise ValueError("The element is not part of the model.")
        return [collection for collection in self._collections.values() if collection.has_element(element)]

    # =============================================================================
    # Materials
    # =============================================================================

    def materials(self) -> Iterator[Material]:
        """Iterate over the materials stored in the model.

        Returns
        -------
        Iterator[Material]
            The materials stored in the model.

        """
        return iter(self._materials.values())

    def add_material(self, material: Material) -> None:
        """Add a material to the model.

        Parameters
        ----------
        material
            A material.

        """
        guid = str(material.guid)
        if guid in self._materials:
            raise Exception("Material already in the model.")

        self._materials[guid] = material

    def has_material(self, material: Material) -> bool:
        """Verify that the model contains a specific material.

        Parameters
        ----------
        material
            A model material.

        Returns
        -------
        bool
            True if the model contains the material.

        """
        guid = str(material.guid)
        return guid in self._materials

    def add_or_get_material(self, material: Material) -> Material:
        """Add a material to the model or retrieve an existing instance of the same type.

        Parameters
        ----------
        material
            A material.

        Returns
        -------
        Material
            The added or existing material.

        """
        for existing in self.materials():
            if isinstance(existing, type(material)):
                return existing
        self.add_material(material)
        return material

    def assign_material(
        self,
        material: Material,
        element: Optional[Element] = None,
        elements: Optional[list[Element]] = None,
    ) -> None:
        """Assign a material to an element or a list of elements.

        Parameters
        ----------
        material
            The material.
        element
            The element to assign the material to.
        elements
            The list of elements to assign the material to.

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
    # Other models
    # =============================================================================

    def set_contacts(self, a: Element, b: Element, contacts: list[Contact]) -> ContactRecord | None:
        """Replace the computed contacts stored between two elements.

        Parameters
        ----------
        a
            The first element.
        b
            The second element.
        contacts
            The replacement contact regions. An empty list removes the contact
            record without affecting other interactions between the pair.

        Returns
        -------
        ContactRecord or None
            The new record, or ``None`` when no contacts were supplied.

        Raises
        ------
        ValueError
            If either element is not part of the model or both arguments refer
            to the same element.

        """
        for record in list(self.interaction_records_between(a, b)):
            if isinstance(record, ContactRecord):
                self.remove_interaction_record(record)
        if not contacts:
            return None
        return cast(ContactRecord, self._add_interaction_record(ContactRecord(str(a.guid), str(b.guid), contacts)))

    # =============================================================================
    # Interactions
    # =============================================================================

    def interaction_records(self) -> Iterator[InteractionRecord]:
        """Iterate over managed interaction records in insertion order."""
        return iter(self._interactions.values())

    def interaction_records_between(self, a: Element, b: Element) -> list[InteractionRecord]:
        """Return interaction records between two model elements.

        Raises
        ------
        ValueError
            If either element is not part of the model or both arguments refer
            to the same element.

        """
        self._validate_interaction_elements(a, b)
        guids = {str(a.guid), str(b.guid)}
        return [record for record in self._interactions.values() if {record.element_a, record.element_b} == guids]

    def contact_records(self) -> Iterator[ContactRecord]:
        """Iterate over computed contact records."""
        return (record for record in self._interactions.values() if isinstance(record, ContactRecord))

    def contact_records_between(self, a: Element, b: Element) -> list[ContactRecord]:
        """Return contact records between two model elements.

        Raises
        ------
        ValueError
            If either element is not part of the model or both arguments refer
            to the same element.

        """
        return [record for record in self.interaction_records_between(a, b) if isinstance(record, ContactRecord)]

    def modifier_records(self) -> Iterator[ModifierRecord]:
        """Iterate over directed modifier records."""
        return (record for record in self._interactions.values() if isinstance(record, ModifierRecord))

    def modifier_records_between(self, a: Element, b: Element) -> list[ModifierRecord]:
        """Return modifier records between two model elements.

        Raises
        ------
        ValueError
            If either element is not part of the model or both arguments refer
            to the same element.

        """
        return [record for record in self.interaction_records_between(a, b) if isinstance(record, ModifierRecord)]

    def modifier_records_for(self, target: Element) -> list[ModifierRecord]:
        """Return directed modifier records targeting an element.

        Raises
        ------
        ValueError
            If `target` is not part of the model.

        """
        if not self.has_element(target):
            raise ValueError("The target element is not part of the model.")
        guid = str(target.guid)
        return sorted((record for record in self.modifier_records() if record.target == guid), key=lambda record: record.order)

    def reorder_modifier_records(self, target: Element, records: Sequence[ModifierRecord]) -> None:
        """Set the evaluation order of all modifiers targeting an element.

        Parameters
        ----------
        target
            Target element whose complete modifier sequence is being ordered.
        records
            Every modifier record targeting the element, in evaluation order.

        Raises
        ------
        ValueError
            If `target` is not part of the model, a record is duplicated, or
            `records` is not exactly the target's current modifier records.

        """
        current = self.modifier_records_for(target)
        requested = list(records)
        requested_guids = [str(record.guid) for record in requested]
        if len(requested_guids) != len(set(requested_guids)):
            raise ValueError("Modifier records cannot be duplicated in the evaluation order.")
        if set(requested_guids) != {str(record.guid) for record in current}:
            raise ValueError("The evaluation order should contain every modifier record targeting the element exactly once.")
        for order, record in enumerate(requested):
            record._set_order(order)
        self._propagate_geometry_invalidation([target], include_local=False)

    def replace_modifier(self, record: ModifierRecord, modifier: Modifier) -> None:
        """Replace the operation of a managed modifier record.

        Parameters
        ----------
        record
            Managed record whose operation should be replaced.
        modifier
            Replacement operation.

        Raises
        ------
        ValueError
            If `record` is not owned by the model.

        Notes
        -----
        Replacing the modifier invalidates final geometry for its target and
        transitive downstream modifier targets. Use this operation instead of
        mutating modifier parameters in place so the model can update its
        caches.

        """
        if self._interactions.get(str(record.guid)) is not record or not isinstance(record, ModifierRecord):
            raise ValueError("Modifier record is not part of the model.")
        record._set_modifier(modifier)
        self._propagate_geometry_invalidation([self.element_by_guid(record.target)], include_local=False)

    def add_interaction(self, a: Element, b: Element) -> InteractionRecord:
        """Add an interaction between two elements of the model.

        Parameters
        ----------
        a
            The first element.
        b
            The second element.

        Returns
        -------
        InteractionRecord
            The managed interaction record.

        Raises
        ------
        ValueError
            If either element is not in the model or both arguments refer to
            the same element.

        """
        self._validate_interaction_elements(a, b)
        for record in self.interaction_records_between(a, b):
            if type(record) is InteractionRecord:
                return record
        return self._add_interaction_record(InteractionRecord(str(a.guid), str(b.guid)))

    def remove_interaction(self, a: Element, b: Element) -> None:
        """Remove the interaction between two elements.

        Parameters
        ----------
        a
            The first element.
        b
            The second element.

        Raises
        ------
        ValueError
            If either element is not part of the model or both arguments refer
            to the same element.

        """
        for record in list(self.interaction_records_between(a, b)):
            if type(record) is InteractionRecord:
                self.remove_interaction_record(record)

    def remove_interaction_record(self, record: InteractionRecord) -> None:
        """Remove one managed record without affecting other pair data.

        Raises
        ------
        ValueError
            If `record` is not owned by the model.

        """
        guid = str(record.guid)
        if self._interactions.get(guid) is not record:
            raise ValueError("Interaction record is not part of the model.")
        a = self.element_by_guid(record.element_a)
        b = self.element_by_guid(record.element_b)
        edge = self._interaction_edge(a, b)
        modifier_target = self.element_by_guid(record.target) if isinstance(record, ModifierRecord) else None
        del self._interactions[guid]
        if edge is not None:
            record_ids: list[str] = list(self.graph.edge_attribute(edge, name="record_ids") or ())
            record_ids.remove(guid)
            if record_ids:
                self.graph.edge_attribute(edge, name="record_ids", value=record_ids)
            else:
                self.graph.delete_edge(edge)
        if modifier_target is not None:
            for order, remaining in enumerate(self.modifier_records_for(modifier_target)):
                remaining._set_order(order)
            self._propagate_geometry_invalidation([modifier_target], include_local=False)

    def has_interaction(self, a: Element, b: Element) -> bool:
        """Returns True if two elements have an interaction set between them.

        Parameters
        ----------
        a
            The first element.
        b
            The second element.

        Returns
        -------
        bool
            True if the elements have an interaction.

        Raises
        ------
        ValueError
            If either element is not part of the model or both arguments refer
            to the same element.

        """
        self._validate_interaction_elements(a, b)
        return self._interaction_edge(a, b) is not None

    def _validate_interaction_elements(self, a: Element, b: Element) -> None:
        if a is b:
            raise ValueError("An element cannot interact with itself.")
        if not self.has_element(a) or not self.has_element(b):
            raise ValueError("Both elements should be part of the model.")

    def _interaction_edge(self, a: Element, b: Element) -> tuple[str, str] | None:
        edge = a.graphnode, b.graphnode
        if self.graph.has_edge(edge):
            return edge
        reverse = b.graphnode, a.graphnode
        if self.graph.has_edge(reverse):
            return reverse
        return None

    def _add_interaction_record(self, record: InteractionRecord) -> InteractionRecord:
        if str(record.guid) in self._interactions:
            raise ValueError("Interaction record is already part of the model.")
        a = self.element_by_guid(record.element_a)
        b = self.element_by_guid(record.element_b)
        self._validate_interaction_elements(a, b)
        edge = self._interaction_edge(a, b) or self.graph.add_edge(a.graphnode, b.graphnode)
        record_ids: list[str] = list(self.graph.edge_attribute(edge, name="record_ids") or ())
        record_ids.append(str(record.guid))
        self.graph.edge_attribute(edge, name="record_ids", value=record_ids)
        self._interactions[str(record.guid)] = record
        return record

    # =============================================================================
    # Modifiers (temp)
    # =============================================================================

    def add_modifier(
        self,
        source: Element,
        target: Element,
        modifier: Modifier,
    ) -> ModifierRecord:
        """Add a modifier between two elements, with one the source of the modifier and the other the target.

        Parameters
        ----------
        source
            The source element.
        target
            The target element.
        modifier
            The modifier.

        Returns
        -------
        ModifierRecord
            The managed directed modifier record.

        Raises
        ------
        ValueError
            If either element is not part of the model or both arguments refer
            to the same element, or the modifier would create a dependency
            cycle.

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
        self._validate_interaction_elements(source, target)
        if self._has_modifier_path(target, source):
            raise ValueError("The modifier would create a cyclic geometry dependency.")
        existing = self.modifier_records_for(target)
        order = max((record.order for record in existing), default=-1) + 1
        record = cast(ModifierRecord, self._add_interaction_record(ModifierRecord(str(source.guid), str(target.guid), modifier, order=order)))
        self._propagate_geometry_invalidation([target], include_local=False)
        return record

    def _has_modifier_path(self, source: Element, target: Element) -> bool:
        target_guid = str(target.guid)
        pending = [str(source.guid)]
        visited = set()
        while pending:
            guid = pending.pop()
            if guid == target_guid:
                return True
            if guid in visited:
                continue
            visited.add(guid)
            pending.extend(record.target for record in self.modifier_records() if record.source == guid)
        return False

    # =============================================================================
    # Compute
    # =============================================================================

    def collision_candidates(
        self,
        geometry_stage: CollisionGeometryStage = "final",
    ) -> Generator[tuple[Element, Element], None, None]:
        """Yield broad-phase collision candidates from the model elements.

        Parameters
        ----------
        geometry_stage
            ``"model"`` for transformed geometry before modifiers or
            ``"final"`` for fully evaluated geometry.

        Yields
        ------
        tuple[Element, Element]
            An unordered pair of elements with overlapping BVH leaf bounds.

        Notes
        -----
        Each unordered pair is yielded at most once and an element is never
        paired with itself. Candidate bounding volumes overlap, but the element
        geometries may not. Precise collision checks are required to reject
        broad-phase false positives.

        """
        bvh = self.bvh_for(geometry_stage)
        yield from bvh.overlap_elements(bvh, self_collision=True)

    def collisions(
        self,
        precision: str = "fast",
        tolerance: float = 0.0,
        include_touching: bool = True,
        geometry_stage: CollisionGeometryStage = "final",
    ) -> Generator[tuple[Element, Element], None, None]:
        """Yield colliding element pairs.

        Parameters
        ----------
        precision
            ``"fast"`` for conservative bounds or ``"precise"`` for
            representation-specific geometric collision.
        tolerance
            The maximum separation considered a collision.
        include_touching
            If ``True``, boundary contact is considered a collision.
        geometry_stage
            ``"model"`` for transformed geometry before modifiers or
            ``"final"`` for fully evaluated geometry.

        Yields
        ------
        tuple[Element, Element]
            An unordered pair of colliding elements.

        Notes
        -----
        The model BVH first removes pairs whose element AABBs do not overlap.
        Remaining pairs are dispatched to either precise mesh-surface or native
        Open CASCADE BRep collision. Mesh and BRep geometry are never mixed.

        """
        if precision not in {"fast", "precise"}:
            raise ValueError(f"Unsupported collision precision: {precision!r}.")
        if geometry_stage not in {"model", "final"}:
            raise ValueError(f"Unsupported collision geometry stage: {geometry_stage!r}.")
        if tolerance < 0:
            raise ValueError("The tolerance should be greater than or equal to zero.")

        candidates = combinations(self.elements(), 2) if tolerance > 0 else self.collision_candidates(geometry_stage=geometry_stage)
        for element_a, element_b in candidates:
            if element_a.is_collision(
                element_b,
                precision=precision,
                tolerance=tolerance,
                include_touching=include_touching,
                geometry_stage=geometry_stage,
            ):
                yield element_a, element_b

    def compute_bvh(
        self,
        nodetype: Union[type[ElementAABBNode], type[ElementOBBNode]] = ElementAABBNode,
        max_depth: Optional[int] = None,
        leafsize: int = 1,
        geometry_stage: CollisionGeometryStage = "final",
    ) -> ElementBVH:
        """Compute the Bounding Volume Hierarchy (BVH) of the elements for fast collision checks.

        Parameters
        ----------
        nodetype
            The type of bounding volume node used in the tree.
        max_depth
            The maximum depth used for constructing the BVH.
        leafsize
            The number of elements contained in a BVH leaf node.
        geometry_stage
            ``"model"`` for transformed geometry before modifiers or
            ``"final"`` for fully evaluated geometry.

        Returns
        -------
        ElementBVH
            The computed BVH.

        """
        if geometry_stage not in {"model", "final"}:
            raise ValueError(f"Unsupported collision geometry stage: {geometry_stage!r}.")

        bounds: Callable[[Element], Box] | None = None
        if geometry_stage == "model":

            def model_bounds(element: Element) -> Box:
                geometry = element.model_geometry
                if issubclass(nodetype, ElementOBBNode):
                    return geometry.obb() if isinstance(geometry, Mesh) else geometry.obb
                return geometry.aabb() if isinstance(geometry, Mesh) else geometry.aabb

            bounds = model_bounds
            elements = (element for element in self.elements() if not is_geometry_empty(element.model_geometry))
        else:
            elements = (element for element in self.elements() if not element.is_empty)
        bvh = ElementBVH.from_elements(
            elements,
            nodetype=nodetype,
            max_depth=max_depth,
            leafsize=leafsize,
            bounds=bounds,
        )
        if geometry_stage == "model":
            self._model_bvh = bvh
        else:
            self._bvh = bvh
        return bvh

    def compute_contacts(self, tolerance: float = 1e-6, minimum_area: float = 1e-2, contacttype: type[Contact] = Contact) -> None:
        """Compute the contacts between the block elements of this model.

        Computing contacts is done independently of the existing interaction
        edges. Derived contacts on existing edges are replaced atomically. An
        edge created by this method is removed when its contact disappears,
        unless it has subsequently acquired modifiers. Explicit interaction
        edges are always preserved.

        The search is conducted entirely based on the BVH of the elements contained in the model.
        It is a spatial search that creates topological connections between elements based on their geometrical interaction.

        Parameters
        ----------
        tolerance
            The distance tolerance.
        minimum_area
            The minimum contact size.
        contacttype
            The contact class to use for the generated contacts.

        Raises
        ------
        ValueError
            If ``tolerance`` or ``minimum_area`` is negative.

        Notes
        -----
        Broad-phase candidates are found by expanding each element AABB by the
        absolute ``tolerance``. Mesh-to-mesh and BRep-to-BRep pairs are
        evaluated separately; mixed representation pairs are ignored.

        All contact geometry is computed before the interaction graph is
        changed. If one computation fails, the graph remains unchanged.

        """
        if tolerance < 0:
            raise ValueError("The tolerance should be greater than or equal to zero.")
        if minimum_area < 0:
            raise ValueError("The minimum area should be greater than or equal to zero.")

        elements = list(self.elements())
        element_index = {id(element): index for index, element in enumerate(elements)}
        results: dict[tuple[str, str], list[Contact]] = {}

        for index, element in enumerate(elements):
            if element.is_empty:
                continue
            for neighbor in self.bvh.nearby_elements(element, tolerance=tolerance):
                neighbor_index = element_index[id(neighbor)]
                if neighbor_index <= index:
                    continue

                geometry_a = element.final_geometry
                geometry_b = neighbor.final_geometry
                is_mesh_pair = isinstance(geometry_a, Mesh) and isinstance(geometry_b, Mesh)
                is_brep_pair = isinstance(geometry_a, Brep) and isinstance(geometry_b, Brep)
                if not (is_mesh_pair or is_brep_pair):
                    continue

                contacts = element.compute_contacts(
                    neighbor,
                    tolerance=tolerance,
                    minimum_area=minimum_area,
                    contacttype=contacttype,
                )
                results[element.graphnode, neighbor.graphnode] = contacts

        for record in list(self.contact_records()):
            self.remove_interaction_record(record)

        for (u, v), contacts in results.items():
            if contacts:
                a = self.element_by_guid(u)
                b = self.element_by_guid(v)
                self.set_contacts(a, b, contacts)
