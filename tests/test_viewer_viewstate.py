import pytest
from typing import cast

from compas.data import json_dumps
from compas.data import json_loads
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Translation

from compas_model.elements import Element
from compas_model.models import Model
from compas_model.viewer import RenderGeometryCache
from compas_model.viewer import RenderSettings


class MeshElement(Element):
    def __init__(self, mesh):
        super().__init__(geometry=mesh)

    def compute_elementgeometry(self, include_features=False) -> Mesh | Brep:
        assert self.geometry is not None
        return self.geometry


def test_render_cache_reuses_geometry_until_element_revision_changes():
    model = Model()
    element = model.add_element(MeshElement(Box().to_mesh()))
    cache = RenderGeometryCache()

    first = cache.get(element)
    second = cache.get(element)

    assert first is second
    assert cache.hits == 1
    assert cache.misses == 1

    element.transform(Translation.from_vector([1, 0, 0]))
    third = cache.get(element)

    assert third is not first
    assert cache.misses == 2
    assert third.vertices[:, 0].min() == pytest.approx(0.5)


def test_render_cache_settings_and_explicit_invalidation_create_misses():
    model = Model()
    element = model.add_element(MeshElement(Box().to_mesh()))
    cache = RenderGeometryCache()

    first = cache.get(element)
    second = cache.get(element, RenderSettings(mesh_tolerance=1e-8))
    cache.invalidate(element)
    third = cache.get(element, RenderSettings(mesh_tolerance=1e-8))

    assert second is not first
    assert third is not second
    assert cache.misses == 3


def test_model_transformation_increments_element_geometry_revisions():
    model = Model()
    elements = model.add_elements([MeshElement(Box().to_mesh()), MeshElement(Box().to_mesh())])
    revisions = [element.geometry_revision for element in elements]

    model.transform(Translation.from_vector([1, 0, 0]))

    assert [element.geometry_revision for element in elements] == [revision + 1 for revision in revisions]


def test_render_settings_reject_invalid_values():
    with pytest.raises(ValueError, match="tolerance"):
        RenderSettings(mesh_tolerance=-1)
    with pytest.raises(ValueError, match="linear deflection"):
        RenderSettings(linear_deflection=0)
    with pytest.raises(ValueError, match="angular deflection"):
        RenderSettings(angular_deflection=-1)
    with pytest.raises(ValueError, match="length unit"):
        RenderSettings(unit="CM")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quality"):
        RenderSettings(quality="ultra")  # type: ignore[arg-type]


def test_model_unit_is_validated_and_serialized():
    model = Model(unit="MM")
    restored = cast(Model, json_loads(json_dumps(model)))

    assert model.unit == "MM"
    assert restored.unit == "MM"
    with pytest.raises(ValueError, match="length unit"):
        Model(unit="CM")  # type: ignore[arg-type]


def test_render_defaults_represent_same_physical_distances_in_m_and_mm():
    meters = RenderSettings(unit="M")
    millimeters = RenderSettings(unit="MM")

    assert meters.effective_linear_deflection(1.0) == pytest.approx(0.001)
    assert millimeters.effective_linear_deflection(1000.0) == pytest.approx(1.0)
    assert meters.effective_mesh_tolerance == pytest.approx(1e-9)
    assert millimeters.effective_mesh_tolerance == pytest.approx(1e-6)
    assert meters.effective_angular_deflection == millimeters.effective_angular_deflection == pytest.approx(0.1)


@pytest.mark.parametrize(
    ("quality", "relative", "angular"),
    [("draft", 1e-2, 0.20), ("standard", 1e-3, 0.10), ("high", 1e-4, 0.05)],
)
def test_render_quality_presets(quality, relative, angular):
    settings = RenderSettings(quality=quality)

    assert settings.effective_linear_deflection(1.0) == pytest.approx(relative)
    assert settings.effective_angular_deflection == pytest.approx(angular)


@pytest.mark.parametrize(
    ("quality", "small", "large"),
    [
        ("draft", 1e-4, 2e-2),
        ("standard", 1e-5, 5e-3),
        ("high", 1e-6, 1e-3),
    ],
)
def test_render_quality_clamps_tiny_degenerate_and_large_objects(quality, small, large):
    settings = RenderSettings(quality=quality)

    assert settings.effective_linear_deflection(0.0) == pytest.approx(small)
    assert settings.effective_linear_deflection(1e-9) == pytest.approx(small)
    assert settings.effective_linear_deflection(1e9) == pytest.approx(large)


def test_render_deflection_depends_on_size_not_coordinate_magnitude():
    settings = RenderSettings()
    local_diagonal = Box(1, 2, 3).diagonal.length
    translated_diagonal = Box(1, 2, 3, frame=Box(1, 2, 3).frame.translated([1e9, -1e9, 1e9])).diagonal.length

    assert translated_diagonal == pytest.approx(local_diagonal)
    assert settings.effective_linear_deflection(translated_diagonal) == pytest.approx(settings.effective_linear_deflection(local_diagonal))


@pytest.mark.parametrize("characteristic_length", [-1.0, float("inf"), float("nan")])
def test_render_deflection_rejects_invalid_characteristic_length(characteristic_length):
    with pytest.raises(ValueError, match="characteristic length"):
        RenderSettings().effective_linear_deflection(characteristic_length)


def test_explicit_render_values_override_unit_and_quality_defaults():
    settings = RenderSettings(
        unit="MM",
        quality="high",
        mesh_tolerance=0.01,
        linear_deflection=0.25,
        angular_deflection=0.025,
    )

    assert settings.effective_mesh_tolerance == 0.01
    assert settings.effective_linear_deflection(1e9) == 0.25
    assert settings.effective_angular_deflection == 0.025


def test_element_object_owns_and_refreshes_render_geometry():
    pytest.importorskip("compas_viewer")
    from compas_model.viewer import ElementObject

    model = Model(unit="MM")
    element = model.add_element(MeshElement(Box().to_mesh()))
    scene_object = ElementObject(item=element, context="Viewer", linewidth=1, pointsize=1, opacity=1)
    original = scene_object.render_geometry

    assert scene_object.element is element
    assert scene_object.render_settings.unit == "MM"

    element.geometry = Box(2).to_mesh()

    assert scene_object.refresh_render_geometry()
    assert scene_object.render_geometry is not original


def test_element_object_rejects_explicit_settings_in_different_unit():
    pytest.importorskip("compas_viewer")
    from compas_model.viewer import ElementObject

    model = Model(unit="MM")
    element = model.add_element(MeshElement(Box().to_mesh()))

    with pytest.raises(ValueError, match="match the model unit"):
        ElementObject(
            item=element,
            context="Viewer",
            linewidth=1,
            pointsize=1,
            opacity=1,
            render_settings=RenderSettings(unit="M"),
        )
