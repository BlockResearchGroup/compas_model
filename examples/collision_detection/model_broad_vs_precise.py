"""Visual comparison of model-level broad and precise mesh collisions.

Amber geometry participates only in a conservative fast collision. Green
geometry participates in a precise surface collision. Grey geometry has no
collision. Run with ``--no-viewer`` to execute without opening a window.
"""

import sys

from _viewer import AMBER
from _viewer import GREEN
from _viewer import GREY
from _viewer import show_scene

from compas.geometry import Box
from compas.geometry import Frame
from compas_model.elements import MeshElement
from compas_model.models import Model


def pair_names(pairs):
    return {tuple(sorted((a.name, b.name))) for a, b in pairs}


def build_example():
    geometries = {
        "overlap A": Box(1, 1, 1, frame=Frame([-2.0, -1.5, 0])).to_mesh(),
        "overlap B": Box(1, 1, 1, frame=Frame([-1.4, -1.5, 0])).to_mesh(),
        "touch A": Box(1, 1, 1, frame=Frame([1.0, -1.5, 0])).to_mesh(),
        "touch B": Box(1, 1, 1, frame=Frame([2.0, -1.5, 0])).to_mesh(),
        "isolated": Box(1, 1, 1, frame=Frame([4.0, -1.5, 0])).to_mesh(),
        "container": Box(3, 3, 3, frame=Frame([0, 2.0, 0])).to_mesh(),
        "contained": Box(0.7, 0.7, 0.7, frame=Frame([0, 2.0, 0])).to_mesh(),
    }

    model = Model()
    elements = {name: model.add_element(MeshElement(geometry=mesh, name=name)) for name, mesh in geometries.items()}
    fast_pairs = pair_names(model.collisions(precision="fast"))
    precise_pairs = pair_names(model.collisions(precision="precise"))

    expected_precise = {("overlap A", "overlap B"), ("touch A", "touch B")}
    assert precise_pairs == expected_precise
    assert fast_pairs == expected_precise | {("contained", "container")}
    return elements, fast_pairs, precise_pairs


def main(show=True):
    elements, fast_pairs, precise_pairs = build_example()
    print(f"fast pairs: {sorted(fast_pairs)}")
    print(f"precise pairs: {sorted(precise_pairs)}")

    if show:
        precise_names = {name for pair in precise_pairs for name in pair}
        fast_only_names = {name for pair in fast_pairs - precise_pairs for name in pair}
        objects = []
        for name, element in elements.items():
            color = GREEN if name in precise_names else AMBER if name in fast_only_names else GREY
            opacity = 0.25 if name == "container" else 0.70
            objects.append((element.modelgeometry, name, color, opacity))

        labels = [
            ("green: precise surface collision", (-2.7, -0.7, 0.8), GREEN),
            ("amber: AABB overlap only (containment)", (-1.5, 3.8, 1.8), AMBER),
            ("grey: no collision", (3.3, -0.7, 0.8), GREY),
        ]
        show_scene("Model collision: broad versus precise", objects, labels)


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
