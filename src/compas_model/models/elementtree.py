from typing import TYPE_CHECKING
from typing import Optional
from typing import Union

from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas_model.elements import Element

if TYPE_CHECKING:
    from compas_model.models import Model


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

    tree: "ElementTree"  # type: ignore

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["element"] = self._element
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "ElementNode":
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, element: Optional[Element] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._element = None
        self.element = element

    @property
    def element(self):
        if self._element:
            return self.tree.model._elements[self._element]

    @element.setter
    def element(self, element: Optional[Union[Element, str]] = None) -> None:
        if isinstance(element, Element):
            self._element = str(element.guid)
        else:
            self._element = element

    def __getitem__(self, index: int) -> "ElementNode":
        return self.children[index]

    def __repr__(self):
        if self.parent:
            if not self.element:
                raise Exception("An element node that is not the root node should have an element.")
            return f"{self.element.__class__.__name__}(name={self.element.name})"
        else:
            return "ROOT"


class ElementTree(Tree):
    """Class representing the hierarchy of elements in a model through a tree.

    Parameters
    ----------
    model : :class:`compas_model.model.Model`
        The parent model of the element tree.
    name : str, optional
        The name of the tree.

    Attributes
    ----------
    model : :class:`compas_model.model.Model`
        The parent model of the tree.
    groups : list[:class:`GroupNode`], read-only
        The groups contained in the tree.
    elements : list[:class:`Element`], read-only
        The elements contained in the tree

    """

    model: "Model"

    @classmethod
    def __from_data__(cls, data: dict) -> "ElementTree":
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, model: "Model", name: Optional[str] = None) -> None:
        super().__init__(name=name)
        self.model = model
        root = ElementNode(name="root")
        self.add(root)

    @property
    def elements(self) -> list[Element]:
        return [node.element for node in self.nodes if isinstance(node, ElementNode) and node.element]

    @property
    def rootelements(self) -> list[Element]:
        if self.root:
            return [node.element for node in self.root.children if isinstance(node, ElementNode) and node.element]
        return []

    def add_element(self, element: Element, parent: Optional[Union[Element, ElementNode]] = None) -> ElementNode:
        if parent is None:
            parentnode = self.root
        elif isinstance(parent, Element):
            parentnode = parent.treenode
            if parentnode is None:
                raise ValueError("The parent element is not part of this model.")
        else:
            parentnode = parent

        treenode = ElementNode(element=element)
        element.treenode = treenode
        parentnode.add(treenode)  # type: ignore
        return treenode

    def find_element_node(self, element: Element) -> ElementNode:
        """Find the node containing the element.

        Parameters
        ----------
        element : :class:`compas_model.elements.Element`

        Returns
        -------
        :class:`compas_model.model.ElementNode`

        Raises
        ------
        ValueError
            If the element is not in the tree.

        """
        for node in self.nodes:
            if isinstance(node, ElementNode):
                if node.element is element:
                    return node
        raise ValueError("Element not in tree")
