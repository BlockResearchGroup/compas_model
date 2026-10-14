from math import pi
import pytest

pytest.importorskip("compas_occ")

from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Polygon
from compas.geometry import Sphere
from compas.geometry import Translation
from compas_model.geometry import clip_brep
from compas_model.geometry import intersection_brep_plane
from compas_model.geometry import section_brep


def brep_face(polygon):
    from compas_occ.brep import OCCBrep
    from compas_occ.brep import OCCBrepFace

    face = OCCBrepFace.from_polygon(polygon)
    return OCCBrep.from_native(face.occ_shape)


def test_section_and_clip_brep_have_distinct_outputs():
    brep = Box(1, 1, 1).to_brep()

    section = section_brep(brep, Frame.worldXY(), "box")
    clip = clip_brep(brep, Frame.worldXY(), "box")

    assert section.classification == "intersecting"
    assert len(section.regions) == 1
    assert section.regions[0].area == pytest.approx(1.0)
    assert section.open_curves == []
    assert clip.geometry is not None
    assert clip.geometry.is_solid
    assert clip.geometry.volume == pytest.approx(0.5)
    assert brep.volume == pytest.approx(1.0)


def test_brep_and_mesh_box_sections_agree():
    regions, curves = intersection_brep_plane(Box().to_brep(), Frame.worldXY())

    assert len(regions) == 1
    assert regions[0].area == pytest.approx(1.0)
    assert curves == []


def test_section_curved_brep_uses_sampled_polygonal_region_and_exact_trim():
    result = clip_brep(
        Sphere(1).to_brep(),
        Frame.worldXY(),
        "sphere",
        curve_samples=128,
    )

    assert len(result.section.regions) == 1
    assert result.section.regions[0].area == pytest.approx(pi, rel=5e-4)
    assert result.geometry is not None
    assert result.geometry.volume == pytest.approx(2 * pi / 3)


def test_section_brep_preserves_hole_and_exact_trimmed_volume():
    brep = Box(4, 4, 2).to_brep().boolean_difference(Box(2, 2, 2).to_brep())

    result = clip_brep(brep, Frame.worldXY(), "tube")

    assert len(result.section.regions) == 1
    assert len(result.section.regions[0].holes) == 1
    assert result.section.regions[0].area == pytest.approx(12.0)
    assert result.geometry is not None
    assert result.geometry.volume == pytest.approx(12.0)


def test_section_brep_open_face_returns_open_curve():
    face = brep_face(Polygon([[-1, 0, -1], [1, 0, -1], [1, 0, 1], [-1, 0, 1]]))

    result = section_brep(face, Frame.worldXY(), "face")

    assert result.classification == "intersecting"
    assert result.regions == []
    assert len(result.open_curves) == 1
    assert result.open_curves[0].length == pytest.approx(2.0)


def test_section_brep_tangent_face_returns_boundary_and_whole_behind():
    brep = Box().to_brep()
    result = clip_brep(brep, Frame([0, 0, 0.5]), "box")

    assert result.classification == "intersecting"
    assert len(result.section.regions) == 1
    assert result.section.regions[0].area == pytest.approx(1.0)
    assert result.geometry is not None
    assert result.geometry.volume == pytest.approx(1.0)


def test_section_brep_coplanar_face_classification():
    face = brep_face(Polygon([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]))

    result = section_brep(face, Frame.worldXY(), "face")

    assert result.classification == "coplanar"


def test_clip_brep_includes_whole_behind_geometry_snapshot():
    brep = Box(frame=Frame([0, 0, -2])).to_brep()
    included = clip_brep(brep, Frame.worldXY(), "box")

    assert included.classification == "behind"
    assert included.geometry is not None
    brep.transform(Translation.from_vector([0, 0, 10]))
    assert included.geometry.centroid.z == pytest.approx(-2.0)


def test_section_brep_rejects_uncapped_intersected_geometry():
    with pytest.raises(NotImplementedError, match="cap=True"):
        clip_brep(Box().to_brep(), Frame.worldXY(), "box", cap=False)


def test_section_brep_rejects_invalid_options_and_empty_shape():
    from compas_occ.brep import OCCBrep

    brep = Box().to_brep()
    with pytest.raises(ValueError, match="tolerance"):
        section_brep(brep, Frame.worldXY(), "box", tolerance=-1)
    with pytest.raises(ValueError, match="minimum area"):
        section_brep(brep, Frame.worldXY(), "box", minimum_area=-1)
    with pytest.raises(ValueError, match="curve samples"):
        section_brep(brep, Frame.worldXY(), "box", curve_samples=1)
    with pytest.raises(ValueError, match="empty native OCC shape"):
        section_brep(OCCBrep(), Frame.worldXY(), "empty")
