import compas.geometry  # noqa: F401
from compas.datastructures import TreeNode
from .elementnode import ElementNode  # noqa: F401


class GroupNode(TreeNode):
    """Class representing nodes containing elements in an element tree.

    A group node can contain other group nodes and/or element nodes.
    A group node never contains elements directly.
    A group node can have a frame, which is then the reference frame for all descendants.
    A group node always has a name, but the name is not required to be unique.
    A group node can have (arbitrary) additional attributes.

    Parameters
    ----------
    name : str
        The name of the group node.

    """

    DATASCHEMA = {
        "type": "object",
        "$recursiveAnchor": True,
        "properties": {
            "name": {"type": "str"},
            "frame": compas.geometry.Frame.DATASCHEMA,
            "attributes": {"type": "object"},
            "children": {
                "type": "array",
                "items": {"$recursiveRef": "#"},
            },  # in this case this is not correct, because a child can also be an element node
        },
        "required": ["name", "frame", "attributes", "children"],
    }

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "name": self.name,
            "frame": self.frame,
            "attributes": self.attributes,
            "children": [child.__data__ for child in self.children],
        }

    @classmethod
    def __from_data__(cls, data):
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, name, frame=None, attr=None, **kwargs):
        # type: (str, compas.geometry.Frame | None, dict | None, dict) -> None
        attr = attr or {}
        attr.update(kwargs)
        attr["name"] = name
        super(GroupNode, self).__init__(**attr)
        self._frame = frame

    def __getitem__(self, index):
        # type: (int) -> GroupNode | ElementNode
        return self.children[index]

    @property
    def frame(self):
        # type: () -> compas.geometry.Frame | None
        return self._frame

    @frame.setter
    def frame(self, frame):
        self._frame = frame
