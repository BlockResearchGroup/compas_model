from typing import TYPE_CHECKING
from typing import Optional

from compas.datastructures import TreeNode
from compas_model.elements import Element

if TYPE_CHECKING:
    from .elementtree import ElementTree


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
