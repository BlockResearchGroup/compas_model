import pytest
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Translation
from compas_model.geometry import clip_mesh
from compas_model.geometry import clip_mesh_halfspace
from compas_model.geometry import intersection_mesh_plane
from compas_model.geometry import section_mesh


def test_section_and_clip_mesh_have_distinct_outputs():
    mesh = Box(1, 1, 1).to_mesh()

    section = section_mesh(mesh, Frame.worldXY(), "box")
    clip = clip_mesh(mesh, Frame.worldXY(), "box")

    assert section.classification == "intersecting"
    assert len(section.regions) == 1
    assert section.regions[0].area == pytest.approx(1.0)
    assert section.open_curves == []
    assert clip.geometry is not None
    assert clip.geometry.is_closed()
    assert clip.geometry.volume() == pytest.approx(0.5)
    assert clip.section.regions[0].area == pytest.approx(1.0)
    assert mesh.volume() == pytest.approx(1.0)


def test_intersection_mesh_plane_returns_disconnected_regions():
    mesh = Box(1, 1, 1, frame=Frame([-1, 0, 0])).to_mesh()
    mesh.join(Box(1, 1, 1, frame=Frame([1, 0, 0])).to_mesh())

    regions, curves = intersection_mesh_plane(mesh, Frame.worldXY())

    assert len(regions) == 2
    assert [region.area for region in regions] == pytest.approx([1.0, 1.0])
    assert curves == []


def test_section_mesh_preserves_hole_in_region_and_caps():
    mesh = Box(4, 4, 2).to_mesh()
    void = Box(2, 2, 2).to_mesh()
    void.flip_cycles()
    mesh.join(void)

    result = clip_mesh(mesh, Frame.worldXY(), "tube")

    assert len(result.section.regions) == 1
    assert len(result.section.regions[0].holes) == 1
    assert result.section.regions[0].area == pytest.approx(12.0)
    assert result.geometry is not None
    assert result.geometry.is_closed()
    assert result.geometry.volume() == pytest.approx(12.0)


def test_intersection_open_mesh_returns_open_curve():
    mesh = Mesh.from_vertices_and_faces(
        [[-1, 0, -1], [1, 0, -1], [1, 0, 1], [-1, 0, 1]],
        [[0, 1, 2, 3]],
    )

    result = section_mesh(mesh, Frame.worldXY(), "surface")

    assert result.classification == "intersecting"
    assert result.regions == []
    assert len(result.open_curves) == 1
    assert result.open_curves[0].length == pytest.approx(2.0)


def test_section_mesh_tangent_plane_returns_boundary_without_duplicate_cap():
    mesh = Box(1, 1, 1).to_mesh()
    frame = Frame([0, 0, 0.5])

    result = clip_mesh(mesh, frame, "box")

    assert result.classification == "intersecting"
    assert len(result.section.regions) == 1
    assert result.section.regions[0].area == pytest.approx(1.0)
    assert result.geometry is not None
    assert result.geometry.is_closed()
    assert result.geometry.volume() == pytest.approx(1.0)


def test_section_mesh_coplanar_surface_has_region_but_no_retained_halfspace():
    mesh = Mesh.from_vertices_and_faces(
        [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
        [[0, 1, 2, 3]],
    )

    result = section_mesh(mesh, Frame.worldXY(), "surface")

    assert result.classification == "coplanar"
    assert len(result.regions) == 1
    assert result.regions[0].area == pytest.approx(1.0)


def test_clip_mesh_includes_whole_behind_geometry_snapshot():
    mesh = Box(1, 1, 1, frame=Frame([0, 0, -2])).to_mesh()

    included = clip_mesh(mesh, Frame.worldXY(), "box")

    assert included.classification == "behind"
    assert included.geometry is not None
    mesh.transform(Translation.from_vector([0, 0, 10]))
    assert included.geometry.centroid()[2] == pytest.approx(-2.0)


def test_section_mesh_minimum_area_filters_regions_but_not_classification():
    result = clip_mesh(
        Box(1, 1, 1).to_mesh(),
        Frame.worldXY(),
        "box",
        minimum_area=2.0,
    )

    assert result.classification == "intersecting"
    assert result.section.regions == []
    assert result.geometry is not None
    assert result.geometry.is_closed()


def test_clip_mesh_halfspace_without_cap():
    clipped = clip_mesh_halfspace(Box(1, 1, 1).to_mesh(), Frame.worldXY(), side="behind")

    assert clipped is not None
    assert not clipped.is_closed()


def test_mesh_section_rejects_invalid_options_and_empty_mesh():
    mesh = Box().to_mesh()
    with pytest.raises(ValueError, match="tolerance"):
        section_mesh(mesh, Frame.worldXY(), "box", tolerance=-1)
    with pytest.raises(ValueError, match="minimum area"):
        section_mesh(mesh, Frame.worldXY(), "box", minimum_area=-1)
    with pytest.raises(ValueError, match="empty mesh"):
        section_mesh(Mesh(), Frame.worldXY(), "empty")
    with pytest.raises(ValueError, match="clipping side"):
        clip_mesh_halfspace(mesh, Frame.worldXY(), side="invalid")
