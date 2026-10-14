"""Visual check of a simple precise mesh-surface collision.

Run with ``--no-viewer`` to execute the assertions without opening a window.
"""

import sys

from _viewer import BLUE
from _viewer import GREEN
from _viewer import show_scene

from compas.geometry import Box
from compas.geometry import Frame
from compas_model.algorithms import is_mesh_mesh_collision
from compas_model.algorithms import is_mesh_mesh_collision_fast


def build_example():
    mesh_a = Box(1, 1, 1, frame=Frame([-0.25, 0, 0])).to_mesh()
    mesh_b = Box(1, 1, 1, frame=Frame([0.25, 0, 0])).to_mesh()

    fast = is_mesh_mesh_collision_fast(mesh_a, mesh_b)
    precise = is_mesh_mesh_collision(mesh_a, mesh_b)

    assert fast is True
    assert precise is True
    return mesh_a, mesh_b, fast, precise


def main(show=True):
    mesh_a, mesh_b, fast, precise = build_example()
    print(f"overlapping boxes: fast={fast}, precise={precise}")

    if show:
        show_scene(
            "Mesh collision: simple overlap",
            [
                (mesh_a, "mesh A", BLUE, 0.65),
                (mesh_b, "mesh B", GREEN, 0.65),
            ],
            [(f"fast={fast}  precise={precise}", (-0.8, 0.8, 0.7), GREEN)],
        )


if __name__ == "__main__":
    main(show="--no-viewer" not in sys.argv)
