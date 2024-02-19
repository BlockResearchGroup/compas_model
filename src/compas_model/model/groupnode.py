from compas.datastructures import TreeNode
from .elementnode import ElementNode  # noqa: F401


class GroupNode(TreeNode):
    """Class representing nodes containing elements in an element tree.

    Parameters
    ----------
    name : str
        The name of the group node.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "children": [child.__data__ for child in self.children],
            "name": self.name,
        }

    @classmethod
    def __from_data__(cls, data):
        raise ValueError(
            "GroupNode objects should only be serialised through a Model object."
        )

    def __init__(self, name):
        # type: (str) -> None
        super(GroupNode, self).__init__(name=name)

    def __getitem__(self, index):
        # type: (int) -> GroupNode | ElementNode
        return self.children[index]
