import compas.datastructures  # noqa: F401
import compas.geometry  # noqa: F401
import numpy
import pythreejs as three
from compas.geometry import Polygon
from compas.geometry import earclip_polygon
from compas_notebook.scene import ThreeSceneObject

from compas_model.scene import BlockObject


class ThreeBlockObject(ThreeSceneObject, BlockObject):
    """Scene object for drawing block objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def draw(self):
        """Draw the mesh associated with the scene object.

        Returns
        -------
        list[three.Mesh, three.LineSegments]
            List of pythreejs objects created.

        """
        self._guids = []

        mesh = self.element.geometry  # type: ignore

        vertices = list(mesh.vertices())  # type: ignore
        faces = list(mesh.faces())  # type: ignore
        edges = list(mesh.edges())  # type: ignore

        transformation = self.element.worldtransformation

        if transformation:
            matrix = numpy.array(transformation.matrix, dtype=numpy.float32).transpose().ravel().tolist()  # noqa: F841  # type: ignore

        vertex_xyz = {vertex: mesh.vertex_attributes(vertex, "xyz") for vertex in vertices}  # type: ignore

        # =============================================================================
        # Vertices
        # =============================================================================

        if self.show_vertices:
            if self.show_vertices is not True:
                vertices = self.show_vertices

            positions = [vertex_xyz[vertex] for vertex in vertices]
            positions = numpy.array(positions, dtype=numpy.float32)

            colors = [self.vertexcolor[vertex] for vertex in vertices]  # type: ignore
            colors = numpy.array(colors, dtype=numpy.float32)

            geometry = three.BufferGeometry(
                attributes={
                    "position": three.BufferAttribute(positions, normalized=False),
                    "color": three.BufferAttribute(colors, normalized=False, itemSize=3),
                }
            )
            material = three.PointsMaterial(
                size=self.vertexsize,
                vertexColors="VertexColors",
            )

            threeobject = three.Points(geometry, material)
            # threeobject.matrix = matrix
            # threeobject.matrixAutoUpdate = False

            self._guids.append(threeobject)

        # =============================================================================
        # Edges
        # =============================================================================

        if self.show_edges:
            if self.show_edges is not True:
                edges = self.show_edges

            positions = []
            colors = []

            for u, v in edges:
                positions.append(vertex_xyz[u])
                positions.append(vertex_xyz[v])
                colors.append(self.edgecolor[u, v])
                colors.append(self.edgecolor[u, v])

            positions = numpy.array(positions, dtype=numpy.float32)
            colors = numpy.array(colors, dtype=numpy.float32)

            geometry = three.BufferGeometry(
                attributes={
                    "position": three.BufferAttribute(positions, normalized=False),
                    "color": three.BufferAttribute(colors, normalized=False, itemSize=3),
                }
            )
            material = three.LineBasicMaterial(vertexColors="VertexColors")

            threeobject = three.LineSegments(geometry, material)
            # threeobject.matrix = matrix
            # threeobject.matrixAutoUpdate = False

            self._guids.append(threeobject)

        # =============================================================================
        # Faces
        # =============================================================================

        if self.show_faces:
            if self.show_faces is not True:
                faces = self.show_faces

            positions = []
            colors = []

            for face in faces:
                vertices = mesh.face_vertices(face)  # type: ignore
                c = self.facecolor[face]  # type: ignore

                if len(vertices) == 3:
                    positions.append(vertex_xyz[vertices[0]])
                    positions.append(vertex_xyz[vertices[1]])
                    positions.append(vertex_xyz[vertices[2]])
                    colors.append(c)
                    colors.append(c)
                    colors.append(c)

                elif len(vertices) == 4:
                    positions.append(vertex_xyz[vertices[0]])
                    positions.append(vertex_xyz[vertices[1]])
                    positions.append(vertex_xyz[vertices[2]])
                    colors.append(c)
                    colors.append(c)
                    colors.append(c)
                    positions.append(vertex_xyz[vertices[0]])
                    positions.append(vertex_xyz[vertices[2]])
                    positions.append(vertex_xyz[vertices[3]])
                    colors.append(c)
                    colors.append(c)
                    colors.append(c)

                else:
                    polygon = Polygon([vertex_xyz[v] for v in vertices])
                    ears = earclip_polygon(polygon)
                    for ear in ears:  # type: ignore
                        positions.append(vertex_xyz[vertices[ear[0]]])
                        positions.append(vertex_xyz[vertices[ear[1]]])
                        positions.append(vertex_xyz[vertices[ear[2]]])
                        colors.append(c)
                        colors.append(c)
                        colors.append(c)

            positions = numpy.array(positions, dtype=numpy.float32)
            colors = numpy.array(colors, dtype=numpy.float32)

            geometry = three.BufferGeometry(
                attributes={
                    "position": three.BufferAttribute(positions, normalized=False),
                    "color": three.BufferAttribute(colors, normalized=False, itemSize=3),
                }
            )
            material = three.MeshBasicMaterial(
                side="DoubleSide",
                vertexColors="VertexColors",
            )

            threeobject = three.Mesh(geometry, material)
            # threeobject.matrix = matrix
            # threeobject.matrixAutoUpdate = False

            self._guids.append(threeobject)

        return self.guids
