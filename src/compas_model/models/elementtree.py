from typing import Optional
from typing import Union

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

    tree: "ElementTree"  # type: ignore

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["element"] = None if not self.element else str(self.element.guid)
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "ElementNode":
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, element: Element, **kwargs) -> None:
        super().__init__(**kwargs)
        self.element = element

    def __getitem__(self, index: int) -> "ElementNode":
        return self.children[index]

    def __repr__(self):
        return f"{self.element.__class__.__name__}(name={self.element.name})"


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

    root: ElementNode  # type: ignore

    @classmethod
    def __from_data__(cls, data: dict) -> "ElementTree":
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name=name)
        # unlike the default tree,
        # an element tree automatically adds a root node...
        root = TreeNode(name="root")
        self.add(root)

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
