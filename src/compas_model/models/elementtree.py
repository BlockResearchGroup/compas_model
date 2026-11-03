from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas_model.elements import Element


class ElementNode(TreeNode):
    """Class representing nodes containing elements in an element tree.

    Parameters
    ----------
    element
        The element contained in the node.

    Notes
    -----
    This object will raise an Exception,
    when it is (de)serialised independently, outside the context of a Model.

    """

    tree: Tree  # type: ignore

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["element"] = None if not self.element else str(self.element.guid)
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "ElementNode":
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, element: Element, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.element = element

    def __getitem__(self, index: int) -> "ElementNode":
        return self.children[index]

    def __repr__(self) -> str:
        return f"{self.element.__class__.__name__}(name={self.element.name})"
