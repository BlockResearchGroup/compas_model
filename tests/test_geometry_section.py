from typing import cast

import pytest
from compas.data import json_dumps
from compas.data import json_loads
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Polyline
from compas.geometry import Translation
from compas_model.geometry import ClipElementResult
from compas_model.geometry import ClipResult
from compas_model.geometry import PlanarRegion
from compas_model.geometry import SectionClassification
from compas_model.geometry import SectionElementResult
from compas_model.geometry import SectionRepresentation
from compas_model.geometry import SectionResult


def square_region(z=0.0):
    return PlanarRegion(
        Polygon([[0, 0, z], [1, 0, z], [1, 1, z], [0, 1, z]]),
        frame=Frame([0, 0, z]),
    )


def test_section_result_empty_defaults():
    result = SectionResult(Frame.worldXY())

    assert result.elements == []
    assert result.regions == []
    assert result.open_curves == []
    assert result.outlines == []


def test_section_result_preserves_element_and_region_order():
    first = SectionElementResult("a", "intersecting", "mesh", regions=[square_region()])
    second = SectionElementResult("b", "behind", "mesh")
    result = SectionResult(Frame.worldXY(), [first, second])

    assert [element.source_guid for element in result.elements] == ["a", "b"]
    assert [element.source_guid for element in result.by_classification("behind")] == ["b"]
    assert result.front == []
    assert result.behind == [result.elements[1]]
    assert result.intersecting == [result.elements[0]]
    assert result.coplanar == []
    assert len(result.regions) == 1
    assert len(result.outlines) == 1


def test_section_result_classifies_signed_distance_with_tolerance():
    result = SectionResult(Frame.worldXY(), tolerance=0.01)

    assert result.signed_distance(Point(0, 0, 2)) == pytest.approx(2.0)
    assert result.classify_point(Point(0, 0, 0.02)) == "front"
    assert result.classify_point(Point(0, 0, -0.02)) == "behind"
    assert result.classify_point(Point(0, 0, 0.01)) == "coplanar"
    assert result.classify_point(Point(0, 0, -0.01)) == "coplanar"


def test_section_result_serialization_preserves_regions_holes_curves_and_geometry():
    exterior = Polygon([[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0]])
    hole = Polygon([[1, 1, 0], [1, 3, 0], [3, 3, 0], [3, 1, 0]])
    region = PlanarRegion(exterior, holes=[hole], frame=Frame.worldXY())
    element = SectionElementResult(
        "block-a",
        "intersecting",
        "mesh",
        regions=[region],
        open_curves=[Polyline([[5, 0, 0], [6, 0, 0]])],
        name="sectioned block",
    )
    result = SectionResult(
        Frame.worldXY(),
        [element],
        tolerance=0.001,
        name="test section",
    )

    restored = json_loads(json_dumps(result))

    assert isinstance(restored, SectionResult)
    assert restored.name == "test section"
    assert restored.elements[0].source_guid == "block-a"
    assert len(restored.regions[0].holes) == 1
    assert restored.regions[0].area == pytest.approx(12.0)
    assert len(restored.open_curves) == 1
    assert len(restored.outlines) == 3


def test_clip_element_result_takes_geometry_snapshot():
    mesh = Box().to_mesh()
    original = mesh.vertex_coordinates(0)
    section = SectionElementResult("a", "behind", "mesh")
    element = ClipElementResult(section, mesh)

    mesh.vertex_attributes(0, names="xyz", values=[10, 10, 10])

    assert element.geometry is not None
    assert element.geometry.vertex_coordinates(0) == original


def test_section_result_transformed_returns_independent_copy():
    element = SectionElementResult("a", "intersecting", "mesh", regions=[square_region()])
    result = SectionResult(Frame.worldXY(), [element])

    transformed = result.transformed(Translation.from_vector([0, 0, 2]))

    assert result.frame.point.z == pytest.approx(0.0)
    assert transformed.frame.point.z == pytest.approx(2.0)
    assert transformed.regions[0].centroid.z == pytest.approx(2.0)


def test_section_result_rejects_off_plane_section_geometry():
    element = SectionElementResult("a", "intersecting", "mesh", regions=[square_region(z=0.1)])

    with pytest.raises(ValueError, match="cutting plane"):
        SectionResult(Frame.worldXY(), [element], tolerance=0.01)


def test_section_result_rejects_invalid_options():
    with pytest.raises(ValueError, match="tolerance"):
        SectionResult(Frame.worldXY(), tolerance=-1)
    element = SectionElementResult("a", "front", "mesh")
    result = SectionResult(Frame.worldXY(), [element])
    with pytest.raises(ValueError, match="classification"):
        result.by_classification(cast(SectionClassification, "invalid"))


def test_section_element_result_rejects_invalid_classification_and_representation():
    with pytest.raises(ValueError, match="classification"):
        SectionElementResult("a", cast(SectionClassification, "invalid"), "mesh")
    with pytest.raises(ValueError, match="representation"):
        SectionElementResult("a", "front", cast(SectionRepresentation, "invalid"))


def test_clip_element_result_rejects_geometry_representation_mismatch():
    pytest.importorskip("compas_occ")

    with pytest.raises(TypeError, match="match"):
        ClipElementResult(SectionElementResult("a", "behind", "mesh"), Box().to_brep())
    with pytest.raises(TypeError, match="match"):
        ClipElementResult(SectionElementResult("a", "behind", "brep"), Box().to_mesh())


def test_clip_result_serialization_and_section_view():
    clip = ClipElementResult(
        SectionElementResult("a", "intersecting", "mesh", regions=[square_region()]),
        Box().to_mesh(),
    )
    result = ClipResult(Frame.worldXY(), [clip], cap=True, name="clip")

    restored = json_loads(json_dumps(result))

    assert isinstance(restored, ClipResult)
    assert restored.name == "clip"
    assert len(restored.geometry) == 1
    assert len(restored.section.regions) == 1
