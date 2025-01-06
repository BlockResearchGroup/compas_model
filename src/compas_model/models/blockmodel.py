from typing import Optional

from compas.geometry import Brep
from compas.tolerance import Tolerance
from compas_model.algorithms.nnbrs import find_nearest_neighbours
from compas_model.elements import Element
from compas_model.interactions import ContactInterface

from .model import Model


class BlockModel(Model):
    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name)

    def compute_intersections(self):
        pass

    def compute_overlaps(self, deflection=None, tolerance=1, max_distance=50, min_area=0):
        pass

    def compute_interfaces(self, deflection=None, tolerance=1, max_distance=50, min_area=0, nmax=10):
        try:
            from compas_occ.brep import OCCBrepFace as BrepFace
        except ImportError:
            raise ImportError("compas_occ is required for this functionality. Please install it via conda.")

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
