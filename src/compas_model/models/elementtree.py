from typing import Optional

from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas_model.elements import Element


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

    tree: "ElementTree"

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["element"] = None if not self.element else str(self.element.guid)
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "ElementNode":
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, element: Optional[Element] = None, **kwargs) -> None:
        super().__init__(**kwargs)

        if element:
            element.treenode = self
        self.element = element

    def __getitem__(self, index: int) -> "ElementNode":
        return self.children[index]


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

    @property
    def __data__(self) -> dict:
        data = super().__data__
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "ElementTree":
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name=name)

        root = ElementNode(name="root")
        self.add(root)

    @property
    def elements(self) -> list[Element]:
        return [node.element for node in self.nodes if isinstance(node, ElementNode) if node.element]

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
