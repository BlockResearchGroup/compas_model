from compas.datastructures import TreeNode


class GroupNode(TreeNode):
    """A group node that is represented by a name and a geometry and a list of children


    Parameters
    ----------
    name : str, optional
        A name or identifier for the node.

    geometry : Any, optional
        Geometry or any other property, when you want to give a group a shape besides name.

    attributes : dict, optional
        A dictionary of additional attributes to be associated with the node.

    parent : Node, optional
        The parent node of this node.
        This input is required when the node is created separately (not by tree.add_group(...))
        After creation, the parent becomes the branch or sub-branch of the node.


    Attributes
    ----------
    geometry : Geometry, read-only
        The geometry of the node, if it is assigned.
    """

    def __init__(self, name=None, geometry=None, attributes=None, parent=None):

        super().__init__(name=name, attributes=attributes)

        # --------------------------------------------------------------------------
        # geometry of the group node
        # --------------------------------------------------------------------------
        self.attributes["my_object"] = geometry  # node stores the Element object

        # --------------------------------------------------------------------------
        # when a node is created separately, a user must define the parent node:
        # --------------------------------------------------------------------------
        self._parent = parent
        if parent is not None:
            self._tree = parent._tree

        # --------------------------------------------------------------------------
        # for debugging, the default name is the guid of th GroupNode
        # --------------------------------------------------------------------------
        self.name = name if name else str(self.guid)
