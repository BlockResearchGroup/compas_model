import time
from typing import Generator
from typing import Optional
from typing import Type
from typing import Union

import compas
from compas.colors import Color
from compas.datastructures import Mesh
from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import centroid_points
from compas.geometry import oriented_bounding_box_numpy
from compas_model.algorithms.intersections import intersection_ray_triangle
from compas_model.algorithms.intersections import is_intersection_box_box
from compas_model.algorithms.intersections import is_intersection_line_aabb
from compas_model.algorithms.intersections import is_intersection_line_box
from compas_viewer import Viewer


class BVHNode(TreeNode):
    def __init__(self, objects: list[tuple[int, Point, list[Point]]], **kwargs):
        super().__init__(**kwargs)
        self.objects = objects
        self._box = None

    @property
    def box(self) -> Box:
        if not self._box:
            self._box = self.compute_box()
        return self._box

    def compute_box(self) -> Box:
        raise NotImplementedError

    def intersect_line(self, line: Line) -> Generator["BVHNode", None, None]:
        raise NotImplementedError

    def intersect_box(self, box: Box) -> Generator["BVHNode", None, None]:
        raise NotImplementedError


class AABBNode(BVHNode):
    def compute_box(self) -> Box:
        points = [point for o in self.objects for point in o[2]]
        return Box.from_points(points)

    def intersect_line(self, line: Line) -> Generator["AABBNode", None, None]:
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_line_aabb(line, node.box):
                yield node
                queue.extend(node.children)


class OBBNode(BVHNode):
    def compute_box(self) -> Box:
        points = [point for o in self.objects for point in o[2]]
        return Box.from_bounding_box(oriented_bounding_box_numpy(points))

    def intersect_line(self, line: Line) -> Generator["OBBNode", None, None]:
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_line_box(line, node.box):
                yield node
                queue.extend(node.children)

    def intersect_box(self, box: Box) -> Generator["OBBNode", None, None]:
        queue = [self]
        while queue:
            node = queue.pop(0)
            if is_intersection_box_box(box, node.box):
                yield node
                queue.extend(node.children)


class BVH(Tree):
    root: BVHNode

    def _add_objects(
        self,
        objects: list[tuple[int, Point, list[Point]]],
        parent: BVHNode,
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = OBBNode,
    ) -> None:
        if not objects:
            return

        if len(objects) == 1:
            parent.add(nodetype(objects[:1]))
            return

        node = nodetype(objects)
        parent.add(node)

        # sort objects according to xaxis box
        # (use the xaxis because it has the largest spread/variance)
        # perhaps axes should be rotated like in a KdTree?
        # also, lots of literature exists about splitting strategies for BVH trees
        # a common criterion is SAH (surface area heuristic)
        center = node.box.frame.point
        axis = node.box.frame.xaxis
        objects.sort(key=lambda o: (o[1] - center).dot(axis))
        median = len(objects) // 2

        # perhaps it woould make sense to make a specific binary tree
        # with left/right instead of a list of children

        # "left" objects
        self._add_objects(objects[:median], parent=node, nodetype=nodetype)

        # "right" objects
        self._add_objects(objects[median:], parent=node, nodetype=nodetype)

    @classmethod
    def from_triangles(
        cls,
        triangles: list[list[Point]],
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = OBBNode,
    ) -> "BVH":
        objects = [(index, centroid_points(abc), abc) for index, abc in enumerate(triangles)]
        tree = cls()
        tree._add_objects(objects, parent=tree, nodetype=nodetype)
        return tree

    @classmethod
    def from_mesh(
        cls,
        mesh: Mesh,
        nodetype: Optional[Union[Type[AABBNode], Type[OBBNode]]] = OBBNode,
    ) -> "BVH":
        faces = list(mesh.faces())
        objects = list(zip(faces, [mesh.face_centroid(face) for face in faces], [mesh.face_points(face) for face in faces]))
        tree = cls()
        tree._add_objects(objects, parent=tree, nodetype=nodetype)
        return tree

    def intersect_line(self, line: Line) -> Generator[BVHNode, None, None]:
        if self.root:
            for node in self.root.intersect_line(line):
                yield node

    def intersect_box(self, box: Box) -> Generator[BVHNode, None, None]:
        if self.root:
            for node in self.root.intersect_box(box):
                yield node


# =============================================================================
# Build BVH
# =============================================================================

mesh = Mesh.from_obj(compas.get("tubemesh.obj"))
mesh.quads_to_triangles()

tree = BVH.from_mesh(mesh, nodetype=AABBNode)

print(tree.get_hierarchy_string())

# =============================================================================
# Intersections
# =============================================================================

t0 = time.time()

boxes = []
points = []

for i in range(1000):
    line = Line.from_point_and_vector([2, 0 + i * 0.01, 0], [0, 0, 10])

    for node in tree.intersect_line(line):
        if node.is_leaf:
            triangle = node.objects[0][2]
            result = intersection_ray_triangle(line, triangle)
            if result:
                boxes.append(node.box)
                points.append(Point(*result))

t1 = time.time()

print(t1 - t0)

# =============================================================================
# Viz
# =============================================================================

viewer = Viewer()
viewer.scene.add(mesh)
viewer.scene.add(line, linecolor=Color.blue(), linewidth=2)
viewer.scene.add(boxes, facecolor=Color.green(), opacity=0.5)
viewer.scene.add(points, pointcolor=Color.red(), pointsize=10)
viewer.show()
