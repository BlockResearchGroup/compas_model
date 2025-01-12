from math import radians
from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Rotation
from compas.geometry import Transformation
from compas.geometry import add_vectors
from compas.geometry import angle_vectors
from compas.geometry import subtract_vectors
from compas.geometry import transform_points
from compas.geometry import translate_points
from compas.tolerance import Tolerance
from compas_model.algorithms.nnbrs import find_nearest_neighbours
from compas_model.elements import Element
from compas_model.interactions import ContactInterface

from .model import Model

try:
    from compas_occ.brep import OCCBrepFace as BrepFace
except ImportError:
    print("compas_occ not installed. Using compas.geometry.BrepFace instead.")


class BlockModel(Model):
    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name)

    def compute_intersections(self):
        pass

    def compute_overlaps(self, deflection=None, tolerance=1, max_distance=50, min_area=0):
        pass

    def compute_interfaces(self, deflection=None, tolerance=1, max_distance=50, min_area=0, nmax=10):
        deflection = deflection or Tolerance().lineardeflection

        node_index = {node: index for index, node in enumerate(self.graph.nodes())}
        index_node = {index: node for index, node in enumerate(self.graph.nodes())}

        geometries: list[Brep] = [self.graph.node_element(node).modelgeometry for node in self.graph.nodes()]

        cloud = [geometry.centroid for geometry in geometries]
        nnbrs = find_nearest_neighbours(cloud, nmax, dims=3)

        for u in self.graph.nodes():
            A: Element = self.graph.node_element(u)  # type: ignore

            i = node_index[u]
            nbrs = nnbrs[i][1]

            for j in nbrs:
                v = index_node[j]

                if u == v:
                    continue

                if self.graph.has_edge((u, v), directed=False):
                    continue

                B: Element = self.graph.node_element(v)  # type: ignore

                faces_A, faces_B = A.modelgeometry.overlap(B.modelgeometry, deflection=deflection, tolerance=tolerance)  # type: ignore
                faces_A: list[BrepFace]
                faces_B: list[BrepFace]

                if faces_A and faces_B:
                    for face_A in faces_A:
                        brep_A = Brep.from_brepfaces([face_A])

                        if brep_A.area < min_area:
                            continue

                        for face_B in faces_B:
                            brep_B = Brep.from_brepfaces([face_B])

                            if brep_B.area < min_area:
                                continue

                            brep_C: Brep = Brep.from_boolean_intersection(brep_A, brep_B)

                            if brep_C.area < min_area:
                                continue

                            poly_C = brep_C.to_polygons()[0]
                            mesh_C = brep_C.to_tesselation()[0]

                            interaction = ContactInterface(points=poly_C.points, mesh=mesh_C)

                            # do something with the interactions
                            self.add_interaction(A, B, interaction=interaction)

    @classmethod
    def from_barrel_vault(
        cls,
        span: float = 6.0,
        length: float = 6.0,
        thickness: float = 0.25,
        rise: float = 0.6,
        vou_span: int = 9,
        vou_length: int = 6,
        zero_is_centerline_or_lowestpoint: bool = False,
    ) -> "BlockModel":
        """
        Creates block elements from the barrel vault geometry.

        Parameters
        ----------
        span : float
            span of the vault
        length : float
            length of the vault perpendicular to the span
        thickness : float
            thickness of the vault
        rise : float
            rise of the vault from 0.0 to middle axis of the vault thickness
        vou_span : int
            number of voussoirs in the span direction
        vou_length : int
            number of voussoirs in the length direction
        zero_is_centerline_or_lowestpoint : bool
            if True, the lowest point of the vault is at the center line of the arch, otherwise the center line of the vault is lowest mesh z-coordinate.

        Returns
        -------
        list[:class:`compas.datastructures.Mesh`]
        A list of meshes representing the geometry of the barrel vault.
        """
        radius: float = rise / 2 + span**2 / (8 * rise)
        top: list[float] = [0, 0, rise]
        left: list[float] = [-span / 2, 0, 0]
        center: list[float] = [0.0, 0.0, rise - radius]
        vector: list[float] = subtract_vectors(left, center)
        springing: float = angle_vectors(vector, [-1.0, 0.0, 0.0])
        sector: float = radians(180) - 2 * springing
        angle: float = sector / vou_span

        a: list[float] = [0, -length / 2, rise - (thickness / 2)]
        d: list[float] = add_vectors(top, [0, -length / 2, (thickness / 2)])

        R: Rotation = Rotation.from_axis_and_angle([0, 1.0, 0], 0.5 * sector, center)
        bottom: list[list[float]] = transform_points([a, d], R)
        brick_pts: list[list[list[float]]] = []
        for i in range(vou_span + 1):
            R_angle: Rotation = Rotation.from_axis_and_angle([0, 1.0, 0], -angle * i, center)
            points: list[list[float]] = transform_points(bottom, R_angle)
            brick_pts.append(points)

        depth: float = length / vou_length
        grouped_data: list[list[float]] = [pair[0] + pair[1] for pair in zip(brick_pts, brick_pts[1:])]

        meshes: list[Mesh] = []
        for i in range(vou_length):
            for l, group in enumerate(grouped_data):  # noqa: E741
                is_support: bool = l == 0 or l == (len(grouped_data) - 1)
                if l % 2 == 0:
                    point_l: list[list[float]] = [group[0], group[1], group[2], group[3]]
                    point_list: list[list[float]] = [
                        [group[0][0], group[0][1] + (depth * i), group[0][2]],
                        [group[1][0], group[1][1] + (depth * i), group[1][2]],
                        [group[2][0], group[2][1] + (depth * i), group[2][2]],
                        [group[3][0], group[3][1] + (depth * i), group[3][2]],
                    ]
                    p_t: list[list[float]] = translate_points(point_l, [0, depth * (i + 1), 0])
                    vertices: list[list[float]] = point_list + p_t
                    faces: list[list[int]] = [[0, 1, 3, 2], [0, 4, 5, 1], [4, 6, 7, 5], [6, 2, 3, 7], [1, 5, 7, 3], [2, 6, 4, 0]]
                    mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
                    mesh.attributes["is_support"] = is_support
                    meshes.append(mesh)
                else:
                    point_l: list[list[float]] = [group[0], group[1], group[2], group[3]]
                    points_base: list[list[float]] = translate_points(point_l, [0, depth / 2, 0])
                    points_b_t: list[list[float]] = translate_points(points_base, [0, depth * i, 0])
                    points_t: list[list[float]] = translate_points(points_base, [0, depth * (i + 1), 0])
                    vertices: list[list[float]] = points_b_t + points_t
                    if i != vou_length - 1:
                        faces: list[list[int]] = [[0, 1, 3, 2], [0, 4, 5, 1], [4, 6, 7, 5], [6, 2, 3, 7], [1, 5, 7, 3], [2, 6, 4, 0]]
                        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
                        mesh.attributes["is_support"] = is_support
                        meshes.append(mesh)

        for l, group in enumerate(grouped_data):  # noqa: E741
            is_support: bool = l == 0 or l == (len(grouped_data) - 1)
            if l % 2 != 0:
                point_l: list[list[float]] = [group[0], group[1], group[2], group[3]]
                p_t: list[list[float]] = translate_points(point_l, [0, depth / 2, 0])
                vertices: list[list[float]] = point_l + p_t
                faces: list[list[int]] = [[0, 1, 3, 2], [0, 4, 5, 1], [4, 6, 7, 5], [6, 2, 3, 7], [1, 5, 7, 3], [2, 6, 4, 0]]
                mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
                mesh.attributes["is_support"] = is_support
                meshes.append(mesh)

                point_f: list[list[float]] = translate_points(point_l, [0, length, 0])
                p_f: list[list[float]] = translate_points(point_f, [0, -depth / 2, 0])
                vertices: list[list[float]] = p_f + point_f
                faces: list[list[int]] = [[0, 1, 3, 2], [0, 4, 5, 1], [4, 6, 7, 5], [6, 2, 3, 7], [1, 5, 7, 3], [2, 6, 4, 0]]
                mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
                mesh.attributes["is_support"] = is_support
                meshes.append(mesh)

        # Find the lowest z-coordinate and move all the block to zero.
        if not zero_is_centerline_or_lowestpoint:
            min_z: float = min([min(mesh.vertex_coordinates(key)[2] for key in mesh.vertices()) for mesh in meshes])
            for mesh in meshes:
                mesh.translate([0, 0, -min_z])

        # Translate blocks to xy frame and create blockmodel.
        blockmodel: BlockModel = BlockModel()
        from compas_model.elements import BlockElement

        for mesh in meshes:
            origin: Point = mesh.face_polygon(5).frame.point
            xform: Transformation = Transformation.from_frame_to_frame(
                Frame(origin, mesh.vertex_point(0) - mesh.vertex_point(2), mesh.vertex_point(4) - mesh.vertex_point(2)), Frame.worldXY()
            )
            mesh_xy: Mesh = mesh.transformed(xform)
            block: BlockElement = BlockElement(shape=mesh_xy, is_support=mesh_xy.attributes["is_support"])
            block.transformation = xform.inverse()
            blockmodel.add_element(block)

        return blockmodel
