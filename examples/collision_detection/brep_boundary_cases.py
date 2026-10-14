"""Visual checks of BRep penetration, touching, and separation.

Run with ``--no-viewer`` to execute the assertions without opening a window.
"""

import sys

from _viewer import AMBER
from _viewer import BLUE
from _viewer import GREEN
from _viewer import RED
from _viewer import show_scene

from compas.geometry import Box
from compas.geometry import Frame
from compas_model.algorithms import is_brep_brep_collision


def build_example():
    specifications = [
        ("penetrating", -2.0, 0.60, True, True, GREEN),
        ("face touching", 0.0, 1.00, True, False, AMBER),
        ("separated", 2.0, 1.05, False, False, RED),
    ]
    rows = []

    for label, y, offset, expected_touching, expected_penetrating, color in specifications:
        brep_a = Box(1, 1, 1, frame=Frame([0, y, 0])).to_brep()
        brep_b = Box(1, 1, 1, frame=Frame([offset, y, 0])).to_brep()
        touching = is_brep_brep_collision(brep_a, brep_b)
        penetrating = is_brep_brep_collision(brep_a, brep_b, include_touching=False)

        assert touching is expected_touching
        assert penetrating is expected_penetrating
        rows.append((label, y, brep_a, brep_b, touching, penetrating, color))

    return rows


def main(show=True):
    rows = build_example()
    for label, _, _, _, touching, penetrating, _ in rows:
        print(f"{label}: include_touching={touching}, penetration={penetrating}")

    if show:
        objects = []
        labels = []
        for label, y, brep_a, brep_b, touching, penetrating, color in rows:
            objects.extend([(brep_a, f"{label}: A", BLUE, 0.60), (brep_b, f"{label}: B", color, 0.60)])
            labels.append((f"{label}: touch={touching}, penetrate={penetrating}", (-0.6, y + 0.8, 0.7), color))
        show_scene("BRep collision: boundary cases", objects, labels)


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
