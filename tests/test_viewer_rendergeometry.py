import numpy as np
import pytest

from compas.datastructures import Mesh
from compas.geometry import Box
from compas_model.viewer import RenderGeometry
from compas_model.viewer import render_geometry_from_brep
from compas_model.viewer import render_geometry_from_mesh


def test_mesh_render_geometry_triangulates_faces_but_keeps_original_edges():
    mesh = Mesh.from_vertices_and_faces(
        [(0, 0, 0), (2, 0, 0), (2, 2, 0), (1, 1, 0), (0, 2, 0)],
        [[0, 1, 2, 3, 4]],
    )

    render = render_geometry_from_mesh(mesh)

    assert render.representation == "mesh"
    assert render.triangles.shape == (3, 3)
    assert render.face_vertices.shape == (9, 3)
    assert render.line_vertices.shape == (10, 3)
    displayed_segments = {tuple(sorted((tuple(a), tuple(b)))) for a, b in render.line_vertices.reshape((-1, 2, 3))}
    assert ((0.0, 0.0, 0.0), (2.0, 2.0, 0.0)) not in displayed_segments


def test_render_geometry_validates_shapes_and_indices():
    empty = np.empty((0, 3), dtype=float)
    with pytest.raises(ValueError, match="shape"):
        RenderGeometry(np.empty((3,), dtype=float), np.empty((0, 3), dtype=np.int32), empty, empty, "mesh")
    with pytest.raises(ValueError, match="Triangle indices"):
        RenderGeometry(np.zeros((3, 3)), np.asarray([[0, 1, 3]], dtype=np.int32), empty, empty, "mesh")
    with pytest.raises(ValueError, match="pairs"):
        RenderGeometry(empty, np.empty((0, 3), dtype=np.int32), np.zeros((3, 3)), empty, "mesh")


def test_brep_render_geometry_uses_native_viewmesh_and_boundaries():
    pytest.importorskip("compas_occ")

    render = render_geometry_from_brep(Box().to_brep())

    assert render.representation == "brep"
    assert len(render.triangles) == 12
    assert len(render.line_vertices) >= 24
    assert len(render.line_vertices) % 2 == 0
